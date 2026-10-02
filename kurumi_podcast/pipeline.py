from __future__ import annotations

import copy
import os
import re
from pathlib import Path

from . import audio
from .core import (chapter_ranges, file_state, lead_speech_share, load_json,
                   natural_chunks, resolve_path, save_json, shifted_opening_rows,
                   validate_plan, write_documents)


def load_config(path):
    path = Path(path).resolve()
    config = load_json(path)
    config["_base"] = str(path.parent)
    return config


def resolve_voice(config, speaker, delivery):
    profile = config.get("voices", {}).get(speaker)
    if not profile or not profile.get("reference_audio"):
        raise ValueError(f"no actual reference voice is configured for {speaker}")
    voice = resolve_path(profile["reference_audio"], config["_base"])
    if not voice.is_file():
        raise FileNotFoundError(f"missing reference audio for {speaker}: {voice}")
    moods = profile.get("emotion_audio", {})
    emotion_value = moods.get(delivery) or moods.get("default")
    emotion = resolve_path(emotion_value, config["_base"]) if emotion_value else None
    if emotion and not emotion.is_file():
        raise FileNotFoundError(emotion)
    return voice, emotion, profile


def line_signature(line, config, plan_base, limit):
    if line.get("reuse_audio"):
        return {"text": line["text"], "speaker": line["speaker"],
                "reuse_audio": file_state(resolve_path(line["reuse_audio"], plan_base)),
                "sample_rate": config.get("sample_rate", 24000)}
    voice, emotion, _ = resolve_voice(config, line["speaker"], line["delivery"])
    home = os.environ.get("INDEXTTS_HOME") or config.get("index_home", "")
    return {
        "text": line["text"], "tts_text": line.get("tts_text", line["text"]),
        "speaker": line["speaker"], "voice": file_state(voice),
        "emotion": file_state(emotion) if emotion else None,
        "engine_home": str(resolve_path(home, config["_base"])) if home else "",
        "model_dir": config.get("model_dir", "checkpoints"),
        "engine": "IndexTTS2.5", "seed": config.get("seed", 20261002),
        "device": config.get("device", "cuda:0"),
        "use_bf16": config.get("use_bf16", True),
        "emo_alpha": config.get("emo_alpha", .5),
        "duration_factor": config.get("duration_factor", 1.0),
        "sample_rate": config.get("sample_rate", 24000), "chunk_chars": limit,
    }


def plausible_duration(seconds, text, factor=1.0):
    return max(.25, len(text) / 18) <= seconds <= max(8, len(text) * .34 * factor + 2)


def render(plan_path, config_path, out, stage="preview", approved=False, backend=None):
    if stage == "full" and not approved:
        raise ValueError("full rendering needs --approved-preview after the user's confirmation")
    plan_path = Path(plan_path).resolve()
    plan = validate_plan(load_json(plan_path), stage)
    if stage == "preview" and sum(len(r["text"]) for r in plan["lines"]) > 360:
        raise ValueError("write a genuine 30–60 second preview instead of synthesizing a long episode")
    config = load_config(config_path)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = out / "work"
    work.mkdir(exist_ok=True)
    cache_path = work / "cache.json"
    cache = load_json(cache_path) if cache_path.is_file() else {}
    rate = int(config.get("sample_rate", 24000))
    binary = config.get("ffmpeg", "ffmpeg")
    limit = int(config.get("segment_chars", 50))
    clips, rows_notes = [], {}
    owns_backend = backend is None
    try:
        for line in plan["lines"]:
            name = line["id"]
            cached = work / f"{name}.wav"
            signature = line_signature(line, config, plan_path.parent, limit)
            record = cache.get(name, {})
            valid = (cached.is_file() and record.get("signature") == signature
                     and record.get("audio_state") == file_state(cached))
            if not valid:
                if line.get("reuse_audio"):
                    source = resolve_path(line["reuse_audio"], plan_path.parent)
                    audio.normalize_source(source, cached, rate, binary)
                    clip = audio.trim_edges(audio.read_pcm(cached, rate), rate)
                    audio.write_pcm(cached, clip, rate)
                else:
                    voice, emotion, profile = resolve_voice(config, line["speaker"], line["delivery"])
                    rows_notes[line["speaker"]] = {
                        k: profile.get(k, "") for k in
                        ("identity_label", "source_kind", "source_url", "reference_language")
                    }
                    if backend is None:
                        from .engine import IndexBackend
                        backend = IndexBackend(config)
                    last_error = None
                    for attempt, chunk_limit in enumerate((limit, min(limit, 30))):
                        try:
                            parts = []
                            for part, chunk in enumerate(natural_chunks(line.get("tts_text", line["text"]), chunk_limit), 1):
                                raw = work / f"{name}_part{part:02d}_raw.wav"
                                pcm = work / f"{name}_part{part:02d}.wav"
                                seed = int(config.get("seed", 20261002)) + int.from_bytes(name.encode(), "little") % 10000 + part
                                raw.unlink(missing_ok=True)
                                backend.synthesize(chunk, raw, voice, emotion, seed)
                                audio.normalize_source(raw, pcm, rate, binary)
                                samples = audio.trim_edges(audio.read_pcm(pcm, rate), rate)
                                visible = re.sub(r"<([^<>|]+)\|[^<>]+>", r"\1", chunk)
                                if not plausible_duration(len(samples) / rate, visible,
                                                          float(config.get("duration_factor", 1))):
                                    raise RuntimeError("speech duration suggests repeated or missing text")
                                if parts:
                                    import numpy as np
                                    parts.append(np.zeros(round(.11 * rate)))
                                parts.append(samples)
                            import numpy as np
                            audio.write_pcm(cached, np.concatenate(parts), rate)
                            break
                        except (RuntimeError, ValueError) as error:
                            last_error = error
                            if attempt:
                                raise RuntimeError(f"{name}: bounded repair failed: {last_error}") from error
                    if not cached.is_file():
                        raise RuntimeError(f"{name}: no verified speech")
                cache[name] = {"signature": signature, "audio_state": file_state(cached)}
                save_json(cache_path, cache)
            profile = config.get("voices", {}).get(line["speaker"], {})
            rows_notes[line["speaker"]] = {
                k: profile.get(k, "") for k in
                ("identity_label", "source_kind", "source_url", "reference_language")
            }
            clips.append(audio.read_pcm(cached, rate))
            print(f"TURN_READY {name} {line['speaker']}", flush=True)
    finally:
        if owns_backend and backend is not None:
            backend.close()
    mixed, rows = audio.mix_turns(plan["lines"], clips, rate)
    rough = work / "mix.wav"
    audio.write_pcm(rough, mixed, rate)
    wav = out / "episode.wav"
    audio.ffmpeg(binary, ["-i", rough, "-af", "loudnorm=I=-18:TP=-1.5:LRA=9",
                          "-ac", "1", "-ar", rate, "-c:a", "pcm_s16le", wav])
    total = audio.duration(wav)
    if stage == "preview" and not 30 <= total <= 60:
        raise ValueError(f"preview is {total:.1f}s, outside 30–60s; revise the short script using its cache")
    share, seconds = lead_speech_share(rows, plan["lead"])
    if stage == "full" and share < .60:
        raise ValueError("the lead's effective speech share is below 60%; redistribute dialogue")
    manifest = {**{k: v for k, v in plan.items() if k != "lines"},
                "stage": stage, "audio": "episode.mp3", "wav": "episode.wav",
                "sample_rate": rate, "duration_seconds": total,
                "lead_speech_fraction": share, "speaker_seconds": seconds,
                "voice_notes": rows_notes, "turns": rows, "chapters": chapter_ranges(rows, total)}
    audio.export_mp3(wav, out / "episode.mp3", manifest, binary)
    write_documents(out, manifest)
    return manifest


