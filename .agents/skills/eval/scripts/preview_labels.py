#!/usr/bin/env python3
"""Render YOLO annotations onto images for quick visual QA."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def load_classes(path: Path) -> list[str]:
    if not path.exists():
        return []
    names = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [name for name in names if name]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw YOLO labels onto images")
    parser.add_argument("frames_dir", help="Directory containing frame images and YOLO txt files")
    parser.add_argument("--classes", required=True, help="Path to classes.txt")
    parser.add_argument("--out-dir", default=None, help="Output directory (default: <frames_dir>/preview)")
    parser.add_argument("--limit", type=int, default=20, help="Number of images to render (default: 20)")
    parser.add_argument("--video-out", default=None, help="Optional MP4 path to encode the previews")
    parser.add_argument("--framerate", type=int, default=2, help="Framerate for preview video (default: 2)")
    return parser.parse_args()


def draw_image(img_path: Path, label_path: Path, out_path: Path, class_names: list[str]) -> None:
    image = Image.open(img_path).convert("RGB")
    width, height = image.size
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()

    if label_path.exists():
        for raw in label_path.read_text(encoding="utf-8").splitlines():
            parts = raw.strip().split()
            if len(parts) != 5:
                continue
            try:
                cls_id = int(parts[0])
                cx, cy, bw, bh = map(float, parts[1:])
            except ValueError:
                continue

            x1 = int((cx - bw / 2.0) * width)
            y1 = int((cy - bh / 2.0) * height)
            x2 = int((cx + bw / 2.0) * width)
            y2 = int((cy + bh / 2.0) * height)

            x1 = clamp(x1, 0, width - 1)
            y1 = clamp(y1, 0, height - 1)
            x2 = clamp(x2, 0, width - 1)
            y2 = clamp(y2, 0, height - 1)

            if x2 <= x1 or y2 <= y1:
                continue

            color = (
                64 + ((cls_id * 73) % 170),
                64 + ((cls_id * 131) % 170),
                64 + ((cls_id * 193) % 170),
            )
            draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=4)
            label = class_names[cls_id] if 0 <= cls_id < len(class_names) else f"class_{cls_id}"
            text_bbox = draw.textbbox((0, 0), label, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]
            text_x = x1 + 3
            text_y = y1 - (text_h + 8) if y1 >= (text_h + 8) else y1 + 3
            draw.rectangle(
                [(text_x - 3, text_y - 2), (text_x + text_w + 3, text_y + text_h + 2)],
                fill=(0, 0, 0),
            )
            draw.text((text_x, text_y), label, fill=color, font=font)

    image.save(out_path)


def main() -> int:
    args = parse_args()
    frames_dir = Path(args.frames_dir)
    classes = load_classes(Path(args.classes))

    out_dir = Path(args.out_dir) if args.out_dir else frames_dir / "preview"
    out_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(frames_dir.glob("*.jpg")) + sorted(frames_dir.glob("*.jpeg")) + sorted(frames_dir.glob("*.png"))
    if args.limit > 0:
        images = images[: args.limit]

    for image_path in images:
        draw_image(image_path, image_path.with_suffix(".txt"), out_dir / image_path.name, classes)

        print(f"Rendered {len(images)} preview images to: {out_dir}")
        if args.video_out and images:
            try:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(args.framerate),
                    "-i",
                    str(out_dir / "frame_%06d.jpg"),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(args.video_out),
                ]
                subprocess.run(cmd, check=True)
                print(f"Created preview video: {args.video_out}")
            except subprocess.CalledProcessError as exc:
                print(f"Warning: Failed to render preview video ({exc})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
