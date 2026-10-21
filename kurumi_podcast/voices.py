"""Local anime voice-reference preparation: vocal separation, speaker search, review and confirmation.

Broadcast material stays on this machine; nothing here uploads or publishes audio or video.
Speaker search only ranks candidates for a person to confirm; it never certifies identity.
"""
from __future__ import annotations

import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import audio
from .core import load_json, save_json

HOP = .1  # seconds per fingerprint frame
FONTS = (r"C:\Windows\Fonts\YuGothM.ttc", r"C:\Windows\Fonts\msgothic.ttc",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
         "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc")


# ---------------------------------------------------------------- separation

def separate_vocals(inputs, out, separator="audio-separator", model="vocals_mel_band_roformer.ckpt",
                    model_dir=None, binary="ffmpeg"):
    """Extract each input's audio and keep only the vocal stem via an installed audio-separator."""
    out = Path(out)
    (out / "input").mkdir(parents=True, exist_ok=True)
    (out / "vocals").mkdir(parents=True, exist_ok=True)
    wavs = []
    for source in map(Path, inputs):
        wav = out / "input" / f"{source.stem}.wav"
        audio.ffmpeg(binary, ["-i", source, "-vn", "-ac", 2, "-ar", 44100, wav], timeout=1800)
        wavs.append(wav)
    command = [separator] if isinstance(separator, str) else list(separator)
    command += [str(w) for w in wavs] + ["-m", model, "--output_dir", str(out / "vocals"),
                                          "--output_format", "WAV", "--single_stem", "Vocals", "--use_autocast"]
    if model_dir:
        command += ["--model_file_dir", str(model_dir)]
    subprocess.run(command, check=True)
    rows = []
    for wav in wavs:
        produced = [p for p in (out / "vocals").glob(f"{glob_escape(wav.stem)}_*") if "(vocals)" in p.name.lower()]
        if not produced:
            raise RuntimeError(f"audio-separator wrote no vocal stem for {wav.name}")
        vocals = out / "vocals" / wav.name
        produced[0].replace(vocals)
        rows.append({"input": str(wav), "vocals": str(vocals), "removed_db": removed_db(wav, vocals, binary)})
    save_json(out / "separation.json", {"model": model, "files": rows})
    return rows


def glob_escape(text):
    return re.sub(r"([\[\]*?])", r"[\1]", text)


def removed_db(mix, vocals, binary="ffmpeg"):
    """Energy taken out (non-vocal residual) relative to the mix; very negative = already clean."""
    import numpy as np
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        pair = []
        for name, path in (("mix", mix), ("vocals", vocals)):
            target = Path(directory) / f"{name}.wav"
            audio.ffmpeg(binary, ["-i", path, "-ac", 1, "-ar", 24000, "-c:a", "pcm_s16le", target], timeout=1800)
            pair.append(audio.read_pcm(target, 24000))
    n = min(map(len, pair))
    residual, mix_pcm = pair[0][:n] - pair[1][:n], pair[0][:n]
    power = lambda x: 10 * np.log10(np.mean(x ** 2) + 1e-9)  # noqa: E731
    return round(float(power(residual) - power(mix_pcm)), 1)


# ------------------------------------------------------------ speaker search

def unit(vectors):
    import numpy as np
    mean = np.mean(np.asarray(vectors), axis=0)
    return mean / np.linalg.norm(mean)


