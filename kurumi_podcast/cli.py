from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from .core import language_warnings, load_json, resolve_path, validate_plan
from .pipeline import (extract_source, load_config, package_chapters, patch_opening, qa_report,
                       render, resolve_voice)
from .recipe import bind_original, validate_runtime


def caller_path(value):
    base = os.environ.get("KURUMI_CALLER_CWD") or os.getcwd()
    return resolve_path(value, base)


def parser():
    root = argparse.ArgumentParser(description="Preview-first Kurumi-led research dialogue.")
    subs = root.add_subparsers(dest="command", required=True)
    bind = subs.add_parser("bind-original", help="verify eight frozen reference slots and lock a new local environment")
    bind.add_argument("--assets", required=True)
    bind.add_argument("--index-home", required=True)
    bind.add_argument("--out", default="config.local.json")
    extract = subs.add_parser("extract", help="extract PDF/TXT/Markdown with source page anchors")
    extract.add_argument("source")
    extract.add_argument("--out", required=True)
    validate = subs.add_parser("validate", help="check dialogue structure and lead allocation")
    validate.add_argument("plan")
    validate.add_argument("--stage", choices=["preview", "full", "opening"], default="preview")
    doctor = subs.add_parser("doctor", help="inspect local configuration without loading weights")
    doctor.add_argument("--config", required=True)
    doctor.add_argument("--plan")
    doctor.add_argument("--import-engine", action="store_true")
    produce = subs.add_parser("render", help="render a short preview or explicitly confirmed episode")
    produce.add_argument("plan")
    produce.add_argument("--config", required=True)
    produce.add_argument("--out", required=True)
    produce.add_argument("--stage", choices=["preview", "full"], default="preview")
    produce.add_argument("--approved-preview", action="store_true")
    patch = subs.add_parser("patch-opening", help="prepend/replace only the opening and shift timing")
    patch.add_argument("plan")
    patch.add_argument("--base", required=True)
    patch.add_argument("--config", required=True)
    patch.add_argument("--out", required=True)
    patch.add_argument("--replace-until", type=float, default=0)
    qa = subs.add_parser("qa", help="measurable checks on a rendered output (not a listening verdict)")
    qa.add_argument("output")
    chapters = subs.add_parser("package-chapters", help="cut per-chapter MP3s from a rendered episode")
    chapters.add_argument("output")
    chapters.add_argument("--ffmpeg", default="ffmpeg")
    separate = subs.add_parser("separate-vocals", help="strip BGM from local clips/episodes via audio-separator")
    separate.add_argument("inputs", nargs="+")
    separate.add_argument("--out", required=True)
    separate.add_argument("--separator", default="audio-separator", help="audio-separator executable")
    separate.add_argument("--model", default="vocals_mel_band_roformer.ckpt")
    separate.add_argument("--model-dir")
    find = subs.add_parser("find-speaker", help="rank one character's lines in separated episode vocals")
    find.add_argument("--target", required=True)
    find.add_argument("--positive", nargs="+", required=True, help="confirmed clips of the target")
    find.add_argument("--negative", nargs="+", required=True, help="CHARACTER=clip for each other voice")
    find.add_argument("--episode", nargs="+", required=True, help="NAME=VOCALS.wav=MIX.wav")
    find.add_argument("--out", required=True)
    find.add_argument("--config", help="bound config whose IndexTTS home provides CAM++ and Whisper")
    find.add_argument("--index-home")
    find.add_argument("--whisper", default="large-v3")
    find.add_argument("--high", type=float, nargs=2, default=(.6, .15), metavar=("SCORE", "MARGIN"))
    find.add_argument("--medium", type=float, nargs=2, default=(.5, .05), metavar=("SCORE", "MARGIN"))
    review = subs.add_parser("review-video", help="cut candidates into one labelled video for a person to check")
    review.add_argument("candidates")
    review.add_argument("--episode", nargs="+", required=True, help="NAME=VIDEO.mp4")
    review.add_argument("--out", required=True)
    review.add_argument("--tier", default="high")
    review.add_argument("--top", type=int)
    review.add_argument("--font")
    confirm = subs.add_parser("confirm-review", help="record a person's verdict on a review video")
    confirm.add_argument("index", help="the review video's .json index")
    confirm.add_argument("--confirmed", required=True, help="folder of confirmed clips for the target")
    confirm.add_argument("--reject", nargs="*", default=[], help="numbers (92-94) or video times (7:37-)")
    confirm.add_argument("--reject-as", help="who the rejected clips actually are")
    confirm.add_argument("--anchors", help="folder holding other characters' anchor clips")
    return root


def engine_home(args):
    from .engine import index_home
    if args.config:
        config = load_config(caller_path(args.config))
    elif args.index_home:
        config = {"index_home": str(caller_path(args.index_home)), "_base": os.getcwd()}
    else:
        raise ValueError("find-speaker needs --config or --index-home for CAM++ and Whisper")
    return index_home(config), config.get("model_dir", "checkpoints")


def pairs(items, parts):
    split = [item.split("=", parts - 1) for item in items]
    if any(len(p) != parts for p in split):
        raise ValueError(f"expected {'='.join(['NAME'] + ['PATH'] * (parts - 1))}: {items}")
    return [[p[0]] + [str(caller_path(x)) for x in p[1:]] for p in split]


