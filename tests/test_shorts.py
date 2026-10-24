import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from kurumi_podcast import audio
from kurumi_podcast.cli import main
from kurumi_podcast.core import load_json, save_json
from kurumi_podcast.pipeline import qa_report
from kurumi_podcast.shorts import compress_pauses, render_series, source_map, split_series

GEX = Path(__file__).resolve().parents[1] / "examples" / "gex"


class WaveBackend:
    """Test-only waveform fixture, not a voice engine."""

    def __init__(self, rate=24000):
        self.rate, self.calls = rate, []

    def synthesize(self, text, target, voice, emotion, seed):
        self.calls.append(text)
        t = np.arange(round((len(text) * .18 + .2) * self.rate)) / self.rate
        audio.write_pcm(target, 4000 * np.sin(2 * np.pi * 200 * t), self.rate)


def episode(title, hook, filler=8):
    lines = [["久留美", "explain", hook], ["萌智子", "question", "这是怎么回事？"]]
    for i in range(filler):
        speaker = "久留美" if i % 3 != 2 else "萌智子"
        lines.append([speaker, "explain", f"第{i + 1}个要点，先把机制讲清楚，再说它的条件和局限。"])
    return {"title": title, "sources": "p2", "lines": lines}


class SeriesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def series(self, episodes, first=1):
        path = self.root / "series.json"
        save_json(path, {"series": "测试一分钟", "lead": "久留美", "source": "测试白皮书", "first_episode": first,
                         "config_hint": "config.test.local.json", "episodes": episodes})
        return path

    def test_split_writes_standalone_hooked_plans(self):
        result = split_series(self.series([episode("盲区", "十二和十五几乎是一回事。"),
                                           episode("尺子", "同样平静的两天也能分出危险。")], first=0),
                              self.root / "out")
        plan = load_json(self.root / "out" / "ep00" / "plan.json")
        self.assertEqual(plan["title"], "测试一分钟 00｜盲区")
        self.assertTrue(plan["lines"][0]["opening"] and plan["lines"][1]["opening"])
        self.assertEqual({l["chapter"] for l in plan["lines"]}, {"盲区"})
        self.assertEqual(plan["lines"][0]["source_refs"][0]["source"], "测试白皮书")
        self.assertTrue((self.root / "out" / "ep01" / "plan.json").is_file())
        self.assertIn("| 01 | 尺子 |", (self.root / "out" / "series.md").read_text(encoding="utf-8"))
        self.assertEqual(result["episodes"][0]["hook_characters"], 12)

    def test_split_warns_on_length_hook_and_long_turns(self):
        short = episode("太短", "这个钩子写得太长太长了，三到五秒根本读不完，观众早就划走了。", filler=1)
        short["lines"].append(["久留美", "explain", "这一句故意写得特别特别长，长到明显超过五十个字，用来确认分割工具真的会提醒我们，把它拆成自然的两句话再交给引擎。"])
        issues = {w["issue"] for w in split_series(self.series([short]), self.root / "out")["episodes"][0]["warnings"]}
        self.assertTrue({"estimated_length", "long_hook", "long_turn"} <= issues)

    def test_split_rejects_a_lead_without_majority(self):
        bad = {"title": "搭档抢戏", "lines": [["久留美", "explain", "开场。"], ["萌智子", "comment", "我来讲一大段解释，久留美几乎不说话。" * 3]]}
        with self.assertRaisesRegex(ValueError, "main speaker"):
            split_series(self.series([bad]), self.root / "out")

    def test_gex_example_series_is_valid(self):
        result = split_series(GEX / "series.json", self.root / "gex")
        self.assertEqual(len(result["episodes"]), 16)
        self.assertEqual(result["episodes"][0]["episode"], "ep00")
        for row in result["episodes"]:
            self.assertEqual(row["warnings"], [], row["episode"])
            self.assertGreaterEqual(row["lead_fraction"], .6)


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is needed for audio tests")
class AudioToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def tone(self, seconds, rate=24000):
        return 8000 * np.sin(2 * np.pi * 220 * np.arange(round(seconds * rate)) / rate)

    def test_render_series_shares_one_backend_and_reuses_cache(self):
        path = self.root / "series.json"
        save_json(path, {"series": "测试", "episodes": [episode("一", "第一集的钩子。"), episode("二", "第二集的钩子。")]})
        split_series(path, self.root / "eps")
        for name in ("lead.wav", "partner.wav"):
            audio.write_pcm(self.root / name, np.ones(2400) * 500, 24000)
        config = self.root / "config.local.json"
        save_json(config, {"recipe": "custom", "voices": {"久留美": {"reference_audio": "lead.wav"},
                                                          "萌智子": {"reference_audio": "partner.wav"}}})
        backend = WaveBackend()
        result = render_series(self.root / "eps", config, backend=backend)
        self.assertEqual([r["episode"] for r in result["episodes"]], ["ep01", "ep02"])
        self.assertTrue(result["duration_ok"])
        calls = len(backend.calls)
        render_series(self.root / "eps", config, only=["2"], backend=backend)
        self.assertEqual(len(backend.calls), calls)
        self.assertTrue((self.root / "eps" / "ep02" / "out" / "episode.mp3").is_file())

    def test_qa_flags_long_internal_pause(self):
        rate = 24000
        speech = np.concatenate([self.tone(1.5), np.zeros(round(1.6 * rate)), self.tone(1.5)])
        audio.write_pcm(self.root / "episode.wav", speech, rate)
        save_json(self.root / "manifest.json", {
            "sample_rate": rate, "wav": "episode.wav", "lead": "久留美", "chapters": [{}], "stage": "preview",
            "duration_seconds": len(speech) / rate,
            "turns": [{"id": "001", "speaker": "久留美", "text": "这一句中间停了很久才继续说完。",
                       "start": 0., "end": len(speech) / rate, "duration": len(speech) / rate}]})
        flags = qa_report(self.root)["flags"]
        pause = [f for f in flags if f["issue"] == "long_internal_pause"]
        self.assertEqual(len(pause), 1)
        self.assertAlmostEqual(pause[0]["seconds"], 1.6, delta=.05)
        self.assertFalse([f for f in qa_report(self.root, long_pause=2.)["flags"] if f["issue"] == "long_internal_pause"])

    def test_compress_pauses_caps_gaps_and_15_second_window(self):
        rate = 44100
        first = np.concatenate([np.zeros(rate // 2), self.tone(3, rate), np.zeros(rate), self.tone(3, rate)])
        audio.write_pcm(self.root / "a.wav", first, rate)
        audio.write_pcm(self.root / "b.wav", self.tone(12, rate), rate)
        result = compress_pauses([self.root / "a.wav", self.root / "b.wav"], self.root / "ref.wav")
        self.assertAlmostEqual(result["seconds"], 6.4, delta=.05)
        self.assertLessEqual(result["longest_pause"], .41)
        self.assertIn("skipped", result["clips"][1])
        self.assertEqual(result["clips"][0]["pauses_shortened"], 1)


class SourceMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        folder = self.root / "series" / "ep00"
        (folder / "out").mkdir(parents=True)
        lines = [{"speaker": "久留美", "text": "钩子。"}, {"speaker": "萌智子", "text": "怎么说？"}]
        save_json(folder / "plan.json", {"title": "测试 00｜开场", "lines": lines})
        save_json(folder / "out" / "manifest.json", {"turns": [
            {"id": "001", "text": "钩子。", "start": 0., "end": 1.2}, {"id": "002", "text": "怎么说？", "start": 1.3, "end": 2.}]})
        save_json(self.root / "catalog.json", {
            "paper": {"title": "白皮书", "pages": 1},
            "white_paper": {"WP-P1-A": {"page": 1, "rects": [[10, 10, 100, 40]], "section": "第1页", "quote": "Q", "zh": "说明"}},
            "external": {"EXT-X": {"cite": "某论文", "where": "摘要", "zh": "发现"}},
            "tags": {"OURS-BRIDGE": "衔接"}})
        self.lines = {"episodes": {"00": {"visual": ["WP-P1-A"], "lines": [[["WP-P1-A"], "钩子"], [["OURS-BRIDGE"], ""]]}}}

    def run_map(self):
        save_json(self.root / "lines.json", self.lines)
        return source_map(self.root / "series", self.root / "catalog.json", self.root / "lines.json", self.root / "map")

    def test_map_lists_every_line_with_time_and_page(self):
        result = self.run_map()
        self.assertEqual(result["lines_by_primary_source"], {"white_paper": 1, "external": 0, "ours": 1})
        text = (self.root / "map" / "source-map.md").read_text(encoding="utf-8")
        self.assertIn("| 001 | 0.0–1.2 | 久留美 | 钩子。 | `WP-P1-A`（第1页） | 钩子 |", text)
        self.assertEqual(load_json(self.root / "map" / "source-map.json")["white_paper_sources"]["WP-P1-A"]["crops"],
                         ["crops/WP-P1-A.png"])

    def test_map_refuses_stale_or_unknown_sources(self):
        self.lines["episodes"]["00"]["lines"].pop()
        with self.assertRaisesRegex(ValueError, "differ in length"):
            self.run_map()
        self.lines["episodes"]["00"]["lines"].append([["EXT-NOPE"], ""])
        with self.assertRaisesRegex(ValueError, "unknown source"):
            self.run_map()

    def test_cli_source_map_without_pdf(self):
        save_json(self.root / "lines.json", self.lines)
        code = main(["source-map", str(self.root / "series"), "--catalog", str(self.root / "catalog.json"),
                     "--lines", str(self.root / "lines.json"), "--out", str(self.root / "cli")])
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "cli" / "source-map.md").is_file())


if __name__ == "__main__":
    unittest.main()