def score_segments(segments, positive, groups, high=(.6, .15), medium=(.5, .05), mixed_below=.5):
    """Score against the target and the *closest* other character, refining the target once.

    Close voices (e.g. two actresses CAM++ hears as similar) need their own negative group;
    calibrate margins from confirmed reviews rather than trusting the defaults.
    """
    import numpy as np
    pos = np.asarray(positive)
    others = {name: unit(vectors) for name, vectors in groups.items()}

    def rate(s, target):
        nearest, value = max(((c, float(s["embedding"] @ v)) for c, v in others.items()), key=lambda x: x[1])
        s["score"] = round(float(s["embedding"] @ target), 3)
        s["margin"] = round(s["score"] - value, 3)
        s["nearest_other"] = nearest

    target = unit(pos)
    for _ in range(2):
        for s in segments:
            rate(s, target)
        seeds = [s["embedding"] for s in segments
                 if s["score"] >= high[0] and s["margin"] >= high[1] and s.get("halves", 1) >= mixed_below]
        if len(seeds) >= 5:
            target = unit(np.vstack([pos, seeds]))
    for s in segments:
        rate(s, target)
        s["mixed"] = s.get("halves", 1) < mixed_below
        s["tier"] = ("high" if s["score"] >= high[0] and s["margin"] >= high[1] and not s["mixed"] else
                     "medium" if s["score"] >= medium[0] and s["margin"] >= medium[1] else "other")
    return target


def shared_intervals(a, b, min_seconds=15., similar=.75, votes=100, window=31, pad=2.):
    """Stretches of identical audio in two episodes (OP/ED, eyecatch, previews).

    Vote for offsets where many frames' best match agrees, then score every frame at that
    fixed offset and keep long smoothed runs; single best matches are too noisy.
    """
    import numpy as np
    import torch
    where = torch.cat([(chunk @ b.T).argmax(dim=1) for chunk in torch.split(a, 2000)]).cpu().numpy()
    lags, counts = np.unique(where - np.arange(len(where)), return_counts=True)
    found_a, found_b = [], []
    for lag in lags[counts >= votes]:
        i = np.arange(max(0, -lag), min(len(a), len(b) - lag))
        if not len(i):
            continue
        sims = (a[i] * b[i + lag]).sum(dim=1).cpu().numpy()
        smooth = np.convolve(sims >= similar, np.ones(window) / window, mode="same") >= .5
        start = None
        for k, ok in enumerate(np.append(smooth, False)):
            if ok and start is None:
                start = k
            elif not ok and start is not None:
                if (k - start) * HOP >= min_seconds:
                    # Pad: smoothing trims the first/last notes of a song.
                    s, e = float(i[start] * HOP) - pad, float((i[k - 1] + 1) * HOP) + pad
                    found_a.append((s, e))
                    found_b.append((s + float(lag * HOP), e + float(lag * HOP)))
                start = None
    return found_a, found_b


def overlaps(start, end, intervals):
    return any(start < e and end > s for s, e in intervals)


class SpeakerTools:
    """CAM++ (the speaker embedding IndexTTS conditions on), fingerprints and local Whisper."""

    def __init__(self, index_home, model_dir="checkpoints"):
        import torch
        self.home = Path(index_home)
        self.models = self.home / model_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        sys.path.insert(0, str(self.home))
        from indextts.s2mel.modules.campplus.DTDNN import CAMPPlus
        self.campplus = CAMPPlus(feat_dim=80, embedding_size=192)
        weights = self.models / "hf_cache" / "campplus_cn_common.bin"
        if not weights.is_file():
            raise FileNotFoundError(f"CAM++ weights not found: {weights}")
        self.campplus.load_state_dict(torch.load(weights, map_location="cpu"))
        self.campplus.eval().to(self.device)

    @staticmethod
    def load(path, start=None, end=None, rate=16000):
        import soundfile as sf
        import torch
        import torchaudio
        samples, sr = sf.read(str(path), dtype="float32", always_2d=True)
        samples = samples.mean(axis=1)
        if start is not None:
            samples = samples[max(0, int(start * sr)):int(end * sr)]
        return torchaudio.functional.resample(torch.from_numpy(samples), sr, rate), samples, sr

    def embed(self, wav16):
        import numpy as np
        import torch
        import torchaudio
        with torch.no_grad():
            feat = torchaudio.compliance.kaldi.fbank(wav16.unsqueeze(0), num_mel_bins=80, dither=0,
                                                     sample_frequency=16000)
            feat = feat - feat.mean(dim=0, keepdim=True)
            emb = self.campplus(feat.unsqueeze(0).to(self.device))[0].float().cpu().numpy()
        return emb / np.linalg.norm(emb)

    def fingerprint(self, path):
        import torch
        import torchaudio
        wav, _, _ = self.load(path)
        with torch.no_grad():
            mel = torchaudio.transforms.MelSpectrogram(16000, n_fft=2048, hop_length=int(16000 * HOP),
                                                       n_mels=48)(wav)
            feat = torch.log(mel + 1e-6).T
            feat = feat - feat.mean(dim=1, keepdim=True)
        return torch.nn.functional.normalize(feat, dim=1).to(self.device)

    def whisper(self, name="large-v3"):
        from faster_whisper import WhisperModel
        compute = "float16" if self.device == "cuda" else "int8"
        if Path(name).exists():
            return WhisperModel(str(name), device=self.device, compute_type=compute)
        # Only the already-cached model; never download inside a production run.
        return WhisperModel(name, device=self.device, compute_type=compute,
                            download_root=str(self.models / "hf_cache"), local_files_only=True)


