from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from .core import load_json, resolve_path, validate_plan
from .pipeline import extract_source, load_config, patch_opening, render, resolve_voice


def caller_path(value):
    base = os.environ.get("KURUMI_CALLER_CWD") or os.getcwd()
    return resolve_path(value, base)


def parser():
    root = argparse.ArgumentParser(description="Preview-first Kurumi-led research dialogue.")
    subs = root.add_subparsers(dest="command", required=True)
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
    return root


def doctor(config_path, plan_path=None, import_native=False):
    from .engine import import_engine, index_home
    config = load_config(config_path)
    report = {"ready": True, "missing": [], "voices": {}}
    try:
        home = index_home(config)
        report["index_home"] = str(home)
    except ValueError as error:
        home = None
        report["missing"].append(str(error))
    binary = config.get("ffmpeg", "ffmpeg")
    if not (shutil.which(binary) or Path(binary).is_file()):
        report["missing"].append("ffmpeg executable")
    if plan_path:
        plan = validate_plan(load_json(plan_path), "opening")
        names = sorted({r["speaker"] for r in plan["lines"]})
    else:
        names = sorted(config.get("voices", {}))
    for name in names:
        try:
            voice, emotion, profile = resolve_voice(config, name, "explain")
            report["voices"][name] = {"reference_audio": str(voice),
                                      "emotion_audio": str(emotion) if emotion else None,
                                      "identity_label": profile.get("identity_label", name)}
        except (ValueError, FileNotFoundError) as error:
            report["missing"].append(str(error))
    if import_native and home:
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
        if args.command == "extract":
            data = extract_source(caller_path(args.source), caller_path(args.out))
            result = {"output": str(caller_path(args.out)), "pages": data["page_count"],
                      "empty_text_pages": data["empty_text_pages"]}
        elif args.command == "validate":
            data = validate_plan(load_json(caller_path(args.plan)), args.stage)
            result = {"valid": True, "lead": data["lead"],
                      "lead_text_fraction": data["lead_text_fraction"],
                      "speakers": data["speaker_characters"], "turns": len(data["lines"])}
        elif args.command == "doctor":
            result = doctor(caller_path(args.config),
                            caller_path(args.plan) if args.plan else None, args.import_engine)
        elif args.command == "render":
            data = render(caller_path(args.plan), caller_path(args.config), caller_path(args.out),
                          args.stage, args.approved_preview)
            result = {"output": str(caller_path(args.out)), "duration_seconds": data["duration_seconds"],
                      "lead_speech_fraction": data["lead_speech_fraction"], "stage": data["stage"]}
        else:
            data = patch_opening(caller_path(args.plan), caller_path(args.base),
                                 caller_path(args.config), caller_path(args.out), args.replace_until)
            result = {"output": str(caller_path(args.out)), "duration_seconds": data["duration_seconds"],
                      "revision": data["revision"]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ready", True) else 2
    except (ValueError, RuntimeError, FileNotFoundError, ImportError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