def patch_opening(opening_plan, base, config_path, out, cut=0, backend=None):
    base, out = Path(base).resolve(), Path(out).resolve()
    if base == out:
        raise ValueError("write an opening revision to a new output directory")
    old = load_json(base / "manifest.json")
    shifted_opening_rows(old["turns"], [], cut, 0, old["duration_seconds"])
    old_wav = resolve_path(old["wav"], base)
    rate = int(old["sample_rate"])
    out.mkdir(parents=True, exist_ok=True)
    prefix_dir = out / "work" / "new-opening"
    prefix = render(opening_plan, config_path, prefix_dir, stage="opening", approved=True, backend=backend)
    if prefix["sample_rate"] != rate:
        raise ValueError("opening and body sample rates differ; preserve the existing master rate")
    rows, shift = shifted_opening_rows(old["turns"], prefix["turns"], cut,
                                      prefix["duration_seconds"], old["duration_seconds"])
    samples = audio.join_mastered(audio.read_pcm(prefix_dir / "episode.wav", rate),
                                  audio.read_pcm(old_wav, rate), cut, rate)
    wav = out / "episode.wav"
    audio.write_pcm(wav, samples, rate)
    total = audio.duration(wav)
    share, seconds = lead_speech_share(rows, old["lead"])
    if share < .60:
        raise ValueError("opening revision would make the lead secondary")
    characters = {}
    for row in rows:
        characters[row["speaker"]] = characters.get(row["speaker"], 0) + len(row["text"])
    manifest = {**old, "duration_seconds": total, "turns": rows,
                "chapters": chapter_ranges(rows, total),
                "lead_speech_fraction": share, "speaker_seconds": seconds,
                "lead_text_fraction": characters.get(old["lead"], 0) / sum(characters.values()),
                "speaker_characters": characters,
                "revision": {"type": "opening", "replaced_until": cut,
                             "body_shift_seconds": shift, "body_preserved": True}}
    manifest["voice_notes"] = {**old.get("voice_notes", {}), **prefix.get("voice_notes", {})}
    config = load_config(config_path)
    binary = config.get("ffmpeg", "ffmpeg")
    audio.export_mp3(wav, out / "episode.mp3", manifest, binary)
    audio.ffmpeg(binary, ["-i", wav, "-t", min(60, total),
                          "-af", f"afade=t=out:st={max(0,min(60,total)-1)}:d=1",
                          "-c:a", "pcm_s16le", out / "opening-preview.wav"])
    write_documents(out, manifest)
    return manifest


def extract_source(path, out):
    path = Path(path).resolve()
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(""):
            raise ValueError("PDF is encrypted and requires a supplied password")
        pages = [{"page": i, "text": page.extract_text() or ""} for i, page in enumerate(reader.pages, 1)]
        metadata = {k: str(v) for k, v in (reader.metadata or {}).items()}
        report = {"file": str(path), "page_count": len(pages), "metadata": metadata,
                  "pages": pages, "empty_text_pages": [p["page"] for p in pages if not p["text"].strip()],
                  "visual_review_required": True,
                  "note": "Text extraction does not replace reading figures and tables."}
    elif path.suffix.lower() in {".txt", ".md"}:
        report = {"file": str(path), "page_count": 1,
                  "pages": [{"page": 1, "text": path.read_text(encoding="utf-8-sig")}],
                  "empty_text_pages": [], "visual_review_required": False}
    else:
        raise ValueError("extract supports PDF, TXT and Markdown")
    save_json(out, report)
    return report
