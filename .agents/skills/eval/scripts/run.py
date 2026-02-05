#!/usr/bin/env python3
"""Eval skill: evaluate trained YOLO model and produce metrics report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from shared.utils import load_config


def main() -> int:
    config = load_config()
    output_dir = Path(config.get("output_dir", "output"))
    weights_dir = output_dir / "weights"
    best_pt = weights_dir / "best.pt"
    target_accuracy = config.get("target_accuracy", 0.75)

    if not best_pt.exists():
        print("[eval] Error: best.pt not found. Run train skill first.", file=sys.stderr)
        return 1

    dataset_yaml = output_dir / "dataset.yaml"
    if not dataset_yaml.exists():
        print("[eval] Error: dataset.yaml not found. Run train skill first.", file=sys.stderr)
        return 1

    from ultralytics import YOLO

    model = YOLO(str(best_pt))
    results = model.val(data=str(dataset_yaml))

    # Extract metrics
    map50 = float(results.box.map50)
    map50_95 = float(results.box.map)
    precision = float(results.box.mp)
    recall = float(results.box.mr)

    # Per-class breakdown
    classes_path = output_dir / "classes.txt"
    class_names = []
    if classes_path.exists():
        class_names = [c for c in classes_path.read_text().strip().split("\n") if c]

    per_class: list[dict] = []
    if hasattr(results.box, "ap50") and results.box.ap50 is not None:
        ap50_per_class = results.box.ap50.tolist()
        for i, ap in enumerate(ap50_per_class):
            name = class_names[i] if i < len(class_names) else f"class_{i}"
            per_class.append({"class": name, "ap50": round(ap, 4)})

    # Sort by AP to identify weakest classes
    per_class.sort(key=lambda x: x["ap50"])

    meets_target = map50 >= target_accuracy

    eval_results = {
        "map50": round(map50, 4),
        "map50_95": round(map50_95, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "target_accuracy": target_accuracy,
        "meets_target": meets_target,
        "per_class": per_class,
        "weakest_classes": [c["class"] for c in per_class[:3]] if per_class else [],
    }

    results_path = output_dir / "eval_results.json"
    results_path.write_text(json.dumps(eval_results, indent=2), encoding="utf-8")

    print(f"[eval] mAP@50: {map50:.4f} | mAP@50-95: {map50_95:.4f}")
    print(f"[eval] Precision: {precision:.4f} | Recall: {recall:.4f}")
    print(f"[eval] Target: {target_accuracy} | Meets target: {meets_target}")
    if per_class:
        print(f"[eval] Weakest classes: {', '.join(eval_results['weakest_classes'])}")
    print(f"[eval] Results saved to {results_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
