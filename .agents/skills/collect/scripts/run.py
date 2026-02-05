#!/usr/bin/env python3
"""Collect skill: download YouTube video and extract frames."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Ensure repo root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from shared.utils import PipelineError, load_config, run_command


def is_local_file(video_url: str) -> bool:
    """Check if video_url is a local file path rather than a URL."""
    return Path(video_url).exists()


def copy_local_video(src: str, output_path: Path) -> None:
    """Copy a local video file to the output directory."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, output_path)


def download_video(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_command([
        "yt-dlp",
        "-f",
        "bestvideo+bestaudio/best",
        "-o",
        str(output_path),
        url,
    ])
    # yt-dlp may append the real container extension (e.g. .webm) even when
    # the output template ends with .mp4. Normalize to the expected path.
    if not output_path.exists():
        candidates = sorted(output_path.parent.glob(f"{output_path.name}*"))
        for candidate in candidates:
            if candidate == output_path:
                continue
            if candidate.is_file():
                candidate.replace(output_path)
                break


def extract_frames(video_path: Path, frames_dir: Path, fps: int = 1) -> list[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_pattern = frames_dir / "frame_%06d.jpg"
    run_command([
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps}",
        str(frame_pattern),
    ])
    frames = sorted(frames_dir.glob("*.jpg"))
    if not frames:
        raise PipelineError("No frames extracted. Check video input and ffmpeg installation.")
    return frames


def main() -> int:
    config = load_config()
    video_url = config["video_url"]
    if not video_url:
        print("Error: video_url is empty in config.json", file=sys.stderr)
        return 1

    output_dir = Path(config.get("output_dir", "output"))
    fps = config.get("fps", 1)

    video_path = output_dir / "video.mp4"
    frames_dir = output_dir / "frames"

    try:
        if is_local_file(video_url):
            print(f"[collect] Copying local video: {video_url}")
            copy_local_video(video_url, video_path)
        else:
            print("[collect] Downloading video with yt-dlp...")
            download_video(video_url, video_path)

        print(f"[collect] Extracting frames at {fps} FPS with ffmpeg...")
        frames = extract_frames(video_path, frames_dir, fps=fps)
        print(f"[collect] Extracted {len(frames)} frames to {frames_dir}")
    except PipelineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
