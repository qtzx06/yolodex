#!/usr/bin/env python3
"""End-to-end YouTube -> frames -> GPT-4o labels -> YOLO annotations pipeline."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI


@dataclass
class BoundingBox:
    class_name: str
    x: float
    y: float
    width: float
    height: float


PROMPT = """
Detect every visible object in this image and return bounding boxes.

Return strict JSON using this exact schema:
{
  "objects": [
    {
      "class_name": "string",
      "x": 0,
      "y": 0,
      "width": 0,
      "height": 0
    }
  ]
}

Rules:
- x,y,width,height must be pixel values in the original image.
- x,y is top-left corner.
- Include all salient objects (people, vehicles, UI elements, weapons, items, enemies, etc.).
- Do not include explanation text.
""".strip()


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


def detect_objects(client: OpenAI, model: str, frame_path: Path) -> list[BoundingBox]:
    image_b64 = encode_image_base64(frame_path)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": PROMPT},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}",
                    },
                ],
            }
        ],
        temperature=0,
    )

    payload = extract_json_from_text(response.output_text)
    objects = payload.get("objects", [])
    if not isinstance(objects, list):
        raise PipelineError("Model JSON missing 'objects' list.")

    boxes: list[BoundingBox] = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        try:
            boxes.append(
                BoundingBox(
                    class_name=str(obj["class_name"]).strip().lower().replace(" ", "_"),
                    x=float(obj["x"]),
                    y=float(obj["y"]),
                    width=float(obj["width"]),
                    height=float(obj["height"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return boxes


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def to_yolo_line(box: BoundingBox, class_id: int, img_w: int, img_h: int) -> str:
    # Clamp raw box values to image bounds before normalization.
    x = clamp(box.x, 0.0, float(img_w))
    y = clamp(box.y, 0.0, float(img_h))
    w = clamp(box.width, 0.0, float(img_w))
    h = clamp(box.height, 0.0, float(img_h))

    center_x = (x + (w / 2.0)) / float(img_w)
    center_y = (y + (h / 2.0)) / float(img_h)
    norm_w = w / float(img_w)
    norm_h = h / float(img_h)

    center_x = clamp(center_x, 0.0, 1.0)
    center_y = clamp(center_y, 0.0, 1.0)
    norm_w = clamp(norm_w, 0.0, 1.0)
    norm_h = clamp(norm_h, 0.0, 1.0)

    return f"{class_id} {center_x:.6f} {center_y:.6f} {norm_w:.6f} {norm_h:.6f}"


def write_yolo_labels(
    frame_path: Path,
    boxes: list[BoundingBox],
    class_to_id: dict[str, int],
) -> None:
    img_w, img_h = read_image_dimensions(frame_path)

    lines: list[str] = []
    for box in boxes:
        if box.class_name not in class_to_id:
            class_to_id[box.class_name] = len(class_to_id)
        class_id = class_to_id[box.class_name]
        lines.append(to_yolo_line(box, class_id, img_w, img_h))

    label_path = frame_path.with_suffix(".txt")
    label_path.write_text("\n".join(lines), encoding="utf-8")


def write_class_map(class_to_id: dict[str, int], output_path: Path) -> None:
    # YOLO usually stores class names by class index in a plain text names file.
    names = [name for name, _ in sorted(class_to_id.items(), key=lambda item: item[1])]
    output_path.write_text("\n".join(names), encoding="utf-8")


def run_pipeline(youtube_url: str, output_dir: Path, model: str) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise PipelineError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "video.mp4"
    frames_dir = output_dir / "frames"

    print("[1/4] Downloading video with yt-dlp...")
    download_video(youtube_url, video_path)

    print("[2/4] Extracting frames at 1 FPS with ffmpeg...")
    frames = extract_frames(video_path, frames_dir, fps=1)

    print(f"[3/4] Labeling {len(frames)} frames with {model}...")
    class_to_id: dict[str, int] = {}

    for idx, frame_path in enumerate(frames, start=1):
        print(f"  - Frame {idx}/{len(frames)}: {frame_path.name}")
        boxes = detect_objects(client, model, frame_path)
        write_yolo_labels(frame_path, boxes, class_to_id)

    write_class_map(class_to_id, output_dir / "classes.txt")

    print("[4/4] Done.")
    print(f"Frames: {frames_dir}")
    print("YOLO labels saved next to each frame image.")
    print(f"Class mapping: {output_dir / 'classes.txt'}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="YouTube -> frames -> GPT-4o vision labels -> YOLO format"
    )
    parser.add_argument("youtube_url", help="YouTube video URL")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (default: output)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI vision-capable model (default: gpt-4o)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        run_pipeline(args.youtube_url, Path(args.output_dir), args.model)
    except PipelineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
