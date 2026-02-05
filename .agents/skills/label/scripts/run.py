#!/usr/bin/env python3
"""Label skill (single-agent mode): label frames sequentially with class-wise GPT vision calls."""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

# Ensure repo root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from openai import OpenAI

from shared.utils import (
    BoundingBox,
    PipelineError,
    clamp,
    encode_image_base64,
    extract_json_from_text,
    load_config,
    read_image_dimensions,
)

MULTI_CLASS_PROMPT_TEMPLATE = """
Detect every visible object in this image and return bounding boxes.
{class_hint}
Rules:
- x,y,width,height must be pixel values in the original image.
- x,y is top-left corner.
- Include all salient objects.
""".strip()

SINGLE_CLASS_PROMPT_TEMPLATE = """
Detect only objects of class "{class_name}" in this image and return bounding boxes.
Rules:
- Return only "{class_name}" objects. Ignore every other class.
- If no "{class_name}" is visible, return an empty list.
- x,y,width,height must be pixel values in the original image.
- x,y is top-left corner.
""".strip()

# Structured output schema — the API enforces this, no more JSON parsing failures
RESPONSE_SCHEMA = {
    "type": "json_schema",
    "name": "bounding_boxes",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "objects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "class_name": {"type": "string"},
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                        "width": {"type": "number"},
                        "height": {"type": "number"},
                    },
                    "required": ["class_name", "x", "y", "width", "height"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["objects"],
        "additionalProperties": False,
    },
}


def build_prompt(classes: list[str]) -> str:
    if classes:
        hint = f"Focus on these classes: {', '.join(classes)}."
    else:
        hint = "Include all salient objects (people, vehicles, UI elements, weapons, items, enemies, etc.)."
    return MULTI_CLASS_PROMPT_TEMPLATE.format(class_hint=hint)


def build_single_class_prompt(class_name: str) -> str:
    return SINGLE_CLASS_PROMPT_TEMPLATE.format(class_name=class_name)


def detect_objects(client: OpenAI, model: str, frame_path: Path, prompt: str) -> list[BoundingBox]:
    image_b64 = encode_image_base64(frame_path)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}",
                    },
                ],
            }
        ],
        text={"format": RESPONSE_SCHEMA},
    )

    payload = extract_json_from_text(response.output_text)
    objects = payload.get("objects", [])

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


def detect_objects_for_class(
    client: OpenAI,
    model: str,
    frame_path: Path,
    class_name: str,
) -> list[BoundingBox]:
    prompt = build_single_class_prompt(class_name)
    boxes = detect_objects(client, model, frame_path, prompt)
    normalized_name = class_name.strip().lower().replace(" ", "_")
    return [
        BoundingBox(
            class_name=normalized_name,
            x=box.x,
            y=box.y,
            width=box.width,
            height=box.height,
        )
        for box in boxes
    ]


def to_yolo_line(box: BoundingBox, class_id: int, img_w: int, img_h: int) -> str:
    x = clamp(box.x, 0.0, float(img_w))
    y = clamp(box.y, 0.0, float(img_h))
    w = clamp(box.width, 0.0, float(img_w))
    h = clamp(box.height, 0.0, float(img_h))

    center_x = clamp((x + (w / 2.0)) / float(img_w), 0.0, 1.0)
    center_y = clamp((y + (h / 2.0)) / float(img_h), 0.0, 1.0)
    norm_w = clamp(w / float(img_w), 0.0, 1.0)
    norm_h = clamp(h / float(img_h), 0.0, 1.0)

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
    names = [name for name, _ in sorted(class_to_id.items(), key=lambda item: item[1])]
    output_path.write_text("\n".join(names), encoding="utf-8")


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    config = load_config()
    model = config.get("model", "gpt-5-nano")
    classes = config.get("classes", [])
    output_dir = Path(config.get("output_dir", "output"))
    frames_dir = output_dir / "frames"

    frames = sorted(frames_dir.glob("*.jpg"))
    if not frames:
        print("Error: No frames found. Run the collect skill first.", file=sys.stderr)
        return 1

    # Skip already-labeled frames
    unlabeled = [f for f in frames if not f.with_suffix(".txt").exists()]
    if not unlabeled:
        print("[label] All frames already labeled.")
        return 0

    client = OpenAI(api_key=api_key)
    fallback_prompt = build_prompt(classes) if not classes else ""
    class_to_id: dict[str, int] = {}

    # Load existing class map if present
    class_map_path = output_dir / "classes.txt"
    if class_map_path.exists():
        for idx, name in enumerate(class_map_path.read_text().strip().split("\n")):
            if name:
                class_to_id[name] = idx
    elif classes:
        for class_name in classes:
            normalized = str(class_name).strip().lower().replace(" ", "_")
            if normalized and normalized not in class_to_id:
                class_to_id[normalized] = len(class_to_id)

    print(f"[label] Labeling {len(unlabeled)} frames with {model}...")
    try:
        for idx, frame_path in enumerate(unlabeled, start=1):
            print(f"  - Frame {idx}/{len(unlabeled)}: {frame_path.name}")
            if classes:
                boxes: list[BoundingBox] = []
                for class_name in classes:
                    boxes.extend(detect_objects_for_class(client, model, frame_path, str(class_name)))
            else:
                boxes = detect_objects(client, model, frame_path, fallback_prompt)
            write_yolo_labels(frame_path, boxes, class_to_id)
    except PipelineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    write_class_map(class_to_id, class_map_path)
    print(f"[label] Done. {len(unlabeled)} frames labeled. Classes: {class_map_path}")
    _maybe_generate_previews(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def _maybe_generate_previews(output_dir: Path) -> None:
    frames_dir = output_dir / "frames"
    classes_path = output_dir / "classes.txt"
    if not frames_dir.exists() or not classes_path.exists():
        return

    preview_dir = frames_dir / "preview"
    video_out = preview_dir / "preview.mp4"

    cmd = [
        "uv",
        "run",
        ".agents/skills/eval/scripts/preview_labels.py",
        str(frames_dir),
        "--classes",
        str(classes_path),
        "--out-dir",
        str(preview_dir),
        "--limit",
        "0",
        "--video-out",
        str(video_out),
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[label] Warning: preview generation failed ({exc})", file=sys.stderr)