def doctor(config_path, plan_path=None, import_native=False):
    from .engine import import_engine, index_home
    config = load_config(config_path)
    report = {"ready": True, "missing": [], "voices": {}}
    plan = validate_plan(load_json(plan_path), "opening") if plan_path else None
    try:
        report["runtime"] = validate_runtime(config, plan)
    except (ValueError, FileNotFoundError) as error:
        report["ready"] = False
        report["missing"].append(str(error))
        return report  # Never import the native engine on a failed restoration lock.
    try:
        home = index_home(config)
        report["index_home"] = str(home)
    except ValueError as error:
        home = None
        report["missing"].append(str(error))
    binary = config.get("ffmpeg", "ffmpeg")
    if not (shutil.which(binary) or Path(binary).is_file()):
        report["missing"].append("ffmpeg executable")
    pairs = sorted({(r["speaker"], r["delivery"]) for r in plan["lines"]}) if plan else sorted({
        (name, delivery) for name, profile in config.get("voices", {}).items()
        for delivery in ({"explain"} | set(profile.get("emotion_audio", {})))})
    for name, delivery in pairs:
        try:
            voice, emotion, profile = resolve_voice(config, name, delivery)
            report["voices"].setdefault(name, {})[delivery] = {
                "reference_audio": str(voice), "emotion_audio": str(emotion) if emotion else None,
                "identity_label": profile.get("identity_label", name)}
        except (ValueError, FileNotFoundError) as error:
            report["missing"].append(str(error))
    if import_native and home and not report["missing"]:
        cls = import_engine(home)
        report["engine_class"] = cls.__name__
        report["engine_method"] = "infer" if callable(getattr(cls, "infer", None)) else "missing"
        if report["engine_method"] == "missing":
            report["missing"].append("native infer method")
    report["ready"] = not report["missing"]
    return report


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "bind-original":
            data = bind_original(caller_path(args.assets), caller_path(args.index_home), caller_path(args.out))
            result = {"output": str(caller_path(args.out)), "recipe": data["recipe"],
                      "binding_kind": "new-current-environment", "listening_verified": False,
                      "historical_native_verified": False, "historical_bits_verified": False}
        elif args.command == "extract":
            data = extract_source(caller_path(args.source), caller_path(args.out))
            result = {"output": str(caller_path(args.out)), "pages": data["page_count"],
                      "empty_text_pages": data["empty_text_pages"]}
        elif args.command == "validate":
            data = validate_plan(load_json(caller_path(args.plan)), args.stage)
            result = {"valid": True, "lead": data["lead"],
                      "lead_text_fraction": data["lead_text_fraction"],
                      "speakers": data["speaker_characters"], "turns": len(data["lines"]),
                      "warnings": language_warnings(data)}
        elif args.command == "doctor":
            result = doctor(caller_path(args.config),
                            caller_path(args.plan) if args.plan else None, args.import_engine)
        elif args.command == "render":
            data = render(caller_path(args.plan), caller_path(args.config), caller_path(args.out),
                          args.stage, args.approved_preview)
            result = {"output": str(caller_path(args.out)), "duration_seconds": data["duration_seconds"],
                      "lead_speech_fraction": data["lead_speech_fraction"], "stage": data["stage"],
                      "duration_ok": data["duration_ok"]}
            if not data["duration_ok"]:
                print(f"WARNING: preview is {data['duration_seconds']:.1f}s, outside 30–60s; "
                      "listen, then revise the short script using its cache", file=sys.stderr)
        elif args.command == "qa":
            result = qa_report(caller_path(args.output))
        elif args.command == "package-chapters":
            result = {"chapters": package_chapters(caller_path(args.output), args.ffmpeg)}
        elif args.command == "separate-vocals":
            from .voices import separate_vocals
            result = {"files": separate_vocals([caller_path(p) for p in args.inputs], caller_path(args.out),
                                               args.separator, args.model,
                                               caller_path(args.model_dir) if args.model_dir else None)}
        elif args.command == "find-speaker":
            from .voices import find_speaker
            home, model_dir = engine_home(args)
            negatives = [f"{n}={caller_path(p)}" for n, p in pairs(args.negative, 2)]
            result = find_speaker(args.target, [str(caller_path(p)) for p in args.positive], negatives,
                                  pairs(args.episode, 3), caller_path(args.out), home, model_dir,
                                  args.whisper, tuple(args.high), tuple(args.medium))
        elif args.command == "review-video":
            from .voices import review_video
            index = review_video(caller_path(args.candidates), dict(pairs(args.episode, 2)),
                                 caller_path(args.out), args.tier, args.top,
                                 font=caller_path(args.font) if args.font else None)
            result = {"output": str(caller_path(args.out)), "clips": len(index),
                      "index": str(caller_path(args.out).with_suffix(".json")), "identity_verified": False}
        elif args.command == "confirm-review":
            from .voices import confirm_review
            result = confirm_review(caller_path(args.index), caller_path(args.confirmed), args.reject,
                                    args.reject_as, caller_path(args.anchors) if args.anchors else None)
        else:
            data = patch_opening(caller_path(args.plan), caller_path(args.base),
                                 caller_path(args.config), caller_path(args.out), args.replace_until)
            result = {"output": str(caller_path(args.out)), "duration_seconds": data["duration_seconds"],
                      "revision": data["revision"]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("duration_ok", True):
            return 3
        return 0 if result.get("ready", True) else 2
    except (ValueError, RuntimeError, FileNotFoundError, ImportError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
