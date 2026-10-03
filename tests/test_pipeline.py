import copy
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from pypdf import PdfWriter

from kurumi_podcast import audio
from kurumi_podcast.core import load_json, save_json, validate_plan
from kurumi_podcast.pipeline import (extract_source, line_signature, load_config,
                                     patch_opening, render)

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "preview.json"


class TestWaveBackend:
    """Test-only waveform fixture. It is not an available production voice engine."""

    def __init__(self, rate=24000):
        self.rate = rate
        self.calls = []

    def synthesize(self, text, target, voice, emotion, seed):
        self.calls.append((text, str(voice), str(emotion), seed))
        t = np.arange(round((len(text) * .18 + .2) * self.rate)) / self.rate
        audio.write_pcm(target, 4000 * np.sin(2 * np.pi * 200 * t), self.rate)


class SourceAndSignatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_text_and_blank_pdf_keep_source_anchors(self):
        source = self.root / "paper.md"
        source.write_text("# 研究\n正文", encoding="utf-8-sig")
        result = extract_source(source, self.root / "text.json")
        self.assertEqual(result["pages"][0]["text"], "# 研究\n正文")
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        pdf = self.root / "paper.pdf"
        with pdf.open("wb") as file:
            writer.write(file)
        result = extract_source(pdf, self.root / "pdf.json")
        self.assertEqual(result["empty_text_pages"], [1])
        self.assertTrue(result["visual_review_required"])

    def test_emotion_and_voice_are_independent_cache_inputs(self):
        voice, mood = self.root / "voice.wav", self.root / "mood.wav"
        voice.write_bytes(b"voice")
        mood.write_bytes(b"mood")
        config = {"_base": str(self.root), "voices": {
            "久留美": {"reference_audio": "voice.wav", "emotion_audio": {"question": "mood.wav"}}
        }}
        line = {"speaker": "久留美", "text": "这里是铺垫。", "delivery": "explain"}
        with patch.dict(os.environ, {"INDEXTTS_HOME": ""}):
            initial = line_signature(line, config, self.root, 50)
            question = line_signature({**line, "delivery": "question"}, config, self.root, 50)
            self.assertEqual(initial["voice"], question["voice"])
            self.assertIsNone(initial["emotion"])
            self.assertIsNotNone(question["emotion"])
            mood.write_bytes(b"changed mood")
            updated = line_signature({**line, "delivery": "question"}, config, self.root, 50)
            self.assertNotEqual(updated, question)
            self.assertEqual(initial, line_signature(line, config, self.root, 50))
            different_model = line_signature(line, {**config, "model_dir": "other"}, self.root, 50)
            self.assertNotEqual(initial, different_model)

    def test_full_requires_confirmation_before_any_io(self):
        with self.assertRaisesRegex(ValueError, "approved-preview"):
            render("missing.json", "missing.config", self.root / "out", stage="full")
        self.assertFalse((self.root / "out").exists())


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is needed for audio integration tests")
class AudioPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan_path = self.root / "plan.json"
        self.config_path = self.root / "config.local.json"
        self.plan = load_json(EXAMPLE)
        save_json(self.plan_path, self.plan)
        for name in ("lead.wav", "partner.wav"):
            audio.write_pcm(self.root / name, np.ones(2400) * 500, 24000)
        save_json(self.config_path, {"sample_rate": 24000, "voices": {
            "久留美": {"reference_audio": "lead.wav", "identity_label": "Test fixture"},
            "萌智子": {"reference_audio": "partner.wav", "identity_label": "Test fixture"}
        }})
        self.backend = TestWaveBackend()

    def test_preview_reuses_cache_and_repairs_only_changed_turn(self):
        out = self.root / "preview"
        first = render(self.plan_path, self.config_path, out, backend=self.backend)
        self.assertTrue(30 <= first["duration_seconds"] <= 60)
        self.assertTrue((out / "episode.mp3").is_file())
        self.assertTrue((out / "subtitles.srt").is_file())
        count = len(self.backend.calls)
        cache = load_json(out / "work" / "cache.json")
        render(self.plan_path, self.config_path, out, backend=self.backend)
        self.assertEqual(len(self.backend.calls), count)
        self.plan["lines"][1]["text"] += "聊聊看。"
        save_json(self.plan_path, self.plan)
        render(self.plan_path, self.config_path, out, backend=self.backend)
        self.assertEqual(len(self.backend.calls), count + 1)
        revised = load_json(out / "work" / "cache.json")
        self.assertEqual(cache["001"], revised["001"])
        self.assertNotEqual(cache["002"], revised["002"])

    def test_opening_patch_keeps_body_and_shifts_documents(self):
        base = self.root / "base"
        old = render(self.plan_path, self.config_path, base, backend=self.backend)
        prefix_path = self.root / "opening.json"
        opening = {"title": old["title"], "lead": "久留美", "lines": [{
            "speaker": "久留美", "opening": True, "chapter": "铺垫", "text": "先认识一下，我是久留美。今天聊聊这篇研究。"
        }]}
        save_json(prefix_path, opening)
        before = len(self.backend.calls)
        with self.assertRaisesRegex(ValueError, "align"):
            patch_opening(prefix_path, base, self.config_path, self.root / "invalid", cut=1., backend=self.backend)
        self.assertEqual(len(self.backend.calls), before)
        out = self.root / "revised"
        new = patch_opening(prefix_path, base, self.config_path, out, backend=self.backend)
        self.assertEqual(len(self.backend.calls), before + 1)
        prefix = audio.read_pcm(out / "work" / "new-opening" / "episode.wav", 24000)
        old_body = audio.read_pcm(base / "episode.wav", 24000)
        new_audio = audio.read_pcm(out / "episode.wav", 24000)
        np.testing.assert_array_equal(new_audio[len(prefix):], old_body)
        self.assertAlmostEqual(new["turns"][1]["start"], old["turns"][0]["start"] + len(prefix) / 24000)
        self.assertGreater(new["speaker_characters"]["久留美"], old["speaker_characters"]["久留美"])
        self.assertTrue(new["revision"]["body_preserved"])
        self.assertTrue((out / "opening-preview.wav").is_file())

    def test_shorter_chunk_retry_is_bounded_and_cached(self):
        config = load_json(self.config_path)
        config["speech_mode"] = "legacy_chunks"
        save_json(self.config_path, config)
        # Deliberately overlong legacy fixture. The shipped default example
        # must no longer depend on >40-character turns to exercise repair.
        self.plan["lines"][0]["text"] = (
            "大家好，我是久留美。今天和萌智子聊个怪事："
            "为什么股市有时很安静，有时却突然大起大落？"
        )
        save_json(self.plan_path, self.plan)
        class RepeatingBackend(TestWaveBackend):
            def synthesize(self, text, target, voice, emotion, seed):
                super().synthesize(text, target, voice, emotion, seed)
                if len(text) > 40:
                    audio.write_pcm(target, np.ones(24000 * 22) * 1000, self.rate)

        backend = RepeatingBackend()
        out = self.root / "retry"
        result = render(self.plan_path, self.config_path, out, backend=backend)
        self.assertTrue(30 <= result["duration_seconds"] <= 60)
        self.assertTrue(any(len(call[0]) > 40 for call in backend.calls))
        self.assertTrue(any(len(call[0]) <= 30 for call in backend.calls))
        count = len(backend.calls)
        render(self.plan_path, self.config_path, out, backend=backend)
        self.assertEqual(len(backend.calls), count)


if __name__ == "__main__":
    unittest.main()
