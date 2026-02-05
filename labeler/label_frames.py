from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

from .rules import labeling_rules_excerpt
from .utils import normalize_class

SCHEMA: dict[str, Any] = {
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
}


class LabelError(RuntimeError):
    pass


def image_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise LabelError("No JSON found in model output.")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LabelError("Malformed JSON from model.") from exc


def build_prompt(classes: list[str], rules_path: Path | None = None) -> str:
    rules_text = labeling_rules_excerpt(rules_path)
    prompt = (
        "Detect visible gameplay objects and return tight pixel bounding boxes.\n"
        "Rules:\n"
        "- x,y is top-left in pixels.\n"
        "- width,height are in pixels.\n"
        "- Boxes must tightly enclose only the object (no large background areas).\n"
        "- If uncertain, skip the object.\n"
        f"- Use ONLY these class names: {', '.join(classes)}.\n"
        "- Ignore objects not in that list.\n"
        "- Return JSON only.\n"
    )
    if rules_text:
        prompt += "\nAdditional labeling rules:\n" + rules_text
    return prompt


def detect(
    client: Any,
    model: str,
    image_path: Path,
    *,
    classes: list[str],
    image_detail: str,
    rules_path: Path | None,
) -> list[dict[str, Any]]:
    prompt = build_prompt(classes, rules_path=rules_path)
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64(image_path)}",
                        "detail": image_detail,
                    },
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "detected_objects",
                "strict": True,
                "schema": SCHEMA,
            }
        },
        temperature=0,
    )
    payload = parse_json(response.output_text)
    objects = payload.get("objects", [])
    if not isinstance(objects, list):
        raise LabelError("'objects' must be a list.")

    results: list[dict[str, Any]] = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        try:
            class_name = normalize_class(str(obj["class_name"]))
            if class_name not in classes:
                continue
            box = {
                "class_name": class_name,
                "x": float(obj["x"]),
                "y": float(obj["y"]),
                "width": float(obj["width"]),
                "height": float(obj["height"]),
            }
            if box["width"] < 2.0 or box["height"] < 2.0:
                continue
            results.append(box)
        except (KeyError, TypeError, ValueError):
            continue
    return results


def run_frame_labeling(
    *,
    model: str,
    image_path: Path,
    classes: list[str],
    image_detail: str,
    rules_path: Path | None,
) -> list[dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LabelError("OPENAI_API_KEY is not set.")
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    return detect(
        client,
        model,
        image_path,
        classes=classes,
        image_detail=image_detail,
        rules_path=rules_path,
    )
