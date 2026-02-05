from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .tasks import load_classes
from .utils import ensure_dir, normalize_class


class MergeError(RuntimeError):
    pass


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def to_yolo(box: dict[str, Any], class_id: int, img_w: int, img_h: int) -> str:
    x = clamp(float(box["x"]), 0.0, float(img_w))
    y = clamp(float(box["y"]), 0.0, float(img_h))
    w = clamp(float(box["width"]), 0.0, float(img_w))
    h = clamp(float(box["height"]), 0.0, float(img_h))

    cx = clamp((x + w / 2.0) / float(img_w), 0.0, 1.0)
    cy = clamp((y + h / 2.0) / float(img_h), 0.0, 1.0)
    nw = clamp(w / float(img_w), 0.0, 1.0)
    nh = clamp(h / float(img_h), 0.0, 1.0)
    return f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}"


def read_frames(run_dir: Path) -> list[dict[str, Any]]:
    frames_path = run_dir / "frames.json"
    payload = json.loads(frames_path.read_text(encoding="utf-8"))
    return list(payload.get("frames", []))


def load_label_outputs(labels_dir: Path) -> dict[str, dict[str, Any]]:
    outputs: dict[str, dict[str, Any]] = {}
    for path in sorted(labels_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            outputs[payload["image_path"]] = payload
    return outputs


def write_data_yaml(dataset_dir: Path, classes: list[str]) -> None:
    data_path = dataset_dir / "data.yaml"
    lines = [
        f"path: {dataset_dir}",
        "train: images/train",
        f"nc: {len(classes)}",
        f"names: [{', '.join(classes)}]",
    ]
    data_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def merge_to_yolo(run_dir: Path, classes_path: Path | None) -> Path:
    frames = read_frames(run_dir)
    if not frames:
        raise MergeError("No frames found. Did you run extract-frames?")

    classes = load_classes(classes_path)
    class_map = {normalize_class(name): idx for idx, name in enumerate(classes)}

    labels_dir = run_dir / "dataset" / "labels" / "train"
    ensure_dir(labels_dir)

    outputs = load_label_outputs(run_dir / "labels_json")

    for frame in frames:
        image_path = frame["image_path"]
        image_rel = Path(image_path)
        label_path = labels_dir / f"{image_rel.stem}.txt"

        payload = outputs.get(image_path)
        if not payload:
            label_path.write_text("", encoding="utf-8")
            continue

        img_w = int(payload.get("width", 0))
        img_h = int(payload.get("height", 0))
        lines: list[str] = []
        for box in payload.get("boxes", []):
            class_name = normalize_class(str(box.get("class_name", "")))
            if class_name not in class_map:
                continue
            lines.append(to_yolo(box, class_map[class_name], img_w, img_h))

        label_path.write_text("\n".join(lines), encoding="utf-8")

    write_data_yaml(run_dir / "dataset", classes)
    return run_dir / "dataset"
