#!/usr/bin/env python3
"""Augment skill: generate synthetic training data variations with transformed labels."""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

from shared.utils import load_config


def flip_horizontal(img: Image.Image, label_lines: list[str]) -> tuple[Image.Image, list[str]]:
    """Flip image horizontally and mirror bounding box x-coordinates."""
    flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
    new_lines: list[str] = []
    for line in label_lines:
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        cls, cx, cy, w, h = parts[0], float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        new_cx = 1.0 - cx
        new_lines.append(f"{cls} {new_cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    return flipped, new_lines


def adjust_brightness(img: Image.Image, factor: float) -> Image.Image:
    """Adjust brightness by a factor (0.5-1.5 typical)."""
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)


def adjust_contrast(img: Image.Image, factor: float) -> Image.Image:
    """Adjust contrast by a factor."""
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)


def add_noise(img: Image.Image, intensity: float = 15.0) -> Image.Image:
    """Add Gaussian noise to image."""
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, intensity, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def main() -> int:
    config = load_config()
    output_dir = Path(config.get("output_dir", "output"))
    frames_dir = output_dir / "frames"
    aug_dir = output_dir / "augmented"
    aug_dir.mkdir(parents=True, exist_ok=True)

    frames = sorted(frames_dir.glob("*.jpg"))
    labeled = [f for f in frames if f.with_suffix(".txt").exists()]

    if not labeled:
        print("[augment] No labeled frames found. Run label skill first.", file=sys.stderr)
        return 1

    print(f"[augment] Augmenting {len(labeled)} labeled frames...")
    count = 0

    for frame_path in labeled:
        label_path = frame_path.with_suffix(".txt")
        label_lines = label_path.read_text(encoding="utf-8").strip().split("\n")
        label_lines = [l for l in label_lines if l.strip()]

        img = Image.open(frame_path).convert("RGB")
        stem = frame_path.stem

        # 1. Horizontal flip
        flipped_img, flipped_labels = flip_horizontal(img, label_lines)
        out_img = aug_dir / f"{stem}_flip.jpg"
        out_lbl = aug_dir / f"{stem}_flip.txt"
        flipped_img.save(out_img, quality=95)
        out_lbl.write_text("\n".join(flipped_labels), encoding="utf-8")
        count += 1

        # 2. Brightness jitter (labels unchanged)
        brightness_factor = random.uniform(0.6, 1.4)
        bright_img = adjust_brightness(img, brightness_factor)
        out_img = aug_dir / f"{stem}_bright.jpg"
        out_lbl = aug_dir / f"{stem}_bright.txt"
        bright_img.save(out_img, quality=95)
        out_lbl.write_text("\n".join(label_lines), encoding="utf-8")
        count += 1

        # 3. Contrast jitter (labels unchanged)
        contrast_factor = random.uniform(0.7, 1.3)
        contrast_img = adjust_contrast(img, contrast_factor)
        out_img = aug_dir / f"{stem}_contrast.jpg"
        out_lbl = aug_dir / f"{stem}_contrast.txt"
        contrast_img.save(out_img, quality=95)
        out_lbl.write_text("\n".join(label_lines), encoding="utf-8")
        count += 1

        # 4. Noise injection (labels unchanged)
        noisy_img = add_noise(img)
        out_img = aug_dir / f"{stem}_noise.jpg"
        out_lbl = aug_dir / f"{stem}_noise.txt"
        noisy_img.save(out_img, quality=95)
        out_lbl.write_text("\n".join(label_lines), encoding="utf-8")
        count += 1

    print(f"[augment] Generated {count} augmented samples in {aug_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
