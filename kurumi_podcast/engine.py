from __future__ import annotations

import inspect
import math
import os
import random
import sys
import wave
from contextlib import contextmanager
from pathlib import Path

from .core import resolve_path


DEFAULT_GENERATION_KWARGS = {
    "do_sample": False, "top_p": .8, "top_k": 30, "temperature": .4,
    "num_beams": 3, "repetition_penalty": 8.0, "length_penalty": 0.0,
    "max_mel_tokens": 1500, "diffusion_steps": 25,
}


def speech_settings(config):
    """Canonical controls shared by inference and the waveform cache signature."""
    mode = config.get("speech_mode", "continuous")
    if mode not in ("continuous", "legacy_chunks"):
        raise ValueError("speech_mode must be continuous or legacy_chunks")
    overrides = config.get("generation_kwargs", {})
    if not isinstance(overrides, dict):
        raise ValueError("generation_kwargs must be an object")
    unknown = set(overrides) - set(DEFAULT_GENERATION_KWARGS)
    if unknown:
        raise ValueError(f"unsupported generation_kwargs: {', '.join(sorted(unknown))}")
    generation = {**DEFAULT_GENERATION_KWARGS, **overrides}
    if type(generation["do_sample"]) is not bool:
        raise ValueError("generation_kwargs.do_sample must be a boolean (not emotion use_random)")
    for name in ("top_k", "num_beams", "max_mel_tokens", "diffusion_steps"):
        value = generation[name]
        minimum = 0 if name == "top_k" else 1
        if type(value) is not int or value < minimum:
            raise ValueError(f"generation_kwargs.{name} must be an integer >= {minimum}")
    for name in ("top_p", "temperature", "repetition_penalty", "length_penalty"):
        value = generation[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"generation_kwargs.{name} must be a finite number")
        if name != "length_penalty" and value <= 0:
            raise ValueError(f"generation_kwargs.{name} must be positive")
        if name == "top_p" and value > 1:
            raise ValueError("generation_kwargs.top_p must be <= 1")
    maximum = config.get("max_text_tokens_per_segment", 160)
    interval = config.get("interval_silence_ms", 0 if mode == "continuous" else 110)
    if type(maximum) is not int or maximum < 1:
        raise ValueError("max_text_tokens_per_segment must be a positive integer")
    if type(interval) is not int or interval < 0:
        raise ValueError("interval_silence_ms must be a nonnegative integer")
    return {"speech_mode": mode, "generation_kwargs": generation,
            "max_text_tokens_per_segment": maximum, "interval_silence_ms": interval}


class ContinuousContextError(ValueError):
    """The requested turn would not retain one native context."""


class UnsupportedContinuousContext(RuntimeError):
    """This native backend cannot prove the required single-segment boundary."""


@contextmanager
def continuous_context_guard(model, text, max_tokens, lang="ZH"):
    """Guard the REAL normalized, pronunciation-expanded native split boundary.

    No reimplementation of normalization/tokenization and no capacity/VRAM
    overrides. The wrapper runs before GPT synthesis in IndexTTS2.5, restores
    the exact original instance/class attribute even on failures, and refuses
    backends which never invoke it. Use this backend sequentially, not in
    concurrent threads sharing one model.
    """
    advice = "rewrite the script as natural dialogue turns or explicitly select speech_mode='legacy_chunks'"
    if type(getattr(model, "low_vram", None)) is not bool:
        raise UnsupportedContinuousContext("continuous: native low_vram policy is unverifiable; " + advice)
    if model.low_vram and len(text) > 40:
        raise ContinuousContextError("continuous: native low_vram auto-split applies to raw text >40 characters; " + advice)
    original = getattr(model, "split_text_by_tokens", None)
    token_len = getattr(model, "_token_len", None)
    try:
        capacity = model.gpt.text_pos_embedding.emb.num_embeddings
    except AttributeError:
        capacity = None
    if not callable(original) or not callable(token_len) or type(capacity) is not int or capacity < 3:
        raise UnsupportedContinuousContext("continuous: native token helper/capacity is unsupported; " + advice)
    try:
        inspect.signature(original).bind("text", max_tokens, f"<|{lang.lower()}|> ")
    except (TypeError, ValueError) as error:
        raise UnsupportedContinuousContext("continuous: unsupported native token-helper signature; " + advice) from error
    marker = object()
    try:
        previous = vars(model).get("split_text_by_tokens", marker)
    except TypeError as error:
        raise UnsupportedContinuousContext("continuous: native boundary has no inspectable instance state") from error
    checks = []

    def checked_split(processed_text, max_tokens_arg, lang_prefix=""):
        if checks:
            raise UnsupportedContinuousContext("continuous: native invoked the token boundary more than once")
        if max_tokens_arg != max_tokens or lang_prefix != f"<|{lang.lower()}|> ":
            raise UnsupportedContinuousContext("continuous: native changed the token budget/language boundary")
        segments = original(processed_text, max_tokens_arg, lang_prefix)
        if not isinstance(segments, (list, tuple)) or not all(isinstance(s, str) for s in segments):
            raise UnsupportedContinuousContext("continuous: unsupported native split result")
        if len(segments) != 1:
            raise ContinuousContextError(f"continuous: native token budget requires {len(segments)} segments; " + advice)
        if not processed_text or segments[0] != processed_text:
            raise UnsupportedContinuousContext("continuous: native split did not preserve the complete processed text")
        # Protected pronunciation atoms can remain indivisible even when too
        # large. Also verify the actual native capacity, not merely len==1.
        lengths = [token_len(processed_text), token_len(lang_prefix), token_len(lang_prefix + processed_text)]
        if any(type(n) is not int or n < 0 for n in lengths):
            raise UnsupportedContinuousContext("continuous: unsupported native token lengths")
        ceiling = min(max_tokens, capacity - 2)
        budget = max(1, ceiling - lengths[1])
        if lengths[0] > budget or lengths[2] > ceiling:
            raise ContinuousContextError("continuous: processed text exceeds native token capacity; " + advice)
        checks.append({"segments": 1, "text_tokens": lengths[0], "budget": budget})
        return segments

    try:
        setattr(model, "split_text_by_tokens", checked_split)
    except (AttributeError, TypeError) as error:
        raise UnsupportedContinuousContext("continuous: native token boundary cannot be guarded") from error
    try:
        yield checks
        if len(checks) != 1:
            raise UnsupportedContinuousContext("continuous: native never invoked the guarded token helper; " + advice)
    finally:
        if previous is marker:
            delattr(model, "split_text_by_tokens")
        else:
            setattr(model, "split_text_by_tokens", previous)


