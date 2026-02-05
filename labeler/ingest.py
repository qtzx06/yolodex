from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import CommandError, ensure_dir, ffprobe_metadata, run_command, write_json


class IngestError(RuntimeError):
    pass


def ingest_youtube(url: str, run_dir: Path) -> Path:
    ensure_dir(run_dir)
    raw_dir = run_dir / "raw"
    ensure_dir(raw_dir)

    video_path = raw_dir / "video.mp4"

    try:
        run_command(["yt-dlp", "-f", "bestvideo+bestaudio/best", "-o", str(video_path), url])
    except CommandError as exc:
        raise IngestError(str(exc)) from exc

    meta = ffprobe_metadata(video_path)
    payload: dict[str, Any] = {
        "source_url": url,
        "path": str(video_path.relative_to(run_dir)),
        "width": meta.get("width"),
        "height": meta.get("height"),
        "fps": meta.get("fps"),
        "duration_s": meta.get("duration_s"),
    }
    write_json(run_dir / "video.json", payload)
    return video_path
