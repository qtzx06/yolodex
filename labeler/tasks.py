from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .rules import extract_rule_classes
from .utils import ensure_dir, normalize_class, write_json


class TaskError(RuntimeError):
    pass


def load_classes(path: Path | None) -> list[str]:
    if path is None:
        return extract_rule_classes()
    if not path.exists():
        raise TaskError(f"Classes file not found: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        import json

        payload = json.loads(text)
        return [normalize_class(name) for name in payload]
    return [normalize_class(line) for line in text.splitlines() if line.strip()]


def split_frames(frames: list[dict[str, Any]], agents: int) -> list[list[dict[str, Any]]]:
    if agents <= 0:
        raise TaskError("agents must be >= 1")
    if not frames:
        return []
    chunk_size = int(math.ceil(len(frames) / float(agents)))
    return [frames[i : i + chunk_size] for i in range(0, len(frames), chunk_size)]


def create_tasks(
    run_dir: Path,
    frames: list[dict[str, Any]],
    agents: int,
    model: str,
    classes: list[str],
    *,
    image_detail: str = "high",
    rules_path: Path | None = None,
) -> list[Path]:
    task_dir = run_dir / "label_tasks"
    output_dir = run_dir / "labels_json"
    ensure_dir(task_dir)
    ensure_dir(output_dir)

    chunks = split_frames(frames, agents)
    tasks: list[Path] = []
    for idx, chunk in enumerate(chunks):
        task_path = task_dir / f"task_{idx:03d}.json"
        output_path = output_dir / f"agent_{idx:03d}.jsonl"
        payload = {
            "task_id": f"task_{idx:03d}",
            "model": model,
            "classes": classes,
            "frames": chunk,
            "output_path": str(output_path.relative_to(run_dir)),
            "image_detail": image_detail,
            "rules_path": str(rules_path) if rules_path else "",
        }
        write_json(task_path, payload)
        tasks.append(task_path)
    return tasks
