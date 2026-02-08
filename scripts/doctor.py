#!/usr/bin/env python3
"""Preflight checks for Yolodex."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from shared.utils import load_config

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}[ok]{NC} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}[!!]{NC} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}[fail]{NC} {msg}")


def check_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def normalize_label_mode(raw: object) -> str:
    return str(raw or "codex").strip().lower()


def main() -> int:
    print(f"{BLUE}yolodex doctor{NC}")
    print("")

    hard_failures = 0

    print(f"{BLUE}[1/4] command checks{NC}")
    required_cmds = ["uv", "ffmpeg", "ffprobe", "yt-dlp"]
    for cmd in required_cmds:
        if check_cmd(cmd):
            ok(f"{cmd} found")
        else:
            fail(f"{cmd} missing")
            hard_failures += 1

    if check_cmd("codex"):
        ok("codex found")
    else:
        fail("codex missing (required for codex-native workflow)")
        hard_failures += 1

    print("")
    print(f"{BLUE}[2/4] config checks{NC}")
    try:
        config = load_config()
    except Exception as exc:  # noqa: BLE001
        fail(f"failed to load config.json: {exc}")
        return 1

    output_dir = Path(config.get("output_dir", "output"))
    mode = normalize_label_mode(config.get("label_mode"))

    if config.get("video_url"):
        ok("video_url set")
    else:
        warn("video_url is empty")

    classes = config.get("classes", [])
    if isinstance(classes, list) and classes:
        ok(f"{len(classes)} classes configured")
    else:
        warn("classes list is empty")

    if mode in {"codex", "gpt", "gemini", "cua+sam"}:
        ok(f"label_mode={mode}")
    else:
        fail(f"unsupported label_mode={mode}")
        hard_failures += 1

    print("")
    print(f"{BLUE}[3/4] mode requirements{NC}")
    if mode in {"codex"}:
        ok("codex mode selected (no external model key required)")
    elif mode in {"gpt", "cua+sam"}:
        if os.getenv("OPENAI_API_KEY"):
            ok("OPENAI_API_KEY set")
        else:
            fail("OPENAI_API_KEY missing for selected label_mode")
            hard_failures += 1
    elif mode == "gemini":
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            ok("gemini key set")
        else:
            fail("GEMINI_API_KEY / GOOGLE_API_KEY missing for gemini mode")
            hard_failures += 1

    print("")
    print(f"{BLUE}[4/4] output path checks{NC}")
    project = config.get("project")
    if project:
        ok(f"project={project} -> output_dir={output_dir}")
    else:
        warn("project not set (using output_dir fallback)")

    if output_dir.exists():
        ok(f"output directory exists: {output_dir}")
    else:
        warn(f"output directory does not exist yet: {output_dir}")

    print("")
    if hard_failures:
        fail(f"doctor found {hard_failures} blocking issue(s)")
        return 1

    ok("doctor checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

