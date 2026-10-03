import copy
import tempfile
import unittest
from pathlib import Path

import numpy as np

from kurumi_podcast import audio
from kurumi_podcast.core import (chapter_ranges, lead_speech_share, load_json,
                                 natural_chunks, shifted_opening_rows, validate_plan)

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "preview.json"


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = load_json(EXAMPLE)

    def test_example_has_setup_two_speakers_and_lead(self):
        result = validate_plan(self.plan)
        self.assertTrue(result["lines"][0]["opening"])
        self.assertEqual(len(result["speaker_characters"]), 2)
        self.assertGreaterEqual(result["lead_text_fraction"], .65)
        self.assertLessEqual(result["lead_text_fraction"], .75)
        self.assertNotIn("id", self.plan["lines"][0])

    def test_example_fits_continuous_low_vram_and_preserves_source_anchors(self):
        lines = self.plan["lines"]
        self.assertTrue(all(len(line["text"]) <= 40 for line in lines))
        self.assertTrue(all("tts_text" not in line and "<" not in line["text"] for line in lines))
        self.assertTrue(all(a["speaker"] != b["speaker"] for a, b in zip(lines, lines[1:])))
        characters = sum(len(line["text"]) for line in lines)
        self.assertTrue(230 <= characters <= 250)
        pages = {ref["page"] for line in lines for ref in line.get("source_refs", [])}
        self.assertEqual(pages, {4, 6})
        self.assertEqual(self.plan["source_note"],
                         "原创短样结构示例；机制示例见SqueezeMetrics 2017 GEX白皮书第4、6页。")
        text = "".join(line["text"] for line in lines)
        for condition in ("卖出一份看跌期权", "可能还要继续卖出股票", "控制自己的方向风险", "模型假设"):
            self.assertIn(condition, text)
        # TestWaveBackend's deterministic CPU fixture, not a native speech or
        # voice-duration claim: include the normal inter-role/chapter gaps.
        seconds = sum(len(line["text"]) * .18 + .2 for line in lines)
        for index, line in enumerate(lines):
            end = index == len(lines) - 1 or lines[index + 1]["chapter"] != line["chapter"]
            seconds += line.get("after_ms", 750 if end else 140) / 1000
        self.assertTrue(30 <= seconds <= 60)

    def test_missing_setup_is_rejected(self):
        del self.plan["lines"][0]["opening"]
        with self.assertRaisesRegex(ValueError, "opening"):
            validate_plan(self.plan)

    def test_lead_cannot_become_secondary(self):
        for line in self.plan["lines"]:
            if line["speaker"] == "久留美":
                line["text"] = "嗯。"
        with self.assertRaisesRegex(ValueError, "main speaker"):
            validate_plan(self.plan, "full")

    def test_ids_cannot_escape_cache_or_collide(self):
        for identifier in ("../outside", "a/b", "", 3):
            with self.subTest(identifier=identifier):
                plan = copy.deepcopy(self.plan)
                plan["lines"][0]["id"] = identifier
                with self.assertRaisesRegex(ValueError, "unsafe"):
                    validate_plan(plan)
        for line in self.plan["lines"]:
            line["id"] = "same"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_plan(self.plan)

    def test_pronunciation_only_in_tts_text(self):
        self.plan["lines"][0]["tts_text"] = "这里是<买|mai3>。"
        validate_plan(self.plan)
        self.plan["lines"][0]["text"] = "这里是<买|mai3>。"
        with self.assertRaisesRegex(ValueError, "tts_text"):
            validate_plan(self.plan)

    def test_malformed_json_types_raise_actionable_error(self):
        for data in ([], {**self.plan, "lead": []}, {**self.plan, "lines": [None]}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_plan(data)
        self.plan["lines"][0]["tts_text"] = None
        with self.assertRaisesRegex(ValueError, "tts_text"):
            validate_plan(self.plan)


class TimingTests(unittest.TestCase):
    def test_natural_chunks_keep_every_character(self):
        texts = ["等等？！为什么会这样！！然后呢……",
                 "，先有铺垫，；再讲机制。最后总结！",
                 "一段很长的内容" * 12 + "，然后自然接话。",
                 "这里是很长的内容" * 5 + "<卖|mai4>出股票，然后再买入。",
                 "第一行\n第二行没有标点"]
        for text in texts:
            with self.subTest(text=text):
                chunks = natural_chunks(text, 20)
                self.assertEqual("".join(chunks), text)
                if "<卖|mai4>" in text:
                    self.assertTrue(any("<卖|mai4>" in c for c in chunks))
                else:
                    self.assertTrue(all(len(c) <= 20 for c in chunks))

    def test_overlap_and_last_gap_do_not_truncate_audio(self):
        lines = [{"speaker": "久留美", "chapter": "正文", "after_ms": -100},
                 {"speaker": "萌智子", "chapter": "正文", "after_ms": -100}]
        clips = [np.ones(1000) * 1000, np.ones(500) * 2000]
        mixed, rows = audio.mix_turns(lines, clips, 1000)
        self.assertEqual(len(mixed), 1400)
        self.assertEqual(rows[1]["start"], .9)
        self.assertEqual(rows[1]["end"], 1.4)
        self.assertEqual(mixed[-1], 1640)
        with self.assertRaises(ValueError):
            audio.mix_turns(lines, clips[:1], 1000)

    def test_opening_moves_timeline_without_changing_source_rows(self):
        base = [{"speaker": "久留美", "start": 0., "end": 2., "duration": 2., "chapter": "开场"},
                {"speaker": "久留美", "start": 2.2, "end": 5., "duration": 2.8, "chapter": "正文"}]
        prefix = [{"speaker": "久留美", "start": 0., "end": 3., "duration": 3., "chapter": "新铺垫"}]
        rows, shift = shifted_opening_rows(base, prefix, 2.2, 3.2, 5.5)
        self.assertAlmostEqual(shift, 1.)
        self.assertAlmostEqual(rows[1]["start"], 3.2)
        self.assertEqual(base[1]["start"], 2.2)
        self.assertEqual(rows[0]["chapter"], "开场")
        with self.assertRaisesRegex(ValueError, "align"):
            shifted_opening_rows(base, prefix, 1., 3.2, 5.5)
        self.assertEqual(chapter_ranges(rows, 6.5)[-1]["end"], 6.5)
        self.assertEqual(lead_speech_share(rows, "久留美")[0], 1.)

    def test_mastered_body_preserved_exactly_in_pcm(self):
        rate = 1000
        prefix = np.arange(123, dtype=float)
        body = np.arange(1000, dtype=float) * 7 - 3000
        joined = audio.join_mastered(prefix, body, .2, rate)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "joined.wav"
            audio.write_pcm(target, joined, rate)
            result = audio.read_pcm(target, rate)
        np.testing.assert_array_equal(result[len(prefix):], body[200:])


if __name__ == "__main__":
    unittest.main()
