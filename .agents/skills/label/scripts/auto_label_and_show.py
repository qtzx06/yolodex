#!/usr/bin/env python3
"""Auto-label frames (based on config label_mode) and show output label previews."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from shared.utils import load_config


MODE_TO_SCRIPT = {
    "cua+sam": "label_cua_sam.py",
    "gemini": "label_gemini.py",
    "gpt": "run.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-label", action="store_true", help="Only show existing labels.")
    parser.add_argument("--samples", type=int, default=5, help="How many label files to print.")
    parser.add_argument(
        "--preview-images",
        type=int,
        default=3,
        help="How many annotated preview images to render.",
    )
    return parser.parse_args()


def maybe_run_labeler(config: dict[str, object], frames_dir: Path, skip_label: bool) -> None:
    if skip_label:
        print("[show] Skipping labeling step by request.")
        return

    frames = sorted(frames_dir.glob("*.jpg"))
    if not frames:
        raise RuntimeError("No frames found. Run collect first.")

    unlabeled = [frame for frame in frames if not frame.with_suffix(".txt").exists()]
    if not unlabeled:
        print("[show] All frames already labeled.")
        return

    mode = str(config.get("label_mode", "gpt")).strip().lower()
    script_name = MODE_TO_SCRIPT.get(mode)
    if not script_name:
        raise RuntimeError(f"Unsupported label_mode: {mode}")

    script_path = Path(__file__).resolve().parent / script_name
    print(f"[show] Running labeler mode '{mode}' on {len(unlabeled)} unlabeled frames...")
    subprocess.run([sys.executable, str(script_path)], check=True)


def load_class_names(output_dir: Path, configured_classes: list[str]) -> list[str]:
    class_map_path = output_dir / "classes.txt"
    if class_map_path.exists():
        file_names = [line.strip() for line in class_map_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if file_names:
            return file_names
    return [name.strip() for name in configured_classes if str(name).strip()]


def read_label_rows(label_path: Path) -> list[tuple[int, float, float, float, float]]:
    rows: list[tuple[int, float, float, float, float]] = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            continue
        try:
            class_id = int(parts[0])
            cx = float(parts[1])
            cy = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])
        except ValueError:
            continue
        rows.append((class_id, cx, cy, w, h))
    return rows


def label_name(class_id: int, class_names: list[str]) -> str:
    if 0 <= class_id < len(class_names):
        return class_names[class_id]
    return f"class_{class_id}"


def print_summary(
    frames_dir: Path,
    output_dir: Path,
    samples: int,
    configured_classes: list[str],
) -> list[Path]:
    frames = sorted(frames_dir.glob("*.jpg"))
    labels = sorted(frames_dir.glob("*.txt"))
    class_names = load_class_names(output_dir, configured_classes)
    counts: Counter[str] = Counter()
    total_boxes = 0

    for label_path in labels:
        for class_id, _, _, _, _ in read_label_rows(label_path):
            counts[label_name(class_id, class_names)] += 1
            total_boxes += 1

    print(f"[show] Frames: {len(frames)}")
    print(f"[show] Labeled files: {len(labels)}")
    print(f"[show] Total boxes: {total_boxes}")
    if counts:
        print("[show] Boxes per class:")
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            print(f"  - {name}: {count}")

    if not labels:
        print("[show] No labels to display yet.")
        return []

    print("[show] Sample label output:")
    for label_path in labels[: max(samples, 0)]:
        rows = read_label_rows(label_path)
        print(f"  {label_path.name}")
        if not rows:
            print("    (empty)")
            continue
        for class_id, cx, cy, w, h in rows:
            cname = label_name(class_id, class_names)
            print(f"    {cname} ({class_id}): cx={cx:.4f} cy={cy:.4f} w={w:.4f} h={h:.4f}")

    return labels


def draw_preview_images(
    labels: list[Path],
    output_dir: Path,
    max_images: int,
    configured_classes: list[str],
) -> None:
    if max_images <= 0:
        return

    class_names = load_class_names(output_dir, configured_classes)
    preview_dir = output_dir / "label_preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    rendered = 0
    for label_path in labels:
        if rendered >= max_images:
            break
        image_path = label_path.with_suffix(".jpg")
        if not image_path.exists():
            continue

        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        width, height = image.size

        for class_id, cx, cy, w, h in read_label_rows(label_path):
            x1 = (cx - (w / 2.0)) * width
            y1 = (cy - (h / 2.0)) * height
            x2 = (cx + (w / 2.0)) * width
            y2 = (cy + (h / 2.0)) * height
            color = (255, 64 + ((class_id * 53) % 160), 64 + ((class_id * 97) % 160))
            draw.rectangle((x1, y1, x2, y2), outline=color, width=3)
            draw.text((x1 + 4, y1 + 4), label_name(class_id, class_names), fill=color)

        out_path = preview_dir / f"{image_path.stem}_preview.jpg"
        image.save(out_path, quality=92)
        print(f"[show] Wrote preview: {out_path}")
        rendered += 1

    if rendered == 0:
        print("[show] No preview images created.")


def main() -> int:
    args = parse_args()
    config = load_config()
    output_dir = Path(str(config.get("output_dir", "output")))
    frames_dir = output_dir / "frames"
    configured_classes = list(config.get("classes", []))

    try:
        maybe_run_labeler(config, frames_dir, args.skip_label)
    except subprocess.CalledProcessError as exc:
        print(f"Error: labeling subprocess failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    labels = print_summary(frames_dir, output_dir, args.samples, configured_classes)
    draw_preview_images(labels, output_dir, args.preview_images, configured_classes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