def parse_negatives(items):
    groups = {}
    for item in items:
        name, path = item.split("=", 1) if "=" in item and not Path(item).exists() else ("other", item)
        groups.setdefault(name, []).append(path)
    return groups


def find_speaker(target, positive, negative, episodes, out, index_home, model_dir="checkpoints",
                 whisper="large-v3", high=(.6, .15), medium=(.5, .05)):
    """Rank one character's lines in separated episode vocals; songs shared by episodes are skipped.

    episodes: [(name, vocals_wav, mix_wav)] - the mix is used only to find shared OP/ED audio.
    """
    import soundfile as sf
    import torch
    tools = SpeakerTools(index_home, model_dir)
    out = Path(out)
    pos = {Path(p).name: tools.embed(tools.load(p)[0]) for p in positive}
    groups = {name: {Path(p).name: tools.embed(tools.load(p)[0]) for p in paths}
              for name, paths in parse_negatives(negative).items()}
    centroid = {name: unit(list(v.values())) for name, v in groups.items()}
    vectors = list(pos.values())
    report = {"target": target,
              "anchors": {"positive": {n: round(float(v @ unit(vectors)), 3) for n, v in pos.items()},
                          **{g: {n: round(float(v @ unit(vectors)), 3) for n, v in items.items()}
                             for g, items in groups.items()}},
              "anchor_nearest_other": {n: max(centroid, key=lambda g: float(v @ centroid[g]))
                                       for n, v in pos.items()}}

    prints = {name: tools.fingerprint(mix) for name, _, mix in episodes}
    excluded = {name: [] for name, _, _ in episodes}
    for i, (a, _, _) in enumerate(episodes):
        for b, _, _ in episodes[i + 1:]:
            ia, ib = shared_intervals(prints[a], prints[b])
            excluded[a] += ia
            excluded[b] += ib
    report["excluded_shared_audio"] = {k: [[round(s, 1), round(e, 1)] for s, e in v] for k, v in excluded.items()}
    del prints
    if tools.device == "cuda":
        torch.cuda.empty_cache()

    asr = tools.whisper(whisper)
    segments = []
    for name, vocals, _ in episodes:
        result, _ = asr.transcribe(str(vocals), language="ja", vad_filter=True, beam_size=5,
                                   condition_on_previous_text=False)
        for seg in result:
            start, end = max(0., seg.start - .05), seg.end + .05
            if not .8 <= end - start <= 20 or overlaps(start, end, excluded[name]):
                continue
            wav, _, _ = tools.load(vocals, start, end)
            half = len(wav) // 2
            # Whisper may merge a quick exchange; disagreeing halves mark a mixed segment.
            halves = float(tools.embed(wav[:half]) @ tools.embed(wav[half:])) if end - start >= 2.4 else 1.
            segments.append({"episode": name, "start": round(start, 3), "end": round(end, 3),
                             "text": seg.text.strip(), "embedding": tools.embed(wav), "halves": round(halves, 3)})
    del asr

    score_segments(segments, vectors, {g: list(v.values()) for g, v in groups.items()}, high, medium)
    vocals_of = {name: vocals for name, vocals, _ in episodes}
    rows, lists = [], {"high": [], "medium": []}
    for s in sorted(segments, key=lambda s: -s["score"]):
        row = {k: v for k, v in s.items() if k != "embedding"}
        if s["tier"] in lists:
            _, samples, sr = tools.load(vocals_of[s["episode"]], s["start"], s["end"])
            path = out / s["tier"] / f"{s['episode']}_{s['start']:07.2f}-{s['end']:07.2f}_s{s['score']:.2f}.wav"
            path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(path), samples, sr, subtype="PCM_16")
            row["file"] = str(path)
            lists[s["tier"]].append(f"{path}\t{s['text']}")
        rows.append(row)
    for tier, lines in lists.items():
        (out / f"{tier}.lst").write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    report["counts"] = {t: sum(r["tier"] == t for r in rows) for t in ("high", "medium", "other")}
    report["seconds"] = {t: round(sum(r["end"] - r["start"] for r in rows if r["tier"] == t), 1)
                         for t in ("high", "medium")}
    report["thresholds"] = {"high": list(high), "medium": list(medium)}
    report["listening_verified"] = False
    save_json(out / "candidates.json", {"report": report, "segments": rows})
    return report


