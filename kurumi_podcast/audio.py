from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path


def ffmpeg(binary, args, timeout=60):
    executable = shutil.which(str(binary)) or str(binary)
    result = subprocess.run([executable, "-y", "-hide_banner", "-loglevel", "error", *map(str, args)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])


def read_pcm(path, rate):
    import numpy as np
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != rate:
            raise ValueError(f"expected mono PCM16/{rate}Hz: {path}")
        return np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float64)


def write_pcm(path, samples, rate):
    import numpy as np
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(np.clip(np.rint(samples), -32768, 32767).astype("<i2").tobytes())


def duration(path):
    with wave.open(str(path), "rb") as wav:
        if not wav.getnframes():
            raise ValueError("audio is empty")
        return wav.getnframes() / wav.getframerate()


def normalize_source(source, target, rate, binary="ffmpeg"):
    ffmpeg(binary, ["-i", source, "-ac", "1", "-ar", rate, "-c:a", "pcm_s16le", target])


def trim_edges(samples, rate):
    import numpy as np
    hop = max(1, round(rate * .01))
    count = len(samples) // hop
    if not count:
        raise ValueError("empty audio")
    rms = np.sqrt(np.mean(samples[:count * hop].reshape(count, hop) ** 2, axis=1))
    active = np.flatnonzero(rms > 32768 * 10 ** (-42 / 20))
    if not len(active):
        raise ValueError("no audible speech")
    start = max(0, int(active[0]) * hop - round(rate * .05))
    end = min(len(samples), (int(active[-1]) + 1) * hop + round(rate * .065))
    trimmed = samples[start:end].copy()
    fade = min(round(rate * .006), len(trimmed) // 2)
    if fade:
        trimmed[:fade] *= np.linspace(0, 1, fade)
        trimmed[-fade:] *= np.linspace(1, 0, fade)
    return trimmed


def mix_turns(lines, clips, rate):
    import numpy as np
    if len(lines) != len(clips) or not lines:
        raise ValueError("each dialogue turn needs exactly one audio clip")
    rows, cursor = [], 0
    for i, (line, clip) in enumerate(zip(lines, clips)):
        if len(clip) / rate <= 0:
            raise ValueError("empty turn")
        rows.append({**line, "start": cursor / rate, "end": (cursor + len(clip)) / rate,
                     "duration": len(clip) / rate})
        chapter_end = i == len(lines) - 1 or lines[i + 1]["chapter"] != line["chapter"]
        gap = line.get("after_ms", 750 if chapter_end else 140) / 1000
        if i == len(lines) - 1:
            gap = max(0, gap)
        if cursor + len(clip) + round(gap * rate) < 0:
            raise ValueError("overlap extends before the episode")
        cursor += len(clip) + round(gap * rate)
    mixed = np.zeros(cursor)
    for row, clip in zip(rows, clips):
        start = round(row["start"] * rate)
        mixed[start:start + len(clip)] += clip * .82
    return mixed, rows


def join_mastered(prefix, body, cut, rate):
    import numpy as np
    if cut < 0 or round(cut * rate) > len(body):
        raise ValueError("cut outside the mastered audio")
    return np.concatenate([prefix, body[round(cut * rate):]])


def export_mp3(wav, target, manifest, binary="ffmpeg"):
    def escape(value):
        return str(value).replace("\\", "\\\\").replace("\n", " ").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#")
    metadata = [";FFMETADATA1", "title=" + escape(manifest["title"]),
                "artist=AI角色闲聊", "comment=AI-generated; source identity recorded in manifest"]
    for chapter in manifest["chapters"]:
        metadata += ["[CHAPTER]", "TIMEBASE=1/1000",
                     f"START={round(chapter['start'] * 1000)}",
                     f"END={round(chapter['end'] * 1000)}", "title=" + escape(chapter["title"])]
    path = Path(target).parent / "work" / "chapters.ffmetadata"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(metadata) + "\n", encoding="utf-8")
    ffmpeg(binary, ["-i", wav, "-i", path, "-map_metadata", "1", "-c:a", "libmp3lame",
                   "-b:a", "160k", target])
