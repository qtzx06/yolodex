"""MSS-based screen capture for gameplay bot input frames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from mss import mss

from shared.game_bot.config import CaptureConfig


@dataclass(frozen=True)
class CaptureRegion:
    left: int
    top: int
    width: int
    height: int


class MSSCapture:
    """Captures frames from a monitor or a configured ROI."""

    def __init__(self, capture_config: CaptureConfig) -> None:
        self._sct = mss()
        self._capture_config = capture_config
        self._region = self._build_region()

    @property
    def region(self) -> CaptureRegion:
        return self._region

    def _build_region(self) -> CaptureRegion:
        monitors = self._sct.monitors
        monitor_index = self._capture_config.monitor_index
        if monitor_index <= 0 or monitor_index >= len(monitors):
            raise ValueError(
                f"Invalid monitor_index={monitor_index}; available indexes are 1..{len(monitors) - 1}"
            )

        monitor = monitors[monitor_index]
        left = self._capture_config.left if self._capture_config.left is not None else int(monitor["left"])
        top = self._capture_config.top if self._capture_config.top is not None else int(monitor["top"])
        width = self._capture_config.width if self._capture_config.width is not None else int(monitor["width"])
        height = self._capture_config.height if self._capture_config.height is not None else int(monitor["height"])

        if width <= 0 or height <= 0:
            raise ValueError("Capture region width/height must be > 0")

        return CaptureRegion(left=left, top=top, width=width, height=height)

    def monitor_info(self) -> list[dict[str, int]]:
        details: list[dict[str, int]] = []
        for idx, monitor in enumerate(self._sct.monitors):
            if idx == 0:
                continue
            details.append(
                {
                    "index": idx,
                    "left": int(monitor["left"]),
                    "top": int(monitor["top"]),
                    "width": int(monitor["width"]),
                    "height": int(monitor["height"]),
                }
            )
        return details

    def grab_bgr(self) -> np.ndarray[Any, np.dtype[np.uint8]]:
        region = {
            "left": self._region.left,
            "top": self._region.top,
            "width": self._region.width,
            "height": self._region.height,
        }
        raw = self._sct.grab(region)
        frame = np.array(raw, dtype=np.uint8)
        return frame[:, :, :3]

    def close(self) -> None:
        self._sct.close()

