"""Shared gameplay bot types that avoid heavy runtime imports."""

from __future__ import annotations

from enum import Enum


class ThreatSide(str, Enum):
    NONE = "none"
    LEFT = "left"
    RIGHT = "right"