# ------------------------------------------------------------ review videos

def stamp(seconds):
    return f"{int(seconds // 60):02d}:{seconds % 60:04.1f}"


def wrap(text, width=32):
    return "\n".join(text[i:i + width] for i in range(0, len(text), width)) or " "


def find_font(font=None):
    for path in ([font] if font else FONTS):
        if path and Path(path).is_file():
            return Path(path)
    raise FileNotFoundError("no CJK font found; pass --font with a .ttc/.otf that covers Japanese")


def review_video(candidates, videos, out, tier="high", top=None, pad=.3, font=None, binary="ffmpeg"):
    """Cut candidates from the original episodes into one labelled video plus a time index."""
    segments = [s for s in load_json(candidates)["segments"] if s["tier"] == tier]
    if top:
        segments = sorted([s for s in segments if 2.5 <= s["end"] - s["start"] <= 10],
                          key=lambda s: -s["score"])[:top]
    else:
        segments.sort(key=lambda s: (s["episode"], s["start"]))
    if not segments:
        raise ValueError(f"no {tier} candidates to review")
    out = Path(out).resolve()
    work = out.with_suffix("")
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy(find_font(font), work / "font.ttc")  # Relative paths avoid drawtext's drive-colon escaping.
    executable = shutil.which(str(binary)) or str(binary)
    index, cursor = [], 0.
    for number, s in enumerate(segments, 1):
        n = f"{number:03d}"
        (work / f"{n}_label.txt").write_text(
            f"#{number:02d}  {s['episode']}  {stamp(s['start'])}–{stamp(s['end'])}"
            f"  score {s['score']:.2f}  margin {s['margin']:.2f}", encoding="utf-8")
        (work / f"{n}_text.txt").write_text(wrap(s["text"]), encoding="utf-8")
        draw = (f"drawtext=fontfile=font.ttc:textfile={n}_label.txt:expansion=none:x=24:y=20:fontsize=30:"
                "fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=8,"
                f"drawtext=fontfile=font.ttc:textfile={n}_text.txt:expansion=none:x=(w-tw)/2:y=h-110-th:"
                "fontsize=34:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=10")
        start = max(0., s["start"] - pad)
        subprocess.run([executable, "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(videos[s["episode"]]),
                        "-t", f"{s['end'] + pad - start:.3f}", "-vf", draw, "-r", "24000/1001",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "160k",
                        "-ar", "48000", "-ac", "2", f"{n}.mp4"], cwd=work, check=True)
        length = audio.duration_any(work / f"{n}.mp4", binary)
        index.append({"no": number, "episode": s["episode"], "start": s["start"], "end": s["end"],
                      "score": s["score"], "margin": s["margin"], "text": s["text"], "file": s.get("file"),
                      "video_start": round(cursor, 2), "video_end": round(cursor + length, 2)})
        cursor += length
    (work / "list.txt").write_text("".join(f"file '{i['no']:03d}.mp4'\n" for i in index), encoding="utf-8")
    subprocess.run([executable, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt",
                    "-c", "copy", str(out)], cwd=work, check=True)
    save_json(out.with_suffix(".json"), index)
    return index


