"""Shared utilities for the Yolodex pipeline."""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BoundingBox:
    class_name: str
    x: float
    y: float
    width: float
    height: float


class PipelineError(RuntimeError):
    """Raised when a pipeline step fails."""


def run_command(cmd: list[str]) -> None:
    """Run a subprocess command and raise with readable context on failure."""
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise PipelineError(f"Required executable not found: {cmd[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise PipelineError(f"Command failed ({exc.returncode}): {' '.join(cmd)}") from exc


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load config.json from the repo root."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def encode_image_base64(image_path: Path) -> str:
    image_bytes = image_path.read_bytes()
    return base64.b64encode(image_bytes).decode("utf-8")


def extract_json_from_text(text: str) -> dict[str, Any]:
    """Parse JSON directly; fallback to extracting from markdown code fences."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise PipelineError("Model did not return valid JSON.")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise PipelineError("Model returned malformed JSON.") from exc


def read_image_dimensions(frame_path: Path) -> tuple[int, int]:
    """Read width/height via ffprobe to avoid extra Python imaging deps."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(frame_path),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except Exception as exc:  # noqa: BLE001
        raise PipelineError(f"Failed to read dimensions for {frame_path}") from exc
