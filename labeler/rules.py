from __future__ import annotations

import re
from pathlib import Path

from .defaults import DEFAULT_CLASSES
from .utils import normalize_class


def default_rules_path() -> Path:
    return Path(__file__).resolve().parent / "LABELING_RULES.md"


def load_rule_text(path: Path | None = None) -> str:
    rules_path = path or default_rules_path()
    if not rules_path.exists():
        return ""
    return rules_path.read_text(encoding="utf-8")


def extract_rule_classes(path: Path | None = None) -> list[str]:
    text = load_rule_text(path)
    if not text:
        return list(DEFAULT_CLASSES)

    in_section = False
    classes: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and "Class Definitions" in stripped:
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section:
            match = re.match(r"-\s+`([^`]+)`", stripped)
            if match:
                classes.append(normalize_class(match.group(1)))

    return classes or list(DEFAULT_CLASSES)


def labeling_rules_excerpt(path: Path | None = None) -> str:
    text = load_rule_text(path)
    if not text:
        return ""

    lines: list[str] = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## Global Rules"):
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if in_section and stripped:
            lines.append(stripped)

    if not lines:
        return ""
    return "\n".join(lines)
