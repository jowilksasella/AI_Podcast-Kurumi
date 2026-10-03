"""Focused CPU fixtures: no native TTS import, weights, reference voices or GPU."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from kurumi_podcast import audio
from kurumi_podcast.core import load_json, save_json
from kurumi_podcast.engine import (DEFAULT_GENERATION_KWARGS, ContinuousContextError,
                                  IndexBackend, UnsupportedContinuousContext,
                                  continuous_context_guard, speech_settings)
from kurumi_podcast.pipeline import line_signature, render


TEXT = "大家好，我是久留美。今天聊期权对冲。"


class NativeContextStub:
    """Use the normalized token boundary before a test-only GPT counter."""
    low_vram = False

    def __init__(self):
        self.gpt = types.SimpleNamespace(text_pos_embedding=types.SimpleNamespace(
            emb=types.SimpleNamespace(num_embeddings=512)))
        self.calls, self.split_calls, self.gpt_calls = [], [], 0
        self.processed = None
        self.split_result = None
        self.fail = False
        self.no_result = False
        self.bypass_split = False
        self.pcm = np.array([[-32768], [-100], [0], [32767], [0]], dtype=np.int16)

    def _token_len(self, text):
        return len(text)

    def split_text_by_tokens(self, text, max_tokens, lang_prefix=""):
        self.split_calls.append((text, max_tokens, lang_prefix))
        if self.split_result is not None:
            return self.split_result
        budget = max(1, min(max_tokens, 510) - self._token_len(lang_prefix))
        return [text] if len(text) <= budget else [text[:budget], text[budget:]]

    def infer(self, **kwargs):
        self.calls.append(kwargs)
        if not self.bypass_split:
            # This simulates native normalization/annotation expansion. The
            # production guard observes native's result, never this simulation.
            processed = self.processed if self.processed is not None else kwargs["text"].lower()
            self.split_text_by_tokens(processed, kwargs["max_text_tokens_per_segment"], "<|zh|> ")
        self.gpt_calls += 1
        if self.fail:
            raise RuntimeError("test native failure")
        if self.no_result:
            return None
        if kwargs["output_path"] is None:
            return 22050, self.pcm
        audio.write_pcm(kwargs["output_path"], self.pcm[:, 0], 22050)
        return kwargs["output_path"]


class BackendContextTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "indextts").mkdir()
        (self.root / "indextts/infer_v2_5.py").write_text("# source fixture")
        self.config = {"_base": str(self.root), "index_home": str(self.root)}
        self.target = self.root / "native.wav"
        self.torch = types.SimpleNamespace(manual_seed=Mock())
        self.modules = patch.dict(sys.modules, {"torch": self.torch})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def backend(self, **config):
        backend = IndexBackend({**self.config, **config})
        backend.model = NativeContextStub()
        return backend

    def synthesize(self, backend, text=TEXT):
        backend.synthesize(text, self.target, "fixture.ref", None, 20261004)

    def test_whole_turn_one_call_all_parameters_and_exact_native_pcm(self):
        backend = self.backend()
        self.synthesize(backend)
        self.assertEqual(len(backend.model.calls), 1)
        kwargs = backend.model.calls[0]
        self.assertEqual(kwargs["text"], TEXT)
        self.assertIsNone(kwargs["output_path"])
        self.assertEqual(kwargs["interval_silence"], 0)
        self.assertEqual(kwargs["max_text_tokens_per_segment"], 160)
        self.assertEqual({k: kwargs[k] for k in DEFAULT_GENERATION_KWARGS}, DEFAULT_GENERATION_KWARGS)
        self.assertFalse(kwargs["use_random"])
        self.assertFalse(kwargs["use_emo_text"])
        self.assertIsNone(kwargs["emo_vector"])
        self.assertIsNone(kwargs["emo_audio_prompt"])
        self.assertEqual(kwargs["emo_alpha"], 1.0)
        self.torch.manual_seed.assert_called_once_with(20261004)
        np.testing.assert_array_equal(audio.read_pcm(self.target, 22050), backend.model.pcm[:, 0])
        self.assertNotIn("split_text_by_tokens", vars(backend.model))

    def test_explicit_gpt_sampling_is_not_emotion_randomness(self):
        backend = self.backend(generation_kwargs={"do_sample": True, "temperature": .6})
        self.synthesize(backend)
        self.assertTrue(backend.model.calls[0]["do_sample"])
        self.assertEqual(backend.model.calls[0]["temperature"], .6)
        self.assertFalse(backend.model.calls[0]["use_random"])

    def test_low_vram_raw_length_rejected_before_native_call(self):
        backend = self.backend()
        backend.model.low_vram = True
        with self.assertRaisesRegex(ContinuousContextError, "low_vram.*>40"):
            self.synthesize(backend, "甲" * 41)
        self.assertEqual(backend.model.calls, [])
        self.assertEqual(backend.model.gpt_calls, 0)
        self.assertFalse(self.target.exists())
        self.assertTrue(backend.model.low_vram)

    def test_large_vram_is_not_globally_limited_to_40_characters(self):
        backend = self.backend()
        self.synthesize(backend, "甲" * 60)
        self.assertEqual(len(backend.model.calls), 1)
        self.assertEqual(backend.model.gpt_calls, 1)

    def test_real_processed_text_and_prefix_guard_reject_before_gpt(self):
        backend = self.backend(max_text_tokens_per_segment=20)
        backend.model.processed = "规范化后扩展的文字" * 4
        with self.assertRaisesRegex(ContinuousContextError, "requires 2 segments"):
            self.synthesize(backend, "12<行|XING2>。")
        self.assertEqual(backend.model.split_calls[0], (backend.model.processed, 20, "<|zh|> "))
        self.assertEqual(backend.model.gpt_calls, 0)
        self.assertNotIn("split_text_by_tokens", vars(backend.model))
        self.assertFalse(self.target.exists())

    def test_indivisible_atom_cannot_bypass_capacity_even_if_one_segment(self):
        backend = self.backend(max_text_tokens_per_segment=900)
        backend.model.gpt.text_pos_embedding.emb.num_embeddings = 20
        backend.model.processed = "甲" * 30
        backend.model.split_result = [backend.model.processed]
        with self.assertRaisesRegex(ContinuousContextError, "capacity"):
            self.synthesize(backend)
        self.assertEqual(backend.model.gpt_calls, 0)
        self.assertEqual(backend.model.gpt.text_pos_embedding.emb.num_embeddings, 20)

    def test_failure_does_not_retry_and_restores_instance_override(self):
        backend = self.backend()
        helper = backend.model.split_text_by_tokens
        backend.model.split_text_by_tokens = helper
        backend.model.fail = True
        with self.assertRaisesRegex(RuntimeError, "test native failure"):
            self.synthesize(backend)
        self.assertEqual(len(backend.model.calls), 1)
        self.assertIs(backend.model.split_text_by_tokens, helper)
        self.assertFalse(self.target.exists())

    def test_none_result_never_uses_an_old_file(self):
        backend = self.backend()
        backend.model.no_result = True
        self.target.write_bytes(b"old output must not count as success")
        with self.assertRaisesRegex(RuntimeError, "no PCM"):
            self.synthesize(backend)
        self.assertEqual(len(backend.model.calls), 1)
        self.assertEqual(self.target.read_bytes(), b"old output must not count as success")

    def test_missing_helper_is_explicitly_unsupported_not_silently_legacy(self):
        backend = self.backend()
        backend.model.split_text_by_tokens = None
        with self.assertRaisesRegex(UnsupportedContinuousContext, "unsupported"):
            self.synthesize(backend)
        self.assertEqual(backend.model.calls, [])

    def test_bypassed_helper_is_not_certified_continuous(self):
        backend = self.backend()
        backend.model.bypass_split = True
        with self.assertRaisesRegex(UnsupportedContinuousContext, "never invoked"):
            self.synthesize(backend)
        self.assertFalse(self.target.exists())
        self.assertNotIn("split_text_by_tokens", vars(backend.model))

    def test_legacy_mode_does_not_require_context_fields(self):
        backend = self.backend(speech_mode="legacy_chunks")
        backend.model.low_vram = None
        self.synthesize(backend, "甲" * 60)
        self.assertEqual(len(backend.model.calls), 1)
        self.assertEqual(backend.model.calls[0]["interval_silence"], 110)

    def test_override_validation_protects_native_request_fields(self):
        for key in ("text", "spk_audio_prompt", "output_path", "use_random", "lora_dir"):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "unsupported"):
                speech_settings({"generation_kwargs": {key: "injected"}})
        for config in ({"speech_mode": "auto"}, {"generation_kwargs": []},
                       {"generation_kwargs": {"do_sample": "false"}},
                       {"generation_kwargs": {"top_p": 1.1}},
                       {"generation_kwargs": {"temperature": float("nan")}},
                       {"generation_kwargs": {"num_beams": 0}},
                       {"max_text_tokens_per_segment": 0}, {"interval_silence_ms": -1}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                speech_settings(config)


class WholeTurnFixture:
    """CPU-only waveform for pipeline routing, not a production voice."""
    def __init__(self):
        self.calls = []
        self.error = None
        self.seconds = 3

    def synthesize(self, text, target, voice, emotion, seed):
        self.calls.append(text)
        if self.error:
            raise self.error
        samples = np.zeros(round(self.seconds * 22050))
        samples[2205:-2205] = 500
        samples[len(samples) // 2:len(samples) // 2 + 2205] = 0
        audio.write_pcm(target, samples, 22050)


class PipelineContinuousTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.plan_path, self.config_path = self.root / "plan.json", self.root / "config.json"
        self.out = self.root / "out"
        self.line = {"id": "001", "speaker": "久留美", "opening": True,
                     "text": TEXT, "tts_text": "大家好，我是<久留美|JIU3 LIU2 MEI3>。今天聊期权对冲。"}
        save_json(self.plan_path, {"title": "CPU fixture", "lead": "久留美", "lines": [self.line]})
        self.voice = self.root / "voice.fixture"
        self.voice.write_bytes(b"not reference audio")
        self.config = {"voices": {"久留美": {"reference_audio": str(self.voice)}}}
        save_json(self.config_path, self.config)
        self.backend = WholeTurnFixture()
        def master_copy(binary, args, **kwargs):
            shutil.copyfile(args[1], args[-1])
        for tool_patch in (patch.object(audio, "ffmpeg", side_effect=master_copy),
                           patch.object(audio, "export_mp3"), patch.dict(os.environ, {"INDEXTTS_HOME": ""})):
            tool_patch.start()
            self.addCleanup(tool_patch.stop)

    def render(self):
        return render(self.plan_path, self.config_path, self.out, stage="opening", backend=self.backend)

    def test_whole_tts_text_no_split_trim_or_conversion_at_native_rate(self):
        with patch("kurumi_podcast.pipeline.natural_chunks", side_effect=AssertionError("external split")), \
             patch.object(audio, "trim_edges", side_effect=AssertionError("DSP")), \
             patch.object(audio, "normalize_source", side_effect=AssertionError("unnecessary conversion")):
            manifest = self.render()
        self.assertEqual(self.backend.calls, [self.line["tts_text"]])
        self.assertEqual((self.out / "work/001_raw.wav").read_bytes(), (self.out / "work/001.wav").read_bytes())
        self.assertEqual(manifest["sample_rate"], 22050)
        self.assertEqual(manifest["speech_mode"], "continuous")
        self.assertFalse(manifest["audio_processing"]["fresh_turn_trim_or_fade"])
        self.assertTrue(manifest["audio_processing"]["episode_loudnorm"])
        self.assertEqual(manifest["turns"][0]["text"], TEXT)

    def test_duration_anomaly_and_native_failure_never_retry(self):
        for failure in (None, ContinuousContextError("native context requires 2 segments")):
            with self.subTest(failure=failure):
                self.backend.calls.clear()
                self.backend.seconds = 25
                self.backend.error = failure
                with self.assertRaises((RuntimeError, ContinuousContextError)):
                    self.render()
                self.assertEqual(self.backend.calls, [self.line["tts_text"]])
                self.assertFalse((self.out / "work/cache.json").exists())

    def test_every_generation_control_and_mode_invalidates_waveform_cache(self):
        self.render()
        self.render()
        self.assertEqual(len(self.backend.calls), 1)
        overrides = {"do_sample": True, "top_p": .7, "top_k": 12, "temperature": .6,
                     "num_beams": 2, "repetition_penalty": 7, "length_penalty": 1,
                     "max_mel_tokens": 1400, "diffusion_steps": 20}
        for key, value in overrides.items():
            self.config["generation_kwargs"] = {key: value}
            save_json(self.config_path, self.config)
            before = len(self.backend.calls)
            self.render()
            self.assertEqual(len(self.backend.calls), before + 1, key)
        for key, value in (("max_text_tokens_per_segment", 150), ("interval_silence_ms", 1),
                           ("speech_mode", "legacy_chunks")):
            self.config[key] = value
            save_json(self.config_path, self.config)
            before = len(self.backend.calls)
            self.render()
            self.assertGreater(len(self.backend.calls), before, key)

    def test_explicit_legacy_chunks_retains_bounded_retry(self):
        self.config.update(speech_mode="legacy_chunks", segment_chars=50)
        save_json(self.config_path, self.config)
        self.line.pop("tts_text")
        self.line["text"] = "甲" * 25 + "。" + "乙" * 19 + "。"
        save_json(self.plan_path, {"title": "CPU fixture", "lead": "久留美", "lines": [self.line]})
        backend = self.backend
        normal = backend.synthesize
        def initially_long(text, target, voice, emotion, seed):
            backend.seconds = 25 if len(text) > 30 else 3
            return normal(text, target, voice, emotion, seed)
        with patch.object(backend, "synthesize", side_effect=initially_long):
            self.render()
        self.assertEqual(len(backend.calls), 3)  # one failed whole chunk, then two smaller chunks
        self.assertEqual("".join(backend.calls[1:]), self.line["text"])
        count = len(backend.calls)
        self.render()
        self.assertEqual(len(backend.calls), count)

    def test_same_effective_defaults_have_same_signature_but_old_signature_cannot_hit(self):
        config = {**self.config, "_base": str(self.root)}
        line = {**self.line, "delivery": "explain"}
        initial = line_signature(line, config, self.root, 50)
        explicit = line_signature(line, {**config, **speech_settings({})}, self.root, 50)
        self.assertEqual(initial, explicit)
        self.assertEqual(initial["speech_pipeline_version"], 2)
        self.assertEqual(initial, line_signature(line, config, self.root, 8))

    def test_reuse_audio_never_synthesizes_a_voice(self):
        source = self.root / "reuse.wav"
        audio.write_pcm(source, np.ones(22050) * 500, 22050)
        self.line["reuse_audio"] = str(source)
        save_json(self.plan_path, {"title": "CPU fixture", "lead": "久留美", "lines": [self.line]})
        with patch.object(audio, "normalize_source", side_effect=lambda a, b, *rest: shutil.copyfile(a, b)):
            self.render()
            self.render()
        self.assertEqual(self.backend.calls, [])


class ConditioningCompatibilityTests(unittest.TestCase):
    def test_persistent_conditioning_survives_text_and_generation_parameter_changes(self):
        # Reuse the established cache fixtures rather than replacing its tests
        # or inventing another conditioning format. All tensors remain on CPU.
        import test_voice_cache as fixtures

        class CachedContextStub(fixtures.NativeStub):
            low_vram = False
            _token_len = NativeContextStub._token_len
            split_text_by_tokens = NativeContextStub.split_text_by_tokens

            def __init__(self, marker):
                super().__init__()
                self.marker = marker
                self.gpt = types.SimpleNamespace(text_pos_embedding=types.SimpleNamespace(
                    emb=types.SimpleNamespace(num_embeddings=512)))
                self.split_calls, self.split_result = [], None

            def infer(self, spk_audio_prompt, text, output_path, **kwargs):
                self.split_text_by_tokens(text, kwargs["max_text_tokens_per_segment"], "<|zh|> ")
                super().infer(spk_audio_prompt, text, str(self.marker), **kwargs)
                return 22050, np.array([[1], [2], [3]], dtype=np.int16)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "indextts").mkdir()
            (root / "indextts/infer_v2_5.py").write_text("# native fixture")
            (root / "checkpoints").mkdir()
            (root / "checkpoints/config.yaml").write_text("fixture")
            reference = root / "reference.fixture"
            reference.write_bytes(b"reference signature fixture, not audio")
            config = {"_base": str(root), "index_home": str(root),
                      "voice_cache_dir": "cache", "device": "cpu", "use_bf16": False}
            with patch.dict(sys.modules, {"torch": fixtures.TEST_TORCH}), \
                 patch.object(fixtures.TEST_TORCH, "manual_seed"), contextlib.redirect_stdout(io.StringIO()):
                first = IndexBackend(config)
                first.model = CachedContextStub(root / "marker")
                first.synthesize("第一句。", root / "first.wav", reference, None, 123)
                fresh = IndexBackend({**config, "generation_kwargs": {"temperature": .6}})
                fresh.model = CachedContextStub(root / "marker")
                fresh.synthesize("另一段完整话语。", root / "second.wav", reference, None, 123)
                self.assertEqual(fresh.model.calls, [])  # no reference encoders on disk hit
                self.assertEqual(fresh.model.encoder_moves, [])
                self.assertEqual(len(list((root / "cache").glob("*.pt"))), 1)


if __name__ == "__main__":
    unittest.main()
