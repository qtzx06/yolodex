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

    try:
        run_command(
            [
                "yt-dlp",
                "-f",
                "bestvideo+bestaudio/best",
                "--merge-output-format",
                "mp4",
                "-o",
                str(raw_dir / "video"),
                url,
            ],
        )
    except CommandError as exc:
        raise IngestError(str(exc)) from exc

    video_candidates = sorted(
        raw_dir.glob("video*"),
        key=lambda path: path.stat().st_mtime,
    )
    if not video_candidates:
        raise IngestError("yt-dlp did not produce a video file")
    video_path = video_candidates[-1]

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
