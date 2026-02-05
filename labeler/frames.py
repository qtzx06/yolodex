from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .utils import CommandError, ensure_dir, ffprobe_metadata, run_command, write_json


class FrameError(RuntimeError):
    pass


def extract_frames(video_path: Path, run_dir: Path, fps: int) -> Path:
    dataset_dir = run_dir / "dataset"
    images_dir = dataset_dir / "images" / "train"
    ensure_dir(images_dir)

    frame_pattern = images_dir / "frame_%06d.jpg"
    try:
        run_command(["ffmpeg", "-y", "-i", str(video_path), "-vf", f"fps={fps}", str(frame_pattern)])
    except CommandError as exc:
        raise FrameError(str(exc)) from exc

    frames = sorted(images_dir.glob("*.jpg"))
    if not frames:
        raise FrameError("No frames extracted.")

    video_meta = ffprobe_metadata(video_path)
    try:
        video_rel = str(video_path.relative_to(run_dir))
    except ValueError:
        video_rel = str(video_path)

    payload: dict[str, Any] = {
        "video": {
            "path": video_rel,
            "width": video_meta.get("width"),
            "height": video_meta.get("height"),
            "fps": video_meta.get("fps"),
            "duration_s": video_meta.get("duration_s"),
        },
        "frames": [],
    }

    for idx, frame in enumerate(frames, start=1):
        payload["frames"].append(
            {
                "frame_index": idx,
                "timestamp_s": (idx - 1) / float(fps),
                "image_path": str(frame.relative_to(run_dir)),
            }
        )

    write_json(run_dir / "frames.json", payload)
    return images_dir


def load_frames(run_dir: Path) -> list[dict[str, Any]]:
    frames_path = run_dir / "frames.json"
    payload = json.loads(frames_path.read_text(encoding="utf-8"))
    return list(payload.get("frames", []))
