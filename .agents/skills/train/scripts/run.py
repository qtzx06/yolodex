#!/usr/bin/env python3
"""Train skill: split dataset, generate dataset.yaml, train YOLO model."""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from shared.utils import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLO model from labeled data.")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to config.json (defaults to repo root config).",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Override project name (forces output_dir to runs/<project>/).",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override training epochs for this run only.",
    )
    return parser.parse_args()


def split_dataset(
    frames_dir: Path,
    aug_dir: Path | None,
    dataset_dir: Path,
    train_split: float,
) -> tuple[Path, Path]:
    """Split labeled images into train/val sets."""
    train_img = dataset_dir / "images" / "train"
    val_img = dataset_dir / "images" / "val"
    train_lbl = dataset_dir / "labels" / "train"
    val_lbl = dataset_dir / "labels" / "val"

    for d in [train_img, val_img, train_lbl, val_lbl]:
        d.mkdir(parents=True, exist_ok=True)

    # Collect all image/label pairs
    pairs: list[tuple[Path, Path]] = []

    for img_path in sorted(frames_dir.glob("*.jpg")):
        lbl_path = img_path.with_suffix(".txt")
        if lbl_path.exists():
            pairs.append((img_path, lbl_path))

    if aug_dir and aug_dir.exists():
        for img_path in sorted(aug_dir.glob("*.jpg")):
            lbl_path = img_path.with_suffix(".txt")
            if lbl_path.exists():
                pairs.append((img_path, lbl_path))

    if not pairs:
        print("[train] No labeled image pairs found.", file=sys.stderr)
        sys.exit(1)

    random.shuffle(pairs)
    split_idx = int(len(pairs) * train_split)
    train_pairs = pairs[:split_idx]
    val_pairs = pairs[split_idx:]

    for img, lbl in train_pairs:
        shutil.copy2(img, train_img / img.name)
        shutil.copy2(lbl, train_lbl / lbl.name)

    for img, lbl in val_pairs:
        shutil.copy2(img, val_img / img.name)
        shutil.copy2(lbl, val_lbl / lbl.name)

    print(f"[train] Split: {len(train_pairs)} train, {len(val_pairs)} val")
    return dataset_dir, dataset_dir


def generate_dataset_yaml(
    dataset_dir: Path,
    classes: list[str],
    output_path: Path,
) -> Path:
    """Generate dataset.yaml for ultralytics."""
    data = {
        "path": str(dataset_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(classes)},
    }
    output_path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    print(f"[train] dataset.yaml written to {output_path}")
    return output_path


def train_model(
    dataset_yaml: Path,
    yolo_model: str,
    epochs: int,
    weights_dir: Path,
) -> Path:
    """Train YOLO model using ultralytics."""
    from ultralytics import YOLO

    weights_dir.mkdir(parents=True, exist_ok=True)

    model = YOLO(yolo_model)
    results = model.train(
        data=str(dataset_yaml),
        epochs=epochs,
        imgsz=640,
        project=str(weights_dir.parent),
        name="yolo_run",
        exist_ok=True,
    )

    # Copy best weights to expected location
    best_src = Path(results.save_dir) / "weights" / "best.pt"
    best_dst = weights_dir / "best.pt"
    if best_src.exists():
        shutil.copy2(best_src, best_dst)
        print(f"[train] Best weights saved to {best_dst}")
    else:
        print("[train] Warning: best.pt not found in training output", file=sys.stderr)

    return best_dst


def main() -> int:
    args = parse_args()
    config = load_config(args.config)

    if args.project:
        config["project"] = args.project
        config["output_dir"] = f"runs/{args.project}"
    if args.epochs is not None:
        if args.epochs < 1:
            print("[train] Error: --epochs must be >= 1", file=sys.stderr)
            return 1
        config["epochs"] = args.epochs

    output_dir = Path(config.get("output_dir", "output"))
    frames_dir = output_dir / "frames"
    aug_dir = output_dir / "augmented"
    dataset_dir = output_dir / "dataset"
    weights_dir = output_dir / "weights"
    train_split = config.get("train_split", 0.8)
    yolo_model = config.get("yolo_model", "yolov8n.pt")
    epochs = config.get("epochs", 50)

    print(f"[train] output_dir={output_dir}")
    print(f"[train] epochs={epochs}")

    # Load class names
    classes_path = output_dir / "classes.txt"
    if not classes_path.exists():
        print("[train] Error: classes.txt not found. Run label skill first.", file=sys.stderr)
        return 1

    classes = [c for c in classes_path.read_text().strip().split("\n") if c]

    print(f"[train] {len(classes)} classes: {', '.join(classes)}")

    split_dataset(
        frames_dir,
        aug_dir if aug_dir.exists() else None,
        dataset_dir,
        train_split,
    )

    dataset_yaml = generate_dataset_yaml(dataset_dir, classes, output_dir / "dataset.yaml")

    train_model(dataset_yaml, yolo_model, epochs, weights_dir)

    print("[train] Training complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
