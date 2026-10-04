import copy
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from kurumi_podcast.core import save_json
from kurumi_podcast.pipeline import render
from kurumi_podcast import audio
from kurumi_podcast.engine import IndexBackend
from kurumi_podcast.recipe import (ORIGINAL, bind_original, content_identity,
                                   effective_settings, native_inference_settings,
                                   original_recipe, turn_chunks, turn_seed, validate_runtime)


class MissingMoodRegression(unittest.TestCase):
    def test_v010_empty_moods_rejected_before_backend_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("kurumi_ja.wav", "mochiko_ja.wav"):
                (root / name).write_bytes(b"JA reference fixture")
            save_json(root / "config.local.json", {"emo_alpha": .5, "voices": {
                "久留美": {"reference_audio": "kurumi_ja.wav", "emotion_audio": {}},
                "萌智子": {"reference_audio": "mochiko_ja.wav", "emotion_audio": {}}
            }})
            save_json(root / "plan.json", {"title": "恢复回归", "lines": [
                {"speaker": "久留美", "opening": True, "text": "大家好，今天聊一个研究里的小发现。"},
                {"speaker": "萌智子", "text": "是什么？", "delivery": "question"}
            ]})
            backend = Mock()
            with self.assertRaisesRegex(ValueError, "emotion_audio|binding|lock"):
                render(root / "plan.json", root / "config.local.json", root / "out", backend=backend)
            backend.synthesize.assert_not_called()
            self.assertFalse((root / "out").exists())


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "engine"
        (self.home / "indextts").mkdir(parents=True)
        (self.home / "indextts" / "infer_v2_5.py").write_text("# native fixture", encoding="utf-8")
        (self.home / "checkpoints").mkdir()
        (self.home / "checkpoints" / "config.yaml").write_text("version: 2.5", encoding="utf-8")
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.recipe = original_recipe()
        for number, slot in enumerate(self.recipe["assets"]):
            path = self.assets / slot
            path.write_bytes(f"test reference {number}".encode())
            self.recipe["assets"][slot] = content_identity(path)
        self.provider = patch("kurumi_podcast.recipe.original_recipe", return_value=self.recipe)
        self.provider.start()
        self.addCleanup(self.provider.stop)
        from unittest.mock import patch as environment_patch
        self.environment = environment_patch.dict("os.environ", {"INDEXTTS_HOME": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.config = bind_original(self.assets, self.home, self.root / "bound.local.json")
        self.config["_base"] = str(self.root)

    def test_bound_profile_has_separate_timbre_and_all_moods(self):
        evidence = validate_runtime(self.config)
        self.assertTrue(evidence["restoration"])
        self.assertFalse(evidence["listening_verified"])
        self.assertFalse(evidence["historical_bits_verified"])
        for profile in self.config["voices"].values():
            self.assertEqual(set(profile["emotion_audio"]), {"explain", "question", "comment", "joke"})
            self.assertNotIn(profile["reference_audio"], profile["emotion_audio"].values())

    def test_renamed_or_replaced_reference_does_not_pass(self):
        (self.assets / "kurumi_explain.wav").write_bytes(b"replacement")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            validate_runtime(self.config)

    def test_native_source_change_invalidates_new_environment_binding(self):
        (self.home / "indextts" / "infer_v2_5.py").write_text("# changed native fixture", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "engine lock changed"):
            validate_runtime(self.config)

    def test_empty_used_delivery_and_missing_lock_are_rejected(self):
        config = copy.deepcopy(self.config)
        del config["voices"]["久留美"]["emotion_audio"]["joke"]
        with self.assertRaisesRegex(ValueError, "emotion_audio"):
            validate_runtime(config, {"lines": [{"speaker": "久留美", "delivery": "joke"}]})
        config = copy.deepcopy(self.config)
        del config["original_lock"]
        with self.assertRaisesRegex(ValueError, "binding lock"):
            validate_runtime(config)

    def test_sampling_and_v020_controls_cannot_silently_override(self):
        settings = effective_settings(self.config)
        self.assertTrue(settings["decoder"]["do_sample"])
        self.assertEqual(settings["emo_alpha"], .5)
        for override in ({"decoder": {**settings["decoder"], "do_sample": False}},
                         {"speech_mode": "continuous"},
                         {"generation_kwargs": {"do_sample": False}},
                         {"interval_silence_ms": 0}, {"emo_alpha": 1.}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_runtime({**self.config, **override})

    def test_length_not_historical_line_number_controls_chunks(self):
        settings = effective_settings(self.config)
        text = "这是一段解释，" * 10
        first = turn_chunks({"id": "001", "text": text}, settings, True)
        late = turn_chunks({"id": "044", "text": text}, settings, True)
        named = turn_chunks({"id": "explanation", "text": text}, settings, True)
        self.assertEqual(first, late)
        self.assertEqual(first, named)
        self.assertGreater(len(first), 1)
        self.assertEqual(turn_chunks({"id": "044", "text": "短短一句。"}, settings, True), ["短短一句。"])
        self.assertEqual(turn_seed({"id": "001"}, settings), 20261903)
        self.assertEqual(turn_seed({"id": "001"}, settings, "opening"), 2026100201)

    def test_native_call_receives_mood_alpha_and_sampled_decoder(self):
        backend = IndexBackend(self.config)
        backend._load = Mock()
        fake_torch = types.ModuleType("torch")
        fake_torch.manual_seed = Mock()
        output = self.root / "speech.wav"

        def infer(**kwargs):
            audio.write_pcm(kwargs["output_path"], [500] * 2400, 24000)

        backend.model = types.SimpleNamespace(infer=Mock(side_effect=infer))
        with patch.dict(sys.modules, {"torch": fake_torch}):
            backend.synthesize("今天聊个怪事。", output, self.assets / "kurumi_ja.wav",
                               self.assets / "kurumi_explain.wav", 20261903)
        kwargs = backend.model.infer.call_args.kwargs
        self.assertEqual(kwargs["emo_alpha"], .5)
        self.assertTrue(kwargs["do_sample"])
        self.assertFalse(kwargs["use_random"])
        self.assertEqual(kwargs["temperature"], .8)
        self.assertEqual(kwargs["repetition_penalty"], 10.)
        self.assertEqual(kwargs["max_mel_tokens"], 1500)
        self.assertEqual(kwargs["emo_audio_prompt"], str(self.assets / "kurumi_explain.wav"))
        opening = native_inference_settings(self.config, "opening")
        self.assertEqual(opening["max_text_tokens_per_segment"], 120)
        self.assertEqual(opening["max_mel_tokens"], 1000)


if __name__ == "__main__":
    unittest.main()
