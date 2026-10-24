"""One-minute series, anime-reference preparation and post-render checks.

These are the steps used for the GEX one-minute series (examples/gex/): split one series file into
standalone episode plans, render them with one shared engine, compress long pauses in anime timbre
references, check every turn with local Whisper, and write a line-by-line source map for the
separate shorts/video agent.
"""
from __future__ import annotations

import difflib
import json
import re
import tempfile
from pathlib import Path

from . import audio
from .core import language_warnings, load_json, resolve_path, save_json, validate_plan

# Measured on the approved anime cast (ep01: 273 visible characters -> 46.1 s, incl. turn gaps).
CHARS_PER_SECOND = 5.9


def visible(text):
    return len(re.sub(r"\s", "", text))


def _line(row):
    if isinstance(row, dict):
        return {"speaker": row["speaker"], "delivery": row.get("delivery", "explain"), "text": row["text"]}
    speaker, delivery, text = row
    return {"speaker": speaker, "delivery": delivery, "text": text}


def split_series(series_path, out, target=(45, 58), hook_max=26, turn_max=50):
    """Write epNN/plan.json for every episode of a series file and a series.md overview.

    Each episode stands alone: the first line is the hook (no self-introduction), both first two
    lines carry the opening flag the validator needs, and estimated length uses CHARS_PER_SECOND.
    """
    series_path, out = Path(series_path).resolve(), Path(out).resolve()
    series = load_json(series_path)
    lead = series.get("lead", "久留美")
    first = int(series.get("first_episode", 1))
    episodes = series.get("episodes") or []
    if not episodes:
        raise ValueError("series needs a non-empty episodes list")
    source = series.get("source", "")
    rows, table = [], []
    for n, episode in enumerate(episodes, first):
        lines = [_line(row) for row in episode["lines"]]
        for line in lines:
            line["chapter"] = episode["title"]
        if len(lines) > 1:
            lines[0]["opening"] = lines[1]["opening"] = True
        refs = episode.get("sources", "")
        if refs:
            lines[0]["source_refs"] = [{"source": source if refs.startswith("p") else refs, "note": refs}]
        plan = {"title": f"{series.get('series', series_path.stem)} {n:02d}｜{episode['title']}",
                "language": series.get("language", "普通话"), "lead": lead,
                "source_note": f"{source}；本集：{refs}。音色 {series.get('config_hint', '')}。".replace("。。", "。"),
                "lines": lines}
        checked = validate_plan(plan, "preview")
        folder = out / f"ep{n:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        total = sum(visible(line["text"]) for line in lines)
        lead_chars = sum(visible(line["text"]) for line in lines if line["speaker"] == lead)
        estimate = round(total / CHARS_PER_SECOND, 1)
        hook = visible(lines[0]["text"])
        warnings = language_warnings(checked)
        if not target[0] <= estimate <= target[1]:
            warnings.append({"issue": "estimated_length", "seconds": estimate, "target": list(target)})
        if hook > hook_max:
            warnings.append({"issue": "long_hook", "characters": hook, "max": hook_max})
        warnings += [{"id": f"{i:03d}", "issue": "long_turn", "characters": visible(line["text"])}
                     for i, line in enumerate(lines, 1) if visible(line["text"]) > turn_max]
        rows.append({"episode": f"ep{n:02d}", "title": episode["title"], "characters": total,
                     "lead_fraction": round(lead_chars / total, 3), "hook_characters": hook,
                     "estimated_seconds": estimate, "warnings": warnings})
        table.append(f"| {n:02d} | {episode['title']} | {lines[0]['text']} | {refs} | {total} | "
                     f"{lead_chars / total:.0%} | ≈{estimate:.0f} 秒 |")
    overview = [f"# {series.get('series', series_path.stem)}", "",
                f"来源：{source}。每集独立成片，第一句是 3–5 秒钩子，不自我介绍。", "",
                "| 集 | 标题 | 钩子 | 来源 | 字数 | 主讲 | 估计 |", "|---|---|---|---|---|---|---|", *table]
    (out / "series.md").write_text("\n".join(overview) + "\n", encoding="utf-8")
    return {"output": str(out), "episodes": rows}


def series_plans(folder, only=None):
    folder = Path(folder).resolve()
    plans = sorted(folder.glob("ep*/plan.json"))
    if only:
        wanted = {f"ep{int(n):02d}" for n in only}
        plans = [p for p in plans if p.parent.name in wanted]
    if not plans:
        raise FileNotFoundError(f"no epNN/plan.json under {folder}")
    return plans


