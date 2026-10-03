"""CPU-only cache tests. No native models, real voices or generated audio."""
import contextlib
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

try:
    import torch as _torch
except (ImportError, OSError):
    _torch = None

from kurumi_podcast.engine import IndexBackend
from kurumi_podcast.voice_cache import PersistentVoiceCache, TENSOR_FIELDS


class _FakeTensor:
    """Isolated serialization mock for the light, torch-free test environment."""
    def __init__(self, values, dtype="float32", device="cpu"):
        self.values = np.asarray(values)
        self.dtype, self.device = dtype, device
        self.shape, self.ndim = self.values.shape, self.values.ndim

    def is_floating_point(self):
        return True

    def detach(self):
        return self

    def cpu(self):
        return self.to(device="cpu")

    def clone(self):
        return _FakeTensor(self.values.copy(), self.dtype, self.device)

    def to(self, *, device):
        return _FakeTensor(self.values.copy(), self.dtype, device)


class _FakeTorch:
    Tensor = _FakeTensor
    __version__ = "isolated-test"
    float16, float32, float64, bfloat16 = "float16", "float32", "float64", "bfloat16"

    @staticmethod
    def full(shape, value, dtype):
        return _FakeTensor(np.full(shape, value), dtype)

    @staticmethod
    def equal(left, right):
        return left.dtype == right.dtype and np.array_equal(left.values, right.values)

    @staticmethod
    def manual_seed(seed):
        pass

    @staticmethod
    def save(payload, path):
        def encode(value):
            if isinstance(value, _FakeTensor):
                return {"_test_tensor": value.values.tolist(), "dtype": value.dtype}
            raise TypeError(type(value))
        Path(path).write_text(json.dumps(payload, default=encode), encoding="utf-8")

    @staticmethod
    def load(path, *, map_location, weights_only):
        assert map_location == "cpu" and weights_only is True
        def decode(value):
            if "_test_tensor" in value:
                return _FakeTensor(value["_test_tensor"], value["dtype"])
            return value
        return json.loads(Path(path).read_text(encoding="utf-8"), object_hook=decode)


TEST_TORCH = _torch or _FakeTorch()


class NativeStub:
    """Mirror native path checks and the five cached conditioning fields."""
    device = "cpu"
    dtype = None
    use_bf16 = False
    model_version = 2.5
    vram_offload = True

    def __init__(self):
        self.cfg = {"version": 2.5, "n_mels": 80}
        self.calls, self.encoder_moves, self.infer_calls = [], [], []
        for field in TENSOR_FIELDS + ("cache_spk_audio_prompt", "cache_emo_audio_prompt"):
            setattr(self, field, None)

    def get_emb(self, prompt, kind):
        self.calls.append("get_emb:" + kind)
        return TEST_TORCH.full((1, 2, 4), sum(Path(prompt).read_bytes()),
                               dtype=TEST_TORCH.float32 if kind == "speaker" else TEST_TORCH.float16)

    def campplus(self):
        self.calls.append("CAMPPlus")
        return TEST_TORCH.full((1, 3), 3, dtype=TEST_TORCH.float32)

    def mel(self):
        self.calls.append("mel")
        return TEST_TORCH.full((1, 3, 5), 4, dtype=TEST_TORCH.float64)

    def reference_encoder(self):
        self.calls.append("reference_encoder")
        return TEST_TORCH.full((1, 5, 4), 5, dtype=TEST_TORCH.bfloat16)

    def infer(self, spk_audio_prompt, text, output_path, emo_audio_prompt=None, **kwargs):
        emotion = emo_audio_prompt or spk_audio_prompt
        self.infer_calls.append((spk_audio_prompt, emo_audio_prompt, kwargs["emo_alpha"]))
        speaker_miss = self.cache_spk_cond is None or self.cache_spk_audio_prompt != spk_audio_prompt
        emotion_miss = self.cache_emo_cond is None or self.cache_emo_audio_prompt != emotion
        if self.vram_offload and (speaker_miss or emotion_miss):
            self.encoder_moves.append("encode")
        if speaker_miss:
            self.cache_spk_cond = self.get_emb(spk_audio_prompt, "speaker")
            self.cache_s2mel_style = self.campplus()
            self.cache_mel = self.mel()
            self.cache_s2mel_prompt = self.reference_encoder()
            self.cache_spk_audio_prompt = spk_audio_prompt
        if emotion_miss:
            self.cache_emo_cond = self.get_emb(emotion, "emotion")
            self.cache_emo_audio_prompt = emotion
        if text == "fail":
            raise RuntimeError("unexpected native infer failure")
        # Only a test completion marker, NOT speech or a fabricated role recording.
        Path(output_path).write_text("test-only completion", encoding="utf-8")
        return str(output_path)


