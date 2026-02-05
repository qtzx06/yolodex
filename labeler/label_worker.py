from __future__ import annotations

import json
import os
from pathlib import Path
from .label_frames import LabelError, detect
from .utils import normalize_class, read_image_dimensions


def run_task(task_path: Path, run_dir: Path) -> Path:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LabelError("OPENAI_API_KEY is not set.")

    task = json.loads(task_path.read_text(encoding="utf-8"))
    model = task["model"]
    classes = [normalize_class(name) for name in task["classes"]]
    frames = task["frames"]
    output_path = run_dir / task["output_path"]
    image_detail = str(task.get("image_detail", "high"))
    rules_path_raw = task.get("rules_path")
    rules_path = Path(rules_path_raw) if isinstance(rules_path_raw, str) and rules_path_raw else None

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    lines: list[str] = []
    for idx, frame in enumerate(frames, start=1):
        image_path = run_dir / frame["image_path"]
        print(f"Labeling {idx}/{len(frames)}: {image_path.name}")
        width, height = read_image_dimensions(image_path)
        boxes = detect(
            client,
            model,
            image_path,
            classes=classes,
            image_detail=image_detail,
            rules_path=rules_path,
        )
        payload = {
            "image_path": frame["image_path"],
            "width": width,
            "height": height,
            "boxes": boxes,
        }
        lines.append(json.dumps(payload))

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
