#!/usr/bin/env python3
"""CUA + SAM labeling: CUA clicks on objects for coordinates, SAM segments for precise bboxes."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from openai import OpenAI
from ultralytics import SAM

from shared.utils import (
    BoundingBox,
    PipelineError,
    encode_image_base64,
    load_config,
    read_image_dimensions,
)


def get_cua_clicks(
    client: OpenAI, frame_path: Path, class_name: str, img_w: int, img_h: int
) -> list[tuple[int, int]]:
    """Use CUA to click on all instances of a class in the frame."""
    image_b64 = encode_image_base64(frame_path)
    clicks: list[tuple[int, int]] = []

    response = client.responses.create(
        model="computer-use-preview",
        tools=[
            {
                "type": "computer_use_preview",
                "display_width": img_w,
                "display_height": img_h,
                "environment": "browser",
            }
        ],
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"This is a game screenshot. Click on every '{class_name}' "
                            f"you can see, one at a time. Start with the first one."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}",
                    },
                ],
            }
        ],
        truncation="auto",
    )

    # Extract click coordinates from the response
    for item in response.output:
        if getattr(item, "type", None) == "computer_call":
            action = item.action
            if getattr(action, "type", None) == "click":
                x, y = int(action.x), int(action.y)
                if 0 <= x <= img_w and 0 <= y <= img_h:
                    clicks.append((x, y))

    # If CUA returned a click, loop to get more instances
    max_passes = 10
    pass_count = 0
    while clicks and pass_count < max_passes:
        pass_count += 1
        response_id = response.id

        # Send back the same screenshot, ask for more
        try:
            # Build computer_call_output for each pending call
            pending_calls = [
                item for item in response.output
                if getattr(item, "type", None) == "computer_call"
            ]
            if not pending_calls:
                break

            call_id = pending_calls[-1].call_id
            response = client.responses.create(
                model="computer-use-preview",
                previous_response_id=response_id,
                tools=[
                    {
                        "type": "computer_use_preview",
                        "display_width": img_w,
                        "display_height": img_h,
                        "environment": "browser",
                    }
                ],
                input=[
                    {
                        "type": "computer_call_output",
                        "call_id": call_id,
                        "output": {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{image_b64}",
                        },
                    }
                ],
                truncation="auto",
            )

            found_new = False
            for item in response.output:
                if getattr(item, "type", None) == "computer_call":
                    action = item.action
                    if getattr(action, "type", None) == "click":
                        x, y = int(action.x), int(action.y)
                        if 0 <= x <= img_w and 0 <= y <= img_h:
                            # Skip if too close to existing click (same object)
                            if all(abs(x - cx) > 20 or abs(y - cy) > 20 for cx, cy in clicks):
                                clicks.append((x, y))
                                found_new = True
            if not found_new:
                break
        except Exception:
            break

    return clicks


def sam_point_to_bbox(
    sam_model: SAM, frame_path: Path, point: tuple[int, int], img_w: int, img_h: int
) -> BoundingBox | None:
    """Use SAM to segment from a point prompt, return bounding box."""
    results = sam_model(str(frame_path), points=[list(point)], labels=[1])

    if not results or not results[0].masks or len(results[0].masks.data) == 0:
        return None

    mask = results[0].masks.data[0].cpu().numpy()
    coords = np.where(mask > 0)
    if len(coords[0]) == 0:
        return None

    y_min, y_max = int(coords[0].min()), int(coords[0].max())
    x_min, x_max = int(coords[1].min()), int(coords[1].max())

    return BoundingBox(
        class_name="",  # filled in by caller
        x=float(x_min),
        y=float(y_min),
        width=float(x_max - x_min),
        height=float(y_max - y_min),
    )


def label_frame_cua_sam(
    client: OpenAI,
    sam_model: SAM,
    frame_path: Path,
    classes: list[str],
) -> list[BoundingBox]:
    """Label a single frame using CUA for clicks + SAM for segmentation."""
    img_w, img_h = read_image_dimensions(frame_path)
    all_boxes: list[BoundingBox] = []

    for class_name in classes:
        clicks = get_cua_clicks(client, frame_path, class_name, img_w, img_h)
        print(f"    CUA found {len(clicks)} '{class_name}' instances")

        for point in clicks:
            box = sam_point_to_bbox(sam_model, frame_path, point, img_w, img_h)
            if box is not None:
                box.class_name = class_name.strip().lower().replace(" ", "_")
                all_boxes.append(box)

    return all_boxes


def main() -> int:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    config = load_config()
    classes = config.get("classes", [])
    if not classes:
        print("Error: CUA+SAM mode requires explicit classes in config.json.", file=sys.stderr)
        return 1

    output_dir = Path(config.get("output_dir", "output"))
    frames_dir = output_dir / "frames"
    sam_model_name = config.get("sam_model", "sam2_b.pt")

    frames = sorted(frames_dir.glob("*.jpg"))
    if not frames:
        print("Error: No frames found. Run the collect skill first.", file=sys.stderr)
        return 1

    unlabeled = [f for f in frames if not f.with_suffix(".txt").exists()]
    if not unlabeled:
        print("[cua+sam] All frames already labeled.")
        return 0

    client = OpenAI(api_key=api_key)
    print(f"[cua+sam] Loading SAM model: {sam_model_name}...")
    sam_model = SAM(sam_model_name)

    # Build class map
    from shared.utils import clamp
    class_to_id: dict[str, int] = {}
    class_map_path = output_dir / "classes.txt"
    if class_map_path.exists():
        for idx, name in enumerate(class_map_path.read_text().strip().split("\n")):
            if name:
                class_to_id[name] = idx

    # Pre-populate from config classes
    for cls in classes:
        key = cls.strip().lower().replace(" ", "_")
        if key not in class_to_id:
            class_to_id[key] = len(class_to_id)

    print(f"[cua+sam] Labeling {len(unlabeled)} frames with CUA + SAM...")
    for idx, frame_path in enumerate(unlabeled, start=1):
        print(f"  Frame {idx}/{len(unlabeled)}: {frame_path.name}")
        try:
            boxes = label_frame_cua_sam(client, sam_model, frame_path, classes)
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

    # Write class map
    names = [n for n, _ in sorted(class_to_id.items(), key=lambda x: x[1])]
    class_map_path.write_text("\n".join(names), encoding="utf-8")
    print(f"[cua+sam] Done. {len(unlabeled)} frames labeled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
