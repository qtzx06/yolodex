from __future__ import annotations

from pathlib import Path

from .rules import default_rules_path, extract_rule_classes

class ValidationError(RuntimeError):
    pass


def read_data_yaml(dataset_dir: Path) -> list[str]:
    data_path = dataset_dir / "data.yaml"
    if not data_path.exists():
        raise ValidationError("data.yaml not found in dataset")
    names_line = None
    for line in data_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("names:"):
            names_line = line
            break
    if names_line is None:
        raise ValidationError("names not found in data.yaml")
    raw = names_line.split(":", 1)[1].strip().strip("[]")
    names = [name.strip().strip("'\"") for name in raw.split(",") if name.strip()]
    return names


def validate_dataset(dataset_dir: Path, rules_path: Path | None = None) -> None:
    resolved_rules_path = rules_path or default_rules_path()
    images_dir = dataset_dir / "images" / "train"
    labels_dir = dataset_dir / "labels" / "train"
    if not images_dir.exists():
        raise ValidationError(f"Missing images directory: {images_dir}")
    if not labels_dir.exists():
        raise ValidationError(f"Missing labels directory: {labels_dir}")

    classes = read_data_yaml(dataset_dir)
    expected_classes = extract_rule_classes(resolved_rules_path)
    if classes != expected_classes:
        raise ValidationError(
            f"Class order mismatch. data.yaml={classes}, LABELING_RULES.md={expected_classes}"
        )

    image_paths = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.jpeg")) + sorted(images_dir.glob("*.png"))
    label_paths = sorted(labels_dir.glob("*.txt"))
    if len(label_paths) != len(image_paths):
        raise ValidationError(
            f"Image/label count mismatch. images={len(image_paths)}, labels={len(label_paths)}"
        )

    image_stems = {path.stem for path in image_paths}
    label_stems = {path.stem for path in label_paths}
    missing_labels = sorted(image_stems - label_stems)
    extra_labels = sorted(label_stems - image_stems)
    if missing_labels:
        raise ValidationError(f"Missing labels for images: {missing_labels[:5]}")
    if extra_labels:
        raise ValidationError(f"Labels without images: {extra_labels[:5]}")

    max_class = len(classes) - 1

    for image in image_paths:
        label_path = labels_dir / f"{image.stem}.txt"
        for line in label_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 5:
                raise ValidationError(f"Invalid YOLO line in {label_path.name}: {line}")
            class_id = int(parts[0])
            if class_id < 0 or class_id > max_class:
                raise ValidationError(f"Invalid class id in {label_path.name}: {class_id}")
            coords = [float(v) for v in parts[1:]]
            if any(v < 0.0 or v > 1.0 for v in coords):
                raise ValidationError(f"Out of range coords in {label_path.name}: {coords}")