def index_home(config):
    value = os.environ.get("INDEXTTS_HOME") or config.get("index_home")
    if not value:
        raise ValueError("set INDEXTTS_HOME or index_home to the existing IndexTTS 2.5 package")
    home = resolve_path(value, config["_base"])
    if not (home / "indextts" / "infer_v2_5.py").is_file():
        raise ValueError(f"IndexTTS 2.5 infer_v2_5.py was not found under {home}")
    return home


def import_engine(home):
    sys.path.insert(0, str(home))
    os.chdir(home)
    from indextts.infer_v2_5 import IndexTTS2
    return IndexTTS2


class IndexBackend:
    """Lazy local backend; never fabricates speech or silently changes the engine."""

    def __init__(self, config):
        speech_settings(config)
        self.config = config
        self.model = None
        self.home = index_home(config)
        self.voice_cache = None
        if config.get("voice_cache_dir"):
            from .voice_cache import PersistentVoiceCache
            self.voice_cache = PersistentVoiceCache(
                resolve_path(config["voice_cache_dir"], config["_base"]), self.home,
                resolve_path(config.get("model_dir", "checkpoints"), self.home), config,
            )

    def _load(self):
        if self.model is not None:
            return
        if self.config.get("offline", True):
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        cls = import_engine(self.home)
        import torch
        torch.set_num_threads(int(self.config.get("cpu_threads", 4)))
        model_dir = resolve_path(self.config.get("model_dir", "checkpoints"), self.home)
        device = self.config.get("device", "cuda:0")
        kwargs = dict(
            model_dir=str(model_dir), cfg_path=str(model_dir / "config.yaml"),
            device=device, use_bf16=bool(self.config.get("use_bf16", True)) and device != "cpu",
            use_cuda_kernel=False, use_deepspeed=False, use_accel=False,
            use_torch_compile=False, use_qwen_emo=False, vram_offload=True,
            lora_dir=None,
        )
        parameters = inspect.signature(cls.__init__).parameters
        if not any(p.kind == p.VAR_KEYWORD for p in parameters.values()):
            kwargs = {k: v for k, v in kwargs.items() if k in parameters}
        self.model = cls(**kwargs)

    def synthesize(self, text, target, voice, emotion, seed):
        settings = speech_settings(self.config)
        self._load()
        import numpy as np
        import torch
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        request = self.voice_cache.prepare(self.model, voice, emotion) if self.voice_cache else None
        kwargs = dict(
            spk_audio_prompt=request.speaker if request else str(voice),
            text=text, lang="ZH",
            emo_audio_prompt=request.emotion if request else str(emotion) if emotion else None,
            emo_alpha=float(self.config.get("emo_alpha", .5)) if emotion else 1.0,
            emo_vector=None, use_emo_text=False, use_random=False,
            duration_factor=float(self.config.get("duration_factor", 1.0)),
            interval_silence=settings["interval_silence_ms"],
            max_text_tokens_per_segment=settings["max_text_tokens_per_segment"],
            verbose=True, **settings["generation_kwargs"],
        )
        if settings["speech_mode"] == "continuous":
            with continuous_context_guard(self.model, text, settings["max_text_tokens_per_segment"]):
                result = self.model.infer(output_path=None, **kwargs)
            if not isinstance(result, tuple) or len(result) != 2:
                raise RuntimeError("continuous: native returned no PCM; no retry or fallback")
            rate, data = result
            data = np.asarray(data)
            if type(rate) is not int or rate <= 0 or data.ndim != 2 or min(data.shape) <= 0:
                raise RuntimeError("continuous: invalid native PCM shape/sample rate")
            if data.dtype != np.dtype("int16"):
                raise RuntimeError("continuous: expected native PCM16; refusing guessed rescaling")
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(target), "wb") as writer:
                writer.setnchannels(int(data.shape[1]))
                writer.setsampwidth(2)
                writer.setframerate(rate)
                writer.writeframes(data.astype("<i2", copy=False).tobytes(order="C"))
        else:
            result = self.model.infer(output_path=str(target), **kwargs)
            if result is None:
                raise RuntimeError("the native model returned no speech")
        if not Path(target).is_file():
            raise RuntimeError("the model returned without creating speech")
        if request is not None:
            self.voice_cache.save(self.model, request)

    def close(self):
        if self.model is not None:
            self.model = None
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

