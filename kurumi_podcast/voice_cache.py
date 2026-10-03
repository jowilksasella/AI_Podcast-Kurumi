"""Optional, local persistence of IndexTTS 2.5's native conditioning tensors.

These profiles are encoder results, not standalone models or trained weights.
Importing this module (or constructing a cache) does not import torch.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import pickle
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .core import resolve_path


FORMAT = "kurumi-indextts2.5-conditioning"
SCHEMA_VERSION = 1
TENSOR_FIELDS = (
    "cache_spk_cond", "cache_s2mel_style", "cache_s2mel_prompt",
    "cache_mel", "cache_emo_cond",
)
PROMPT_FIELDS = ("cache_spk_audio_prompt", "cache_emo_audio_prompt")
_RANKS = dict(zip(TENSOR_FIELDS, (3, 2, 3, 3, 3)))


def _file_signature(path):
    path = Path(path).resolve()
    try:
        stat = path.stat()
    except FileNotFoundError:
        return {"path": str(path), "missing": True}
    return {"path": str(path), "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns, "ctime_ns": stat.st_ctime_ns}


def _file_inventory(root, suffixes, exclude=None):
    """Stat relevant source/weight/config files, never read or hash weights."""
    return [_file_signature(p) for p in sorted(Path(root).rglob("*"))
            if p.is_file() and p.suffix.lower() in suffixes
            and (exclude is None or exclude not in p.resolve().parents)]


@dataclass
class CacheRequest:
    key: str
    metadata: dict
    speaker: str
    emotion: str | None
    hit: bool = False

    @property
    def effective_emotion(self):
        # Native infer substitutes the speaker reference when emotion is None.
        return self.emotion or self.speaker


class PersistentVoiceCache:
    """Persist complete speaker/emotion pairs using the native cache contract."""

    def __init__(self, directory, home, model_dir, config):
        self.directory = Path(directory).resolve()
        self.home = Path(home).resolve()
        self.model_dir = Path(model_dir).resolve()
        self.config = config
        self._active = None

    def _metadata(self, model, speaker, emotion):
        import torch

        profiles = []
        for role, profile in sorted(self.config.get("voices", {}).items()):
            ref = profile.get("reference_audio")
            if ref and str(resolve_path(ref, self.config["_base"])) == speaker:
                profiles.append({"role": role, **{k: profile.get(k, "") for k in
                                 ("identity_label", "source_kind", "source_url",
                                  "reference_language")}})
        state = {k: str(getattr(model, k, None)) for k in (
            "model_version", "dtype", "use_bf16", "use_accel", "use_torch_compile",
            "use_cuda_kernel", "vram_offload", "encode_on_cpu", "_semantic_runs_on_cpu",
        )}
        # These are the effective, loaded settings, not just requested BF16 flags.
        for name in ("semantic_model", "campplus_model", "s2mel", "gpt"):
            module = getattr(model, name, None)
            if hasattr(module, "parameters"):
                parameter = next(module.parameters(), None)
                state[name + "_dtype"] = str(parameter.dtype) if parameter is not None else None
        source = inspect.getsourcefile(type(model))
        return {
            "format": FORMAT, "schema": SCHEMA_VERSION,
            "engine": self.config.get("engine", "IndexTTS2.5"),
            "class": type(model).__module__ + "." + type(model).__qualname__,
            "home": str(self.home), "model_dir": str(self.model_dir),
            "device": str(model.device), "torch_version": str(torch.__version__),
            "state": state, "loaded_config": str(getattr(model, "cfg", None)),
            "revision": str(self.config.get("voice_cache_revision", "")),
            "source": _file_inventory(self.home / "indextts", {".py"}),
            "class_source": _file_signature(source) if source else None,
            "model_files": _file_inventory(self.model_dir,
                {".pth", ".pt", ".bin", ".safetensors", ".json", ".yaml", ".yml"},
                exclude=self.directory),
            "speaker": _file_signature(speaker), "emotion": _file_signature(emotion),
            "voice_metadata": profiles,
        }

    def _event(self, event, request, **details):
        roles = request.metadata["voice_metadata"]
        identity = "; ".join(p["role"] + ": " + (p["identity_label"] or p["role"])
                             for p in roles) or str(Path(request.speaker).parent.name)
        print("[voice-cache] " + json.dumps({
            "event": event, "voice_identity": identity,
            "speaker": request.speaker, "emotion": request.effective_emotion,
            "key": request.key, "model_version": request.metadata["state"]["model_version"],
            **details,
        }, ensure_ascii=False), flush=True)

    def path_for(self, request):
        return self.directory / (request.key + ".pt")

    def _clear(self, model):
        # Required even when the path is unchanged: native only compares paths,
        # so replacing a reference or weight/config at that path must invalidate it.
        self._active = None
        for field in TENSOR_FIELDS + PROMPT_FIELDS:
            setattr(model, field, None)

    @staticmethod
    def _tensor_specs(tensors):
        import torch

        if not isinstance(tensors, dict) or set(tensors) != set(TENSOR_FIELDS):
            raise ValueError("incomplete native conditioning fields")
        specs = {}
        for name, tensor in tensors.items():
            if type(tensor) is not torch.Tensor or not tensor.is_floating_point():
                raise ValueError("conditioning must be plain floating point tensors")
            if tensor.ndim != _RANKS[name] or any(n <= 0 for n in tensor.shape):
                raise ValueError("incompatible native conditioning shape")
            specs[name] = {"type": "torch.Tensor", "dtype": str(tensor.dtype),
                           "shape": list(tensor.shape)}
        return specs

    def prepare(self, model, speaker, emotion=None):
        """Restore before native infer; on a miss force native re-encoding."""
        speaker = str(Path(speaker).resolve())
        emotion = str(Path(emotion).resolve()) if emotion else None
        metadata = self._metadata(model, speaker, emotion or speaker)
        key = hashlib.sha256(json.dumps(metadata, sort_keys=True, ensure_ascii=False,
                                      separators=(",", ":")).encode("utf-8")).hexdigest()
        request = CacheRequest(key, metadata, speaker, emotion)
        if not all(hasattr(model, name) for name in TENSOR_FIELDS + PROMPT_FIELDS):
            self._event("miss", request, reason="unsupported_native_cache_contract")
            return request
        if (self._active == (id(model), key)
                and model.cache_spk_audio_prompt == speaker
                and model.cache_emo_audio_prompt == request.effective_emotion
                and all(getattr(model, name) is not None for name in TENSOR_FIELDS)):
            request.hit = True
            self._event("hit", request, source="memory")
            return request

        import torch

        path = self.path_for(request)
        try:
            payload = torch.load(path, map_location="cpu", weights_only=True)
            if (not isinstance(payload, dict) or payload.get("key") != key
                    or payload.get("metadata") != metadata):
                raise ValueError("incompatible conditioning metadata")
            tensors = payload["tensors"]
            if self._tensor_specs(tensors) != payload["tensor_specs"]:
                raise ValueError("incompatible conditioning dtype/shape metadata")
        except FileNotFoundError:
            self._clear(model)
            self._event("miss", request, reason="not_found", path=str(path))
            return request
        except (OSError, EOFError, pickle.UnpicklingError, RuntimeError,
                ValueError, TypeError, KeyError) as error:
            # Only loading/validation failures are recoverable cache misses.
            self._clear(model)
            self._event("miss", request, reason="corrupt_or_incompatible", error=str(error), path=str(path))
            return request

        # Device errors (e.g. OOM) are NOT corrupt-cache failures. Propagate them.
        restored = {name: tensor.to(device=model.device) for name, tensor in tensors.items()}
        for name, tensor in restored.items():
            setattr(model, name, tensor)
        model.cache_spk_audio_prompt = speaker
        model.cache_emo_audio_prompt = request.effective_emotion
        self._active = (id(model), key)
        request.hit = True
        self._event("hit", request, source="disk", path=str(path))
        return request

    def save(self, model, request):
        """Save only after successful infer; atomic replacement works on Windows."""
        if request.hit:
            return
        if (getattr(model, "cache_spk_audio_prompt", None) != request.speaker
                or getattr(model, "cache_emo_audio_prompt", None) != request.effective_emotion):
            self._event("miss", request, reason="native_prompts_not_ready")
            return
        if self._metadata(model, request.speaker, request.effective_emotion) != request.metadata:
            self._clear(model)
            self._event("miss", request, reason="inputs_changed_during_infer")
            return

        import torch

        tensors = {name: getattr(model, name, None) for name in TENSOR_FIELDS}
        try:
            specs = self._tensor_specs(tensors)
        except ValueError as error:
            self._event("miss", request, reason="incomplete_native_cache", error=str(error))
            return
        payload = {"key": request.key, "metadata": request.metadata, "tensor_specs": specs,
                   "tensors": {name: value.detach().cpu().clone() for name, value in tensors.items()}}
        temporary = None
        path = self.path_for(request)
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.directory, suffix=".tmp", delete=False) as file:
                temporary = Path(file.name)
            torch.save(payload, temporary)
            os.replace(temporary, path)
        except OSError as error:
            self._event("miss", request, reason="save_failed", error=str(error), path=str(path))
            return
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        self._active = (id(model), request.key)
        self._event("saved", request, path=str(path))
