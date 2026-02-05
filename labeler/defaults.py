from __future__ import annotations

DEFAULT_CLASSES: list[str] = [
    "player_jake",
    "train",
    "barrier",
    "coin",
    "powerup",
]

PROMPT_TEMPLATE = """
Detect objects for the following classes only: {classes}.

Return strict JSON with pixel boxes.

Schema:
{{
  "objects": [
    {{
      "class_name": "string",
      "x": 0,
      "y": 0,
      "width": 0,
      "height": 0
    }}
  ]
}}

Rules:
- x,y is top-left in pixels.
- width,height are in pixels.
- class_name must match one of the provided classes exactly.
- Return JSON only.
""".strip()