class VoiceCacheTests(unittest.TestCase):
    def setUp(self):
        if _torch is None:
            self.torch_patch = patch.dict(sys.modules, {"torch": TEST_TORCH})
            self.torch_patch.start()
            self.addCleanup(self.torch_patch.stop)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.home = self.root / "home"
        (self.home / "indextts").mkdir(parents=True)
        (self.home / "indextts" / "infer_v2_5.py").write_text("# native source fixture")
        (self.home / "checkpoints").mkdir()
        (self.home / "checkpoints" / "config.yaml").write_text("version: 2.5")
        (self.home / "checkpoints" / "gpt.pth").write_bytes(b"weight signature fixture")
        self.a, self.b, self.emotion = (self.root / name for name in ("a.ref", "b.ref", "emotion.ref"))
        for ref, data in ((self.a, b"A"), (self.b, b"B"), (self.emotion, b"emotion")):
            ref.write_bytes(data)
        self.config = {
            "_base": str(self.root), "index_home": str(self.home), "device": "cpu",
            "use_bf16": False, "voice_cache_dir": "conditioning-cache",
            "speech_mode": "legacy_chunks",  # This simple stub tests conditioning, not native context.
            "voices": {"A": {"reference_audio": str(self.a), "identity_label": "test profile A"},
                       "B": {"reference_audio": str(self.b), "identity_label": "test profile B"}},
        }
        self.cache_dir = self.root / "conditioning-cache"

    def backend(self, config=None):
        backend = IndexBackend(config or self.config)
        backend.model = NativeStub()
        return backend

    def synthesize(self, backend, voice=None, emotion=None, text="ok"):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            backend.synthesize(text, self.root / "completion.result", voice or self.a, emotion, 123)
        return [json.loads(line[len("[voice-cache] "):]) for line in output.getvalue().splitlines()
                if line.startswith("[voice-cache] ")]

    def test_first_save_is_cpu_tensor_dict_with_original_dtype_and_shape(self):
        backend = self.backend()
        events = self.synthesize(backend, emotion=self.emotion)
        self.assertEqual([e["event"] for e in events], ["miss", "saved"])
        self.assertIn("test profile A", events[0]["voice_identity"])
        self.assertEqual(events[1]["model_version"], "2.5")
        self.assertEqual(backend.model.encoder_moves, ["encode"])
        files = list(self.cache_dir.glob("*.pt"))
        self.assertEqual(len(files), 1)
        self.assertFalse(list(self.cache_dir.glob("*.tmp")))
        payload = TEST_TORCH.load(files[0], map_location="cpu", weights_only=True)
        for name in TENSOR_FIELDS:
            stored, original = payload["tensors"][name], getattr(backend.model, name)
            self.assertEqual(str(stored.device), "cpu")
            self.assertEqual(stored.dtype, original.dtype)
            self.assertEqual(stored.shape, original.shape)
            self.assertTrue(TEST_TORCH.equal(stored, original))

    def test_fresh_model_disk_restore_skips_all_reference_encoders(self):
        original = self.backend()
        self.synthesize(original, emotion=self.emotion)
        fresh = self.backend()
        with patch.object(TEST_TORCH, "load", wraps=TEST_TORCH.load) as load:
            events = self.synthesize(fresh, emotion=self.emotion)
        load.assert_called_once_with(next(self.cache_dir.glob("*.pt")), map_location="cpu", weights_only=True)
        self.assertEqual(events[0]["event"], "hit")
        self.assertEqual(events[0]["source"], "disk")
        self.assertEqual(fresh.model.calls, [])
        self.assertEqual(fresh.model.encoder_moves, [])
        self.assertEqual(fresh.model.cache_spk_audio_prompt, str(self.a.resolve()))
        self.assertEqual(fresh.model.cache_emo_audio_prompt, str(self.emotion.resolve()))
        for name in TENSOR_FIELDS:
            self.assertTrue(TEST_TORCH.equal(getattr(original.model, name), getattr(fresh.model, name)))

    def test_a_b_a_switch_and_adjacent_memory_hit_do_not_reencode_a(self):
        backend = self.backend()
        self.synthesize(backend, self.a)
        self.synthesize(backend, self.b)
        calls = list(backend.model.calls)
        self.assertEqual(len(calls), 10)
        events = self.synthesize(backend, self.a)
        self.assertEqual(events[0]["source"], "disk")
        self.assertEqual(backend.model.calls, calls)
        events = self.synthesize(backend, self.a)
        self.assertEqual(events[0]["source"], "memory")
        self.assertEqual(backend.model.calls, calls)
        self.assertEqual(len(backend.model.encoder_moves), 2)
        self.assertEqual(len(list(self.cache_dir.glob("*.pt"))), 2)

    def test_changed_reference_emotion_engine_weights_config_dtype_source_metadata_miss(self):
        mutations = {
            "reference": lambda backend: self.a.write_bytes(b"changed reference"),
            "emotion": lambda backend: self.emotion.write_bytes(b"changed emotion"),
            "engine": lambda backend: backend.config.update(engine="changed engine"),
            "weights": lambda backend: (self.home / "checkpoints" / "gpt.pth").write_bytes(b"new weights"),
            "config": lambda backend: backend.model.cfg.update(n_mels=81),
            "dtype": lambda backend: setattr(backend.model, "dtype", TEST_TORCH.bfloat16),
            "version": lambda backend: setattr(backend.model, "model_version", "2.5-revised"),
            "source": lambda backend: (self.home / "indextts" / "infer_v2_5.py").write_text("# changed native source"),
            "metadata": lambda backend: backend.config["voices"]["A"].update(identity_label="changed identity"),
            "revision": lambda backend: backend.config.update(voice_cache_revision="adapter-v2"),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                backend = self.backend(copy.deepcopy(self.config))
                first = self.synthesize(backend, emotion=self.emotion)
                count = len(backend.model.calls)
                mutate(backend)
                changed = self.synthesize(backend, emotion=self.emotion)
                self.assertEqual(changed[0]["event"], "miss")
                self.assertNotEqual(changed[0]["key"], first[0]["key"])
                self.assertEqual(len(backend.model.calls), count + 5)
                self.assertEqual(changed[-1]["event"], "saved")

    def test_corrupt_and_incompatible_cache_reencodes_and_records_miss(self):
        for corruption in ("bytes", "metadata", "dtype_spec", "missing_tensor"):
            with self.subTest(corruption=corruption):
                backend = self.backend()
                self.synthesize(backend)
                path = next(self.cache_dir.glob("*.pt"))
                if corruption == "bytes":
                    path.write_bytes(b"not a conditioning archive")
                else:
                    payload = TEST_TORCH.load(path, map_location="cpu", weights_only=True)
                    if corruption == "metadata":
                        payload["metadata"]["engine"] = "wrong engine"
                    elif corruption == "dtype_spec":
                        payload["tensor_specs"]["cache_mel"]["dtype"] = "wrong dtype"
                    else:
                        del payload["tensors"]["cache_mel"]
                    TEST_TORCH.save(payload, path)
                fresh = self.backend()
                events = self.synthesize(fresh)
                self.assertEqual(events[0]["reason"], "corrupt_or_incompatible")
                self.assertEqual(len(fresh.model.calls), 5)
                self.assertEqual(events[-1]["event"], "saved")

    def test_no_config_preserves_native_behavior_and_constructor_is_torch_lazy(self):
        config = {k: v for k, v in self.config.items() if k != "voice_cache_dir"}
        with patch.dict(sys.modules, {"torch": None}):
            backend = self.backend(config)
            cached_backend = self.backend()
        self.assertIsNotNone(cached_backend.voice_cache)
        self.assertIsNone(backend.voice_cache)
        for ref in (self.a, self.b, self.a):
            self.assertEqual(self.synthesize(backend, ref), [])
        self.assertEqual(len(backend.model.calls), 15)
        self.assertEqual(backend.model.infer_calls[0], (str(self.a), None, 1.0))
        self.assertFalse(self.cache_dir.exists())

    def test_default_emotion_canonical_paths_and_relative_cache_directory(self):
        backend = self.backend()
        self.assertEqual(backend.voice_cache.directory, self.cache_dir)
        alias = self.root / "alias"
        alias.mkdir()
        events = self.synthesize(backend, alias / ".." / "a.ref")
        self.assertEqual(events[0]["speaker"], str(self.a.resolve()))
        self.assertEqual(events[0]["emotion"], str(self.a.resolve()))
        self.assertIsNone(backend.model.infer_calls[-1][1])
        fresh = self.backend()
        self.assertEqual(self.synthesize(fresh, self.a)[0]["event"], "hit")
        self.assertEqual(fresh.model.calls, [])

    def test_infer_failure_is_not_swallowed_or_saved(self):
        backend = self.backend()
        with self.assertRaisesRegex(RuntimeError, "unexpected native infer failure"):
            self.synthesize(backend, text="fail")
        self.assertFalse(self.cache_dir.exists())

    def test_cache_under_model_directory_does_not_invalidate_itself(self):
        config = {**self.config, "voice_cache_dir": str(self.home / "checkpoints" / "profiles")}
        backend = self.backend(config)
        self.synthesize(backend)
        fresh = self.backend(config)
        self.assertEqual(self.synthesize(fresh)[0]["event"], "hit")
        self.assertEqual(fresh.model.calls, [])

    def test_transfer_uses_only_device_and_does_not_hide_device_errors(self):
        backend = self.backend()
        self.synthesize(backend)
        fresh = self.backend()
        transfers = []
        original_to = TEST_TORCH.Tensor.to
        def recorded_to(tensor, *args, **kwargs):
            transfers.append((args, kwargs))
            return original_to(tensor, *args, **kwargs)
        with patch.object(TEST_TORCH.Tensor, "to", new=recorded_to):
            self.synthesize(fresh)
        self.assertEqual(transfers, [((), {"device": "cpu"})] * 5)
        other = self.backend()
        with patch.object(TEST_TORCH.Tensor, "to", side_effect=RuntimeError("device transfer failed")):
            with self.assertRaisesRegex(RuntimeError, "device transfer failed"):
                self.synthesize(other)

    def test_real_fresh_process_restore(self):
        self.synthesize(self.backend(), emotion=self.emotion)
        script = '''
import json, sys
from test_voice_cache import NativeStub, TEST_TORCH, _torch
from kurumi_podcast.engine import IndexBackend
if _torch is None:
    sys.modules['torch'] = TEST_TORCH
backend = IndexBackend(json.loads(sys.argv[1]))
backend.model = NativeStub()
backend.synthesize('ok', sys.argv[4], sys.argv[2], sys.argv[3], 123)
assert backend.model.calls == [], backend.model.calls
assert backend.model.encoder_moves == [], backend.model.encoder_moves
'''
        env = {**os.environ, "PYTHONPATH": os.pathsep.join((
            str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]),
            os.environ.get("PYTHONPATH", "")))}
        result = subprocess.run([sys.executable, "-c", script, json.dumps(self.config),
                                 str(self.a), str(self.emotion), str(self.root / "fresh.result")],
                                env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn('"event": "hit"', result.stdout)
        self.assertIn('"source": "disk"', result.stdout)


if __name__ == "__main__":
    unittest.main()