def render_series(folder, config_path, only=None, backend=None):
    """Render every episode as a preview (30–60 s target) with one engine instance."""
    from .pipeline import load_config, render
    owns = backend is None
    if owns:
        from .engine import IndexBackend
        backend = IndexBackend(load_config(config_path))
    results = []
    try:
        for plan in series_plans(folder, only):
            data = render(plan, config_path, plan.parent / "out", "preview", backend=backend)
            results.append({"episode": plan.parent.name, "duration_seconds": round(data["duration_seconds"], 2),
                            "duration_ok": data["duration_ok"],
                            "lead_speech_fraction": round(data["lead_speech_fraction"], 3)})
    finally:
        if owns:
            backend.close()
    return {"episodes": results, "duration_ok": all(r["duration_ok"] for r in results),
            "listening_verified": False}


def compress_pauses(inputs, out, max_pause=.4, limit=15., gap=.2, rate=44100, threshold_db=-40, binary="ffmpeg"):
    """Join reference clips and shorten their internal pauses to at most max_pause seconds.

    IndexTTS imitates the reference's pausing; anime dialogue is often 25–60% silence, which caused
    dead air and dropped words. IndexTTS only reads the first 15 s, so clips stop at `limit`.
    """
    import numpy as np
    out = Path(out).resolve()
    hop = round(rate * .01)
    keep = round(max_pause * rate)
    pieces, report, used = [], [], 0.
    with tempfile.TemporaryDirectory() as directory:
        for i, source in enumerate(inputs):
            decoded = Path(directory) / f"{i}.wav"
            audio.ffmpeg(binary, ["-i", source, "-ac", "1", "-ar", rate, "-c:a", "pcm_s16le", decoded], timeout=600)
            samples = audio.read_pcm(decoded, rate)
            count = len(samples) // hop
            rms = np.sqrt(np.mean(samples[:count * hop].reshape(count, hop) ** 2, axis=1))
            loud = np.flatnonzero(rms >= 32768 * 10 ** (threshold_db / 20))
            if not len(loud):
                raise ValueError(f"reference clip is silent: {source}")
            clip = samples[loud[0] * hop:(loud[-1] + 1) * hop]
            before = audio.silent_runs(clip, rate, threshold_db, min_ms=round(max_pause * 1000))
            kept, cursor = [], 0
            for start, length in before:
                a, b = round(start * rate), round((start + length) * rate)
                kept += [clip[cursor:a + keep // 2]]
                cursor = b - keep // 2
            kept.append(clip[cursor:])
            clip = np.concatenate(kept)
            seconds = len(clip) / rate
            if pieces and used + gap + seconds > limit:
                report.append({"source": str(source), "skipped": "would pass the 15 s IndexTTS window"})
                continue
            if pieces:
                pieces.append(np.zeros(round(gap * rate)))
                used += gap
            pieces.append(clip)
            used += seconds
            report.append({"source": str(source), "seconds": round(seconds, 2),
                           "pauses_shortened": len(before)})
    joined = np.concatenate(pieces)
    audio.write_pcm(out, joined, rate)
    left = audio.silent_runs(joined, rate, threshold_db, min_ms=300)
    result = {"output": str(out), "seconds": round(len(joined) / rate, 2), "clips": report,
              "longest_pause": max((length for _, length in left), default=0.), "identity_verified": False}
    if result["seconds"] > limit:
        result["warning"] = f"longer than {limit:g} s; IndexTTS only conditions on the first {limit:g} s"
    return result


def _whisper(index_home, model_dir="checkpoints", name="large-v3"):
    import torch
    from faster_whisper import WhisperModel
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = "float16" if device == "cuda" else "int8"
    if Path(name).exists():
        return WhisperModel(str(name), device=device, compute_type=compute)
    # Only an already-cached model; never download during a production check.
    return WhisperModel(name, device=device, compute_type=compute,
                        download_root=str(Path(index_home) / model_dir / "hf_cache"), local_files_only=True)


def asr_check(output, index_home, model_dir="checkpoints", whisper="large-v3", lowest=10, model=None):
    """Transcribe every rendered turn and compare it with its script text.

    Low similarity is mostly numerals and homophones; read the lowest rows for real omissions or
    repeats. Lines whose 买/卖 counts differ are listening leads (Whisper merges parallel 买…卖).
    """
    output = Path(output).resolve()
    manifest = load_json(output / "manifest.json")
    model = model or _whisper(index_home, model_dir, whisper)
    norm = lambda s: re.sub(r"[^\w]", "", s)
    rows = []
    for turn in manifest["turns"]:
        clip = output / "work" / f"{turn['id']}.wav"
        segments, _ = model.transcribe(str(clip), language="zh", beam_size=5, initial_prompt="以下是普通话的句子。")
        segments = list(segments)
        heard = "".join(s.text for s in segments)
        gaps = [round(b.start - a.end, 2) for a, b in zip(segments, segments[1:])]
        rows.append({"id": turn["id"], "start": round(turn["start"], 2), "speaker": turn["speaker"],
                     "text": turn["text"], "asr": heard,
                     "similarity": round(difflib.SequenceMatcher(None, norm(turn["text"]), norm(heard)).ratio(), 3),
                     "max_gap": max(gaps or [0])})
    action = [r["id"] for r in rows
              if (r["text"].count("买"), r["text"].count("卖")) != (r["asr"].count("买"), r["asr"].count("卖"))]
    report = {"output": str(output), "turns": len(rows),
              "lowest": sorted(rows, key=lambda r: r["similarity"])[:lowest],
              "buy_sell_listen": [{"id": r["id"], "start": r["start"], "text": r["text"], "asr": r["asr"]}
                                  for r in rows if r["id"] in action],
              "note": "ASR mismatches are leads, not verdicts; numerals/homophones lower similarity.",
              "listening_verified": False}
    save_json(output / "asr.json", {**report, "rows": rows})
    return report


def source_map(series_dir, catalog_path, lines_path, out, pdf=None, dpi=150):
    """Line-by-line source map (Markdown + JSON, optional page renders and crops) for the video agent."""
    series_dir, out = Path(series_dir).resolve(), Path(out).resolve()
    catalog, mapping = load_json(catalog_path), load_json(lines_path)
    paper = dict(catalog.get("paper", {}))
    wp, ext, tags = catalog.get("white_paper", {}), catalog.get("external", {}), catalog.get("tags", {})
    out.mkdir(parents=True, exist_ok=True)
    crops = {}
    for sid, entry in wp.items():
        parts = [(entry["page"], r) for r in entry["rects"]] + [tuple(x) for x in entry.get("extra", [])]
        same_page = len({p for p, _ in parts}) == 1
        crops[sid] = [f"crops/{sid}.png"] if same_page else [f"crops/{sid}-{k}.png" for k in range(1, len(parts) + 1)]
    if pdf:
        _render_pdf(Path(pdf), wp, out, dpi)
        paper["file"] = Path(pdf).name
    episodes = []
    for key in sorted(mapping["episodes"], key=int):
        folder = series_dir / f"ep{int(key):02d}"
        plan, manifest = load_json(folder / "plan.json"), load_json(folder / "out" / "manifest.json")
        spec = mapping["episodes"][key]
        if not len(plan["lines"]) == len(manifest["turns"]) == len(spec["lines"]):
            raise ValueError(f"ep{int(key):02d}: plan, manifest and source lines differ in length; "
                             "update the source lines after any script change")
        lines = []
        for line, turn, (ids, note) in zip(plan["lines"], manifest["turns"], spec["lines"]):
            if line["text"] != turn["text"]:
                raise ValueError(f"{folder.name}/{turn['id']}: manifest text differs from plan; re-render first")
            unknown = [s for s in ids if s not in wp and s not in ext and s not in tags]
            if unknown:
                raise ValueError(f"{folder.name}/{turn['id']}: unknown source ids {unknown}")
            lines.append({"id": turn["id"], "start": round(turn["start"], 2), "end": round(turn["end"], 2),
                          "speaker": line["speaker"], "text": line["text"], "sources": ids, "note": note})
        used = sorted({s for r in lines for s in r["sources"]}, key=lambda s: (s not in wp, s))
        episodes.append({"episode": folder.name, "title": plan["title"].split("｜")[-1],
                         "audio": f"{folder.name}/out/episode.mp3", "subtitles": f"{folder.name}/out/subtitles.srt",
                         "manifest": f"{folder.name}/out/manifest.json", "duration": round(manifest["turns"][-1]["end"], 2),
                         "visual_suggestion": spec.get("visual", []), "sources_used": used, "lines": lines})
    data = {"paper": paper,
            "white_paper_sources": {k: {**{x: v[x] for x in ("page", "section", "quote", "zh")}, "rects": v["rects"],
                                        "extra": v.get("extra", []), "crops": crops[k]} for k, v in wp.items()},
            "external_sources": ext, "non_paper_tags": tags, "episodes": episodes}
    save_json(out / "source-map.json", data)
    (out / "source-map.md").write_text(_source_markdown(data, catalog.get("notes", [])), encoding="utf-8")
    counted = {"white_paper": 0, "external": 0, "ours": 0}
    for episode in episodes:
        for row in episode["lines"]:
            kind = ("white_paper" if any(s in wp for s in row["sources"])
                    else "external" if any(s in ext for s in row["sources"]) else "ours")
            counted[kind] += 1
    return {"output": str(out), "episodes": len(episodes), "lines_by_primary_source": counted,
            "images": bool(pdf)}


def _render_pdf(pdf, wp, out, dpi):
    try:
        import fitz
    except ImportError as error:
        raise ImportError("page renders and crops need PyMuPDF (pip install pymupdf); omit --pdf to skip") from error
    doc = fitz.open(pdf)
    (out / "pages").mkdir(exist_ok=True)
    (out / "crops").mkdir(exist_ok=True)
    for i, page in enumerate(doc, 1):
        page.get_pixmap(dpi=dpi).save(out / "pages" / f"p{i:02d}.png")
    zoom = fitz.Matrix(dpi / 72, dpi / 72)
    for sid, entry in wp.items():
        parts = [(entry["page"], r) for r in entry["rects"]] + [tuple(x) for x in entry.get("extra", [])]
        if len({p for p, _ in parts}) == 1:
            rect = fitz.Rect(parts[0][1])
            for _, r in parts[1:]:
                rect |= fitz.Rect(r)
            page = doc[parts[0][0] - 1]
            page.get_pixmap(matrix=zoom, clip=(rect + (-8, -8, 8, 8)) & page.rect).save(out / "crops" / f"{sid}.png")
        else:
            for k, (p, r) in enumerate(parts, 1):
                page = doc[p - 1]
                page.get_pixmap(matrix=zoom, clip=(fitz.Rect(r) + (-8, -8, 8, 8)) & page.rect).save(
                    out / "crops" / f"{sid}-{k}.png")


def _source_markdown(d, notes):
    paper = d["paper"]
    o = ["# 逐句来源对照（给 short / 视频制作 Agent）", "",
         "## 怎么用", "",
         "- 每集每句都标了来源 ID。`WP-…` = 主资料原文的某一段或某张图（下方目录有页码、PDF 坐标、原文开头和截图路径）；"
         "`EXT-…` = 主资料以外的论文（只有文字依据，没有可截的图）；`OURS-…` = 我们自己的比喻、解读、常识定义或串场，"
         "不对应论文任何部分，画面不要标成“论文原文”。",
         "- 时间码来自各集 `out/manifest.json`，单位秒，是该句在 `episode.mp3` 里的起止。字幕在 `out/subtitles.srt`。",
         "- 截图：`crops/<ID>.png` 是对应段落或图表的裁切；`pages/pNN.png` 是整页。",
         f"- 主资料：{paper.get('title', '')}（{paper.get('dates', '')}，{paper.get('pages', '')} 页，文件 `{paper.get('file', '')}`）。"
         f"坐标系：{paper.get('coordinates', '')}。",
         *[f"- {n}" for n in notes], "",
         "## 主资料来源目录（WP）", "",
         "| ID | 页 | 位置 | 原文开头（便于在 PDF 里找） | 内容（中文） | 截图 |", "|---|---|---|---|---|---|"]
    for k, v in d["white_paper_sources"].items():
        o.append(f"| `{k}` | {v['page']} | {v['section']} | {v['quote']} | {v['zh']} | "
                 f"{'<br>'.join(f'`{c}`' for c in v['crops'])} |")
    o += ["", "## 外部研究目录（EXT）", "", "| ID | 书目 | 依据与定位 | 用于 |", "|---|---|---|---|"]
    for k, v in d["external_sources"].items():
        o.append(f"| `{k}` | {v['cite']} | {v['where']} | {v['zh']} |")
    o += ["", "## 非论文标签（OURS）", ""] + [f"- `{k}`：{v}" for k, v in d["non_paper_tags"].items()]
    o += ["", "## 各集逐句对照", ""]
    wp = d["white_paper_sources"]
    for e in d["episodes"]:
        pages = sorted({wp[s]["page"] for s in e["sources_used"] if s in wp})
        o += [f"### {e['episode']}｜{e['title']}（{e['duration']} 秒）", "",
              f"- 音频 `{e['audio']}`；字幕 `{e['subtitles']}`；时间码 `{e['manifest']}`",
              f"- 涉及主资料页：{'、'.join(f'第{p}页' for p in pages) or '无（本集主要依据外部研究或我们的总结）'}",
              f"- 外部研究：{'、'.join(f'`{s}`' for s in e['sources_used'] if s.startswith('EXT-')) or '无'}",
              f"- 建议主画面：{'、'.join(f'`{s}`' for s in e['visual_suggestion']) or '无'}", "",
              "| # | 时间 | 说话人 | 台词 | 来源 | 说明 |", "|---|---|---|---|---|---|"]
        for r in e["lines"]:
            src = "<br>".join(f"`{s}`" + (f"（第{wp[s]['page']}页）" if s in wp else "") for s in r["sources"])
            o.append(f"| {r['id']} | {r['start']:.1f}–{r['end']:.1f} | {r['speaker']} | {r['text']} | {src} | {r['note']} |")
        o.append("")
    return "\n".join(o) + "\n"
