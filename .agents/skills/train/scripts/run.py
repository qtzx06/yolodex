#!/usr/bin/env python3
"""Train skill: split dataset, generate dataset.yaml, train YOLO model."""

from __future__ import annotations

import json
import random
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from shared.utils import load_config
from shared.run_state import (
    init_run_manifest,
    mark_phase_done,
    mark_phase_failed,
    mark_phase_running,
)


def split_dataset(
    pairs: list[tuple[Path, Path]],
    dataset_dir: Path,
    train_split: float,
    seed: int,
) -> tuple[Path, Path]:
    """Split labeled images into train/val sets."""
    train_img = dataset_dir / "images" / "train"
    val_img = dataset_dir / "images" / "val"
    train_lbl = dataset_dir / "labels" / "train"
    val_lbl = dataset_dir / "labels" / "val"

    # Rebuild split directories each run to avoid stale file leakage between iterations.
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)

    for d in [train_img, val_img, train_lbl, val_lbl]:
        d.mkdir(parents=True, exist_ok=True)

    if not pairs:
        print("[train] No labeled image pairs found.", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(seed)
    rng.shuffle(pairs)
    split_idx = int(len(pairs) * train_split)
    if len(pairs) > 1:
        split_idx = max(1, min(split_idx, len(pairs) - 1))
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


def collect_pairs(frames_dir: Path, aug_dir: Path | None) -> list[tuple[Path, Path]]:
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

    return pairs


def validate_labels(
    pairs: list[tuple[Path, Path]],
    num_classes: int,
    report_path: Path,
) -> dict[str, int]:
    """Validate YOLO label syntax/ranges and write report."""
    total_errors = 0
    total_warnings = 0
    files_with_errors = 0
    files_checked = 0
    report_rows: list[dict[str, object]] = []

    # De-duplicate label files while preserving order.
    seen: set[Path] = set()
    labels: list[Path] = []
    for _, label_path in pairs:
        if label_path not in seen:
            labels.append(label_path)
            seen.add(label_path)

    for label_path in labels:
        files_checked += 1
        file_errors: list[str] = []
        file_warnings: list[str] = []
        raw = label_path.read_text(encoding="utf-8")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]

        if not lines:
            file_warnings.append("empty label file")

        for idx, line in enumerate(lines, start=1):
            parts = line.split()
            if len(parts) != 5:
                file_errors.append(f"line {idx}: expected 5 fields, got {len(parts)}")
                continue

            try:
                class_id = int(parts[0])
            except ValueError:
                file_errors.append(f"line {idx}: class id is not an int")
                continue

            try:
                cx, cy, w, h = [float(x) for x in parts[1:]]
            except ValueError:
                file_errors.append(f"line {idx}: bbox values are not floats")
                continue

            if class_id < 0 or class_id >= num_classes:
                file_errors.append(f"line {idx}: class id {class_id} out of range [0,{num_classes - 1}]")
            if not (0.0 <= cx <= 1.0 and 0.0 <= cy <= 1.0):
                file_errors.append(f"line {idx}: center out of range [0,1]")
            if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                file_errors.append(f"line {idx}: width/height out of range (0,1]")
            if cx - (w / 2.0) < 0.0 or cx + (w / 2.0) > 1.0:
                file_warnings.append(f"line {idx}: bbox extends beyond x bounds")
            if cy - (h / 2.0) < 0.0 or cy + (h / 2.0) > 1.0:
                file_warnings.append(f"line {idx}: bbox extends beyond y bounds")

        if file_errors:
            files_with_errors += 1

        total_errors += len(file_errors)
        total_warnings += len(file_warnings)
        report_rows.append(
            {
                "file": str(label_path),
                "errors": file_errors,
                "warnings": file_warnings,
            }
        )

    report = {
        "files_checked": files_checked,
        "files_with_errors": files_with_errors,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "results": report_rows,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "files_checked": files_checked,
        "files_with_errors": files_with_errors,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
    }


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
    config = load_config()
    init_run_manifest(config)
    mark_phase_running(config, "train")
    output_dir = Path(config.get("output_dir", "output"))
    frames_dir = output_dir / "frames"
    aug_dir = output_dir / "augmented"
    dataset_dir = output_dir / "dataset"
    weights_dir = output_dir / "weights"
    train_split = config.get("train_split", 0.8)
    yolo_model = config.get("yolo_model", "yolov8n.pt")
    epochs = config.get("epochs", 50)
    seed = int(config.get("seed", 42))

    if not 0.0 < float(train_split) < 1.0:
        mark_phase_failed(config, "train", "train_split must be between 0 and 1 (exclusive).")
        print("[train] Error: train_split must be between 0 and 1 (exclusive).", file=sys.stderr)
        return 1

    # Load class names
    classes_path = output_dir / "classes.txt"
    if not classes_path.exists():
        mark_phase_failed(config, "train", "classes.txt not found.")
        print("[train] Error: classes.txt not found. Run label skill first.", file=sys.stderr)
        return 1

    classes = [c for c in classes_path.read_text().strip().split("\n") if c]

    print(f"[train] {len(classes)} classes: {', '.join(classes)}")
    pairs = collect_pairs(frames_dir, aug_dir if aug_dir.exists() else None)

    if not pairs:
        mark_phase_failed(config, "train", "No labeled image pairs found.")
        print("[train] Error: No labeled image pairs found.", file=sys.stderr)
        return 1

    qa_report_path = output_dir / "label_qa_report.json"
    qa = validate_labels(pairs, len(classes), qa_report_path)
    print(
        f"[train] Label QA: {qa['files_checked']} files, "
        f"{qa['total_errors']} errors, {qa['total_warnings']} warnings"
    )
    if qa["total_errors"] > 0:
        mark_phase_failed(
            config,
            "train",
            f"Label QA failed with {qa['total_errors']} error(s). See {qa_report_path}",
        )
        print(
            f"[train] Error: Label QA failed with {qa['total_errors']} error(s). "
            f"See {qa_report_path}",
            file=sys.stderr,
        )
        return 1

    split_dataset(
        pairs,
        dataset_dir,
        train_split,
        seed,
    )

    dataset_yaml = generate_dataset_yaml(dataset_dir, classes, output_dir / "dataset.yaml")

    train_model(dataset_yaml, yolo_model, epochs, weights_dir)

    print("[train] Training complete.")
    mark_phase_done(
        config,
        "train",
        {
            "dataset_yaml": str(dataset_yaml),
            "weights_path": str(weights_dir / "best.pt"),
            "epochs": epochs,
            "label_qa_report": str(qa_report_path),
            "label_qa_errors": qa["total_errors"],
            "label_qa_warnings": qa["total_warnings"],
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