# -------------------------------------------------------------- confirmation

def video_time(text):
    minutes, _, seconds = text.strip().rpartition(":")
    return int(minutes or 0) * 60 + float(seconds)


def select_entries(index, picks):
    """Pick entries by number (7, 92-94) or review-video time (0:51-0:54, 7:37-)."""
    chosen = set()
    for pick in picks:
        for token in filter(None, re.split(r"[,\s]+", pick)):
            low, sep, high = token.replace("~", "-").partition("-")
            if ":" in token:
                a = video_time(low) if low else 0.
                b = (video_time(high) if high else float("inf")) if sep else a
                if a == b:
                    chosen |= {e["no"] for e in index if e["video_start"] <= a < e["video_end"]}
                else:  # Ignore clips that only touch the range by a few frames.
                    chosen |= {e["no"] for e in index
                               if min(e["video_end"], b) - max(e["video_start"], a) > .2}
            else:
                last = int(high) if high else (max(e["no"] for e in index) if sep else int(low))
                chosen |= set(range(int(low), last + 1))
    unknown = chosen - {e["no"] for e in index}
    if unknown:
        raise ValueError(f"review index has no entries {sorted(unknown)}")
    return chosen


def confirm_review(index_path, confirmed, reject=(), reject_as=None, anchors=None):
    """Accepted clips join the confirmed set; rejected ones become another character's anchors."""
    index = load_json(index_path)
    rejected = select_entries(index, reject)
    if rejected and not (reject_as and anchors):
        raise ValueError("rejected clips need --reject-as CHARACTER and --anchors DIR")
    today = datetime.date.today().isoformat()
    confirmed = Path(confirmed)
    confirmed.mkdir(parents=True, exist_ok=True)
    listing = confirmed / f"{confirmed.name}.lst"
    lines = listing.read_text(encoding="utf-8").splitlines() if listing.is_file() else []
    moved = {"confirmed": [], "rejected": []}
    for entry in index:
        if not entry.get("file") or not Path(entry["file"]).is_file():
            raise FileNotFoundError(f"#{entry['no']}: candidate clip is missing: {entry.get('file')}")
        source = Path(entry["file"])
        if entry["no"] in rejected:
            target = Path(anchors) / reject_as / source.name
            moved["rejected"].append(entry["no"])
        else:
            target = confirmed / source.name
            line = f"{target}\t{entry['text']}"
            if line not in lines:
                lines.append(line)
            moved["confirmed"].append(entry["no"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, target)
    listing.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    note = f"{today} {Path(index_path).name}: "
    with (confirmed / "README.txt").open("a", encoding="utf-8") as stream:
        stream.write(note + f"user confirmed #{moved['confirmed']} as {confirmed.name}.\n")
    if rejected:
        with (Path(anchors) / reject_as / "README.txt").open("a", encoding="utf-8") as stream:
            stream.write(note + f"user identified #{sorted(rejected)} as {reject_as}.\n")
    return {**moved, "confirmed_total": len(lines), "listing": str(listing)}
