"""Frozen reference identities and a new local binding, not historical audio certification."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import re
import sys
from importlib import metadata
from pathlib import Path

from .core import file_state, load_json, natural_chunks, resolve_path, save_json

ORIGINAL = "original-chat-20261002"


def original_recipe():
    source = Path(__file__).resolve().parents[1] / "recipes" / f"{ORIGINAL}.json"
    if not source.is_file():
        source = Path(sys.prefix) / "share" / "kurumi-podcast" / "recipes" / source.name
    return load_json(source)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def content_identity(path):
    path = Path(path)
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return {"sha256": sha.hexdigest(), "size": path.stat().st_size}


def recipe_id(config):
    value = config.get("recipe", ORIGINAL)
    if value not in (ORIGINAL, "custom"):
        raise ValueError(f"unknown recipe {value!r}; no implicit recipe fallback")
    if value == "custom" and config.get("original_lock"):
        raise ValueError("custom is non-restoration; remove the original binding explicitly")
    return value


def effective_settings(config):
    restored = recipe_id(config) == ORIGINAL
    if restored:
        aliases = {"speech_mode", "generation_kwargs", "interval_silence_ms"} & set(config)
        if aliases:
            raise ValueError(f"original recipe rejects alternate controls: {sorted(aliases)}")
    defaults = original_recipe()["settings"]
    settings = copy.deepcopy(defaults)
    if not restored:
        settings["chunk_policy"] = "always"
    for key in defaults:
        if key not in config:
            continue
        if restored and config[key] != defaults[key]:
            raise ValueError(f"original recipe settings drift: {key}; custom is non-restoration")
        if isinstance(settings[key], dict):
            if not isinstance(config[key], dict):
                raise ValueError(f"{key} must be an object")
            unknown = set(config[key]) - set(settings[key])
            if unknown:
                raise ValueError(f"unsupported {key} settings: {sorted(unknown)}")
            settings[key].update(config[key])
        else:
            settings[key] = config[key]
    # Do not accept silently ignored flat decoder overrides.
    for key, value in settings["decoder"].items():
        if key in config:
            if restored and config[key] != value:
                raise ValueError(f"original recipe decoder drift: {key}")
            settings["decoder"][key] = config[key]
    return settings


def engine_snapshot(config):
    home = resolve_path(os.environ.get("INDEXTTS_HOME") or config.get("index_home", ""), config["_base"])
    model = resolve_path(config.get("model_dir", "checkpoints"), home)
    required = [home / "indextts" / "infer_v2_5.py", model / "config.yaml"]
    optional = [home / "indextts" / name for name in
                ("gpt/model_v2.py", "utils/front.py", "utils/tokenizer.py", "utils/common.py")]
    optional += [model / name for name in ("bpe.model", "tokenizer.json", "glossary.yaml")]
    files = {}
    for path in required + [p for p in optional if p.is_file()]:
        if not path.is_file():
            raise FileNotFoundError(f"missing native binding file: {path}")
        files[str(path)] = {**file_state(path), **content_identity(path)}
    # Large model weights are identified by file state, never read/hashes of GB weights.
    weights = [file_state(p) for p in sorted(model.glob("*"))
               if p.is_file() and p.suffix in {".pth", ".pt", ".ckpt", ".safetensors"}]
    software = {"python": platform.python_version()}
    for name in ("numpy", "torch", "torchaudio", "transformers", "safetensors"):
        try:
            software[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            software[name] = None
    return {"index_home": str(home), "model_dir": str(model), "files": files,
            "weight_file_states": weights, "software": software,
            "binding_kind": "new-current-environment", "historical_native_verified": False}


def bound_voices(recipe, assets):
    voices = {}
    for name, spec in recipe["voices"].items():
        profile = {k: v for k, v in spec.items() if k not in {"speaker_slot", "emotion_slots"}}
        profile["reference_audio"] = str(assets / spec["speaker_slot"])
        profile["emotion_audio"] = {k: str(assets / slot) for k, slot in spec["emotion_slots"].items()}
        voices[name] = profile
    return voices


def reference_snapshot(recipe, assets):
    refs = {}
    for slot, expected in recipe["assets"].items():
        path = assets / slot
        if not path.is_file():
            raise FileNotFoundError(f"missing original asset slot: {slot}")
        identity = content_identity(path)
        if identity != expected:
            raise ValueError(f"original asset identity mismatch: {slot}")
        refs[slot] = {"path": str(path), **identity}
    return refs


def bind_original(assets, index_home, out):
    """Verify all eight frozen input identities and save only an ignored local config."""
    assets, index_home, out = Path(assets).resolve(), Path(index_home).resolve(), Path(out).resolve()
    if not out.name.endswith(".local.json"):
        raise ValueError("binding output must end in .local.json (ignored local configuration)")
    recipe = original_recipe()
    config = {"recipe": ORIGINAL, "index_home": str(index_home), "model_dir": "checkpoints",
              "ffmpeg": "ffmpeg", **copy.deepcopy(recipe["settings"]),
              "voices": bound_voices(recipe, assets), "_base": str(out.parent)}
    refs = reference_snapshot(recipe, assets)
    engine = engine_snapshot(config)
    if engine["index_home"] != str(index_home):
        raise ValueError("INDEXTTS_HOME overrides --index-home; bind the explicitly selected engine")
    snapshot = {"recipe": ORIGINAL, "recipe_sha256": digest(recipe), "assets_dir": str(assets),
                "references": refs, "voices": copy.deepcopy(config["voices"]),
                "settings": effective_settings(config), "engine": engine,
                "binding_kind": "new-current-environment", "historical_native_verified": False,
                "listening_verified": False, "historical_bits_verified": False}
    config["original_lock"] = {"snapshot": snapshot, "sha256": digest(snapshot)}
    del config["_base"]
    save_json(out, config)
    return config


def validate_runtime(config, plan=None):
    """Run before model import or output creation, including every employed delivery."""
    rid = recipe_id(config)
    if plan and plan.get("recipe", rid) != rid:
        raise ValueError("plan/config recipe override mismatch")
    settings = effective_settings(config)
    recipe = original_recipe()
    if rid == "custom":
        return {"recipe": "custom", "restoration": False, "label": "custom / non-restoration",
                "effective_settings": settings}
    voices = config.get("voices", {})
    if set(voices) != set(recipe["voices"]):
        raise ValueError("original recipe speaker/actor choice mismatch")
    deliveries = [(r["speaker"], r["delivery"]) for r in plan["lines"]] if plan else [
        (name, delivery) for name in voices for delivery in recipe["voices"][name]["emotion_slots"]]
    for name, delivery in deliveries:
        if name not in voices:
            raise ValueError(f"original recipe speaker/actor choice mismatch: {name}")
        if not voices[name].get("emotion_audio", {}).get(delivery):
            raise ValueError(f"{name}/{delivery}: original recipe requires independent emotion_audio; "
                             "empty moods force native alpha=1 instead of .5")
    lock = config.get("original_lock")
    if not isinstance(lock, dict) or not isinstance(lock.get("snapshot"), dict):
        raise ValueError("missing original binding lock; run bind-original")
    snapshot = lock["snapshot"]
    if lock.get("sha256") != digest(snapshot):
        raise ValueError("original binding lock changed; run bind-original for a new binding")
    if snapshot.get("recipe_sha256") != digest(recipe) or snapshot.get("recipe") != rid:
        raise ValueError("original binding recipe lock mismatch")
    if snapshot.get("settings") != settings:
        raise ValueError("original binding settings lock changed")
    assets = Path(snapshot["assets_dir"])
    expected_voices = bound_voices(recipe, assets)
    if voices != expected_voices or snapshot.get("voices") != expected_voices:
        raise ValueError("original binding voice/actor/delivery override changed")
    refs = reference_snapshot(recipe, assets)
    if refs != snapshot.get("references"):
        raise ValueError("original binding reference lock changed")
    engine = engine_snapshot(config)
    if engine != snapshot.get("engine"):
        raise ValueError("original binding engine lock changed; bind current environment anew")
    return {"recipe": rid, "restoration": True, "label": "reference-input/settings restoration",
            "effective_settings": settings, "public_recipe": recipe,
            "binding": copy.deepcopy(snapshot), "lock_sha256": lock["sha256"],
            "listening_verified": False, "historical_bits_verified": False}


def turn_seed(line, settings, stage="preview"):
    name = line["id"]
    number = int(name) if name.isdecimal() else int.from_bytes(
        hashlib.sha256(name.encode("utf-8")).digest()[:4], "big") % 1000000
    base = settings["opening_seed"] if stage == "opening" else settings["seed"] + settings["seed_offset"]
    # NumPy accepts a uint32 seed. Named ids use a stable hash, never Python hash().
    return (int(base) + number) % (2 ** 32)


def spoken_text(text):
    substitutions = (("伽马", "<伽|GA1><马|MA3>"), ("减震器", "减<震|ZHEN4>器"),
                     ("卖", "<卖|MAI4>"), ("买", "<买|MAI3>"))
    parts = re.split(r"(<[^<>]+\|[^<>]+>)", text)
    for i in range(0, len(parts), 2):
        for source, target in substitutions:
            parts[i] = parts[i].replace(source, target)
    return "".join(parts)


def turn_chunks(line, settings, restored, stage="preview"):
    text = line.get("tts_text", line["text"])
    limit = int(settings["segment_chars"])
    if restored:
        # Historical turn 37/44 were repairs of one paper, not reusable IDs.
        # Preserve natural short exchanges; only long exchanges need chunking.
        short = len(re.sub(r"<([^<>|]+)\|[^<>]+>", r"\1", text)) > limit
        chunks = natural_chunks(text, limit) if short else [text]
        return [spoken_text(chunk) for chunk in chunks]
    return natural_chunks(text, limit) if settings["chunk_policy"] == "always" else [text]


def native_inference_settings(config, stage="preview"):
    settings = effective_settings(config)
    keys = ("lang", "emo_alpha", "use_random", "duration_factor", "interval_silence",
            "max_text_tokens_per_segment", "max_mel_tokens", "diffusion_steps")
    kwargs = {key: settings[key] for key in keys}
    if stage == "opening":
        for key in ("max_text_tokens_per_segment", "max_mel_tokens"):
            kwargs[key] = settings["opening_" + key]
    return {**kwargs, **settings["decoder"], "verbose": False}
