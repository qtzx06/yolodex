#!/usr/bin/env python3
"""Gemini labeling: uses Gemini's native bounding box detection for precise object localization."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from shared.utils import (
    BoundingBox,
    PipelineError,
    clamp,
    load_config,
    read_image_dimensions,
)


def detect_objects_gemini(
    model, frame_path: Path, classes: list[str],
) -> list[BoundingBox]:
    """Use Gemini's native bounding box detection."""
    import google.generativeai as genai
    from PIL import Image

    img = Image.open(frame_path)
    img_w, img_h = img.size

    if classes:
        class_hint = f"Focus on detecting: {', '.join(classes)}."
    else:
        class_hint = "Detect all visible objects."

    prompt = (
        f"Detect objects in this game screenshot and return bounding boxes. "
        f"{class_hint}\n\n"
        f"Return JSON with this format:\n"
        f'{{"objects": [{{"label": "class_name", "box_2d": [y_min, x_min, y_max, x_max]}}]}}\n'
        f"Coordinates should be in the 0-1000 normalized scale."
    )

    response = model.generate_content([prompt, img])
    text = response.text

    # Parse response — Gemini returns bounding boxes in [y0, x0, y1, x1] format, 0-1000 scale
    try:
        # Try direct JSON parse
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try extracting from markdown code blocks
        import re
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            print(f"    Warning: Gemini did not return valid JSON")
            return []
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            print(f"    Warning: Gemini returned malformed JSON")
            return []

    objects = data.get("objects", [])
    boxes: list[BoundingBox] = []

    for obj in objects:
        if not isinstance(obj, dict):
            continue
        try:
            label = str(obj.get("label", "")).strip().lower().replace(" ", "_")
            box_2d = obj["box_2d"]  # [y_min, x_min, y_max, x_max] in 0-1000

            # Convert from Gemini's 0-1000 [y0, x0, y1, x1] to pixel [x, y, w, h]
            y_min = float(box_2d[0]) / 1000.0 * img_h
            x_min = float(box_2d[1]) / 1000.0 * img_w
            y_max = float(box_2d[2]) / 1000.0 * img_h
            x_max = float(box_2d[3]) / 1000.0 * img_w

            boxes.append(BoundingBox(
                class_name=label,
                x=x_min,
                y=y_min,
                width=x_max - x_min,
                height=y_max - y_min,
            ))
        except (KeyError, TypeError, ValueError, IndexError):
            continue

    return boxes


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY or GOOGLE_API_KEY is not set.", file=sys.stderr)
        return 1

    try:
        import google.generativeai as genai
    except ImportError:
        print("Error: google-generativeai not installed. Run: uv pip install google-generativeai", file=sys.stderr)
        return 1

    config = load_config()
    classes = config.get("classes", [])
    gemini_model = config.get("gemini_model", "gemini-2.5-flash")
    output_dir = Path(config.get("output_dir", "output"))
    frames_dir = output_dir / "frames"

    frames = sorted(frames_dir.glob("*.jpg"))
    if not frames:
        print("Error: No frames found. Run the collect skill first.", file=sys.stderr)
        return 1

    unlabeled = [f for f in frames if not f.with_suffix(".txt").exists()]
    if not unlabeled:
        print("[gemini] All frames already labeled.")
        return 0

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(gemini_model)

    class_to_id: dict[str, int] = {}
    class_map_path = output_dir / "classes.txt"
    if class_map_path.exists():
        for idx, name in enumerate(class_map_path.read_text().strip().split("\n")):
            if name:
                class_to_id[name] = idx

    print(f"[gemini] Labeling {len(unlabeled)} frames with {gemini_model}...")
    for idx, frame_path in enumerate(unlabeled, start=1):
        print(f"  Frame {idx}/{len(unlabeled)}: {frame_path.name}")
        try:
            boxes = detect_objects_gemini(model, frame_path, classes)
        except Exception as exc:
            print(f"    Warning: {exc}")
            boxes = []

        img_w, img_h = read_image_dimensions(frame_path)
        lines: list[str] = []
        for box in boxes:
            if box.class_name not in class_to_id:
                class_to_id[box.class_name] = len(class_to_id)
            cid = class_to_id[box.class_name]
            cx = clamp((box.x + box.width / 2.0) / img_w, 0.0, 1.0)
            cy = clamp((box.y + box.height / 2.0) / img_h, 0.0, 1.0)
            nw = clamp(box.width / img_w, 0.0, 1.0)
            nh = clamp(box.height / img_h, 0.0, 1.0)
            lines.append(f"{cid} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        label_path = frame_path.with_suffix(".txt")
        label_path.write_text("\n".join(lines), encoding="utf-8")

    names = [n for n, _ in sorted(class_to_id.items(), key=lambda x: x[1])]
    class_map_path.write_text("\n".join(names), encoding="utf-8")
    print(f"[gemini] Done. {len(unlabeled)} frames labeled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
