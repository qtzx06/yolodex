from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class CommandError(RuntimeError):
    pass


def run_command(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise CommandError(f"Missing executable: {cmd[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise CommandError(f"Command failed ({exc.returncode}): {' '.join(cmd)}") from exc


def ffprobe_metadata(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,r_frame_rate,duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        stream = payload["streams"][0]
    except Exception as exc:  # noqa: BLE001
        raise CommandError(f"Failed to read metadata for {path}") from exc

    def parse_rate(value: str | None) -> float | None:
        if not value or value == "0/0":
            return None
        if "/" in value:
            num, den = value.split("/", 1)
            try:
                return float(num) / float(den)
            except (ValueError, ZeroDivisionError):
                return None
        try:
            return float(value)
        except ValueError:
            return None

    fps = parse_rate(stream.get("avg_frame_rate")) or parse_rate(stream.get("r_frame_rate"))
    duration = stream.get("duration")
    try:
        duration_s = float(duration) if duration is not None else None
    except ValueError:
        duration_s = None

    return {
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "fps": fps,
        "duration_s": duration_s,
    }


def read_image_dimensions(path: Path) -> tuple[int, int]:
    meta = ffprobe_metadata(path)
    return int(meta["width"]), int(meta["height"])


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_class(name: str) -> str:
    return name.strip().lower().replace(" ", "_")
