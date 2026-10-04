from __future__ import annotations

import copy
import json
import re
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_path(value, base):
    path = Path(value).expanduser()
    return (path if path.is_absolute() else Path(base) / path).resolve()


def file_state(path):
    path = Path(path).resolve()
    stat = path.stat()
    return {"path": str(path), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def validate_plan(data, stage="preview"):
    if not isinstance(data, dict):
        raise ValueError("plan must be a JSON object")
    plan = copy.deepcopy(data)
    if stage not in {"preview", "full", "opening"}:
        raise ValueError("stage must be preview, full or opening")
    if not isinstance(plan.get("title"), str) or not plan["title"].strip():
        raise ValueError("title is required")
    lead = plan.setdefault("lead", "久留美")
    if not isinstance(lead, str) or not lead.strip():
        raise ValueError("lead must name the main speaker")
    lines = plan.get("lines")
    if not isinstance(lines, list) or not lines:
        raise ValueError("lines must be a non-empty list")
    seen = set()
    counts = {}
    for i, line in enumerate(lines, 1):
        if not isinstance(line, dict):
            raise ValueError(f"turn {i} must be a JSON object")
        line.setdefault("id", f"{i:03d}")
        line.setdefault("chapter", "正文")
        line.setdefault("delivery", "explain")
        identifier = line["id"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", identifier):
            raise ValueError(f"unsafe line id: {identifier!r}")
        if identifier in seen:
            raise ValueError(f"duplicate line id: {identifier}")
        seen.add(identifier)
        if not isinstance(line.get("speaker"), str) or not line["speaker"].strip():
            raise ValueError(f"{identifier}: speaker is required")
        if not isinstance(line.get("text"), str) or not line["text"].strip():
            raise ValueError(f"{identifier}: text is required")
        if "tts_text" in line and (not isinstance(line["tts_text"], str) or not line["tts_text"].strip()):
            raise ValueError(f"{identifier}: tts_text must be non-empty text")
        if re.search(r"<[^<>]+\|[^<>]+>", line["text"]):
            raise ValueError(f"{identifier}: pronunciation markup belongs in tts_text, not text")
        if len(line["text"]) > 180:
            raise ValueError(f"{identifier}: split this long turn into a natural exchange")
        if not isinstance(line["chapter"], str) or not line["chapter"].strip():
            raise ValueError(f"{identifier}: chapter is required")
        if line["delivery"] not in {"explain", "question", "comment", "joke"}:
            raise ValueError(f"{identifier}: unsupported delivery")
        gap = line.get("after_ms", 140)
        if not isinstance(gap, (int, float)) or not -120 <= gap <= 3000:
            raise ValueError(f"{identifier}: after_ms must be between -120 and 3000")
        counts[line["speaker"]] = counts.get(line["speaker"], 0) + len(line["text"])
    if lead not in counts:
        raise ValueError("the lead character has no dialogue")
    if stage != "opening" and len(counts) < 2 and not plan.get("allow_solo", False):
        raise ValueError("the default dialogue needs at least two speakers")
    if not lines[0].get("opening", False):
        raise ValueError("mark and write an opening that establishes people and topic")
    share = counts[lead] / sum(counts.values())
    minimum = .65 if stage == "full" else .60 if stage == "preview" else 0
    if share < minimum:
        raise ValueError(f"{lead} is not the main speaker: text share {share:.1%} < {minimum:.0%}")
    plan["lead_text_fraction"] = share
    plan["speaker_characters"] = counts
    return plan


def natural_chunks(text, limit=50):
    if limit < 8:
        raise ValueError("chunk limit is too short")
    # Tokenize first: even punctuation inside a phoneme annotation is indivisible.
    atoms = re.findall(r"<[^<>]+\|[^<>]+>|.", text, re.S)

    def split_at(items, punctuation):
        groups, current = [], []
        for atom in items:
            current.append(atom)
            if atom in punctuation:
                groups.append(current)
                current = []
        if current:
            groups.append(current)
        return groups

    pieces = split_at(atoms, "。！？!?")
    result, buffer = [], ""
    for sentence in pieces:
        fragments = split_at(sentence, "，；") if len(sentence) > limit else [sentence]
        for atoms in fragments:
            fragment = "".join(atoms)
            if buffer and len(buffer + fragment) > limit:
                result.append(buffer)
                buffer = ""
            if len(atoms) > limit:
                if buffer:
                    result.append(buffer)
                    buffer = ""
                while len(atoms) > limit:
                    result.append("".join(atoms[:limit]))
                    atoms = atoms[limit:]
                fragment = "".join(atoms)
            buffer += fragment
    if buffer:
        result.append(buffer)
    return result or [text]


def chapter_ranges(rows, total):
    chapters = []
    for row in rows:
        if not chapters or chapters[-1]["title"] != row["chapter"]:
            if chapters:
                chapters[-1]["end"] = row["start"]
            chapters.append({"title": row["chapter"], "start": row["start"]})
    if chapters:
        chapters[-1]["end"] = total
    return chapters


def lead_speech_share(rows, lead):
    seconds = {}
    for row in rows:
        seconds[row["speaker"]] = seconds.get(row["speaker"], 0) + row["duration"]
    denominator = sum(seconds.values())
    if denominator <= 0:
        raise ValueError("no spoken audio")
    return seconds.get(lead, 0) / denominator, seconds


def shifted_opening_rows(base_rows, prefix_rows, cut, prefix_seconds, total):
    if cut < 0 or cut > total:
        raise ValueError("opening cut is outside the episode")
    boundaries = [0.0, total] + [r[k] for r in base_rows for k in ("start", "end")]
    if not any(abs(x - cut) <= .002 for x in boundaries):
        raise ValueError("replace-until must align to a turn start or end, not cut speech")
    shift = prefix_seconds - cut
    kept = []
    for row in base_rows:
        if row["end"] <= cut + .002:
            continue
        if row["start"] < cut - .002:
            raise ValueError("cut crosses a spoken turn")
        shifted = copy.deepcopy(row)
        shifted["start"] += shift
        shifted["end"] += shift
        kept.append(shifted)
    prefix = copy.deepcopy(prefix_rows)
    for row in prefix:
        row["chapter"] = base_rows[0]["chapter"]
    return prefix + kept, shift


def time_label(seconds):
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def srt_time(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{sec:02d},{ms:03d}"


def caption_chunks(text, limit=24):
    return natural_chunks(text, limit)


def write_documents(out, manifest):
    out = Path(out)
    rows = manifest["turns"]
    text = [manifest["title"], "", "普通话角色闲聊 · AI生成/同人角色分工",
            f"主讲：{manifest['lead']}；时长：{time_label(manifest['duration_seconds'])}；"
            f"主讲有效发言占比：{manifest['lead_speech_fraction']:.1%}。",
            "字幕为发言区间内按文字长度分配的初稿，非精确字级对齐。", ""]
    for speaker, profile in manifest.get("voice_notes", {}).items():
        text.append(f"{speaker}：{profile.get('identity_label', speaker)}")
        if profile.get("source_url"):
            text.append("来源：" + profile["source_url"])
    if manifest.get("source_note"):
        text += ["", "资料说明：" + manifest["source_note"]]
    text += ["", "章节"]
    for chapter in manifest["chapters"]:
        text.append(time_label(chapter["start"]) + "  " + chapter["title"])
    text += ["", "正文"]
    subtitles, cue = [], 1
    for row in rows:
        text += [f"[{time_label(row['start'])}] {row['speaker']}：{row['text']}", ""]
        chunks = caption_chunks(row["text"])
        count, offset = sum(len(c) for c in chunks), 0
        for chunk in chunks:
            start = row["start"] + row["duration"] * offset / count
            offset += len(chunk)
            end = row["start"] + row["duration"] * offset / count
            subtitles += [str(cue), srt_time(start) + " --> " + srt_time(end),
                          row["speaker"] + "：" + chunk, ""]
            cue += 1
    (out / "transcript.txt").write_text("\n".join(text), encoding="utf-8-sig")
    (out / "subtitles.srt").write_text("\n".join(subtitles), encoding="utf-8-sig")
    save_json(out / "manifest.json", manifest)
