"""YOLO detector adapter and threat-side extraction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from ultralytics import YOLO


class ThreatSide(str, Enum):
    NONE = "none"
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) * 0.5

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) * 0.5


@dataclass(frozen=True)
class ThreatObservation:
    side: ThreatSide
    best: Detection | None
    score: float


class YoloThreatDetector:
    """Runs inference and maps detections to a single threat side signal."""

    def __init__(
        self,
        model_path: Path,
        confidence: float,
        imgsz: int,
        threat_classes: list[str],
    ) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Model weights not found at {model_path}")
        self._model = YOLO(str(model_path))
        self._confidence = confidence
        self._imgsz = imgsz
        self._threat_classes = {name.lower() for name in threat_classes}

    def detect(self, frame_bgr: np.ndarray[Any, np.dtype[np.uint8]]) -> list[Detection]:
        results = self._model.predict(
            source=frame_bgr,
            conf=self._confidence,
            imgsz=self._imgsz,
            verbose=False,
        )
        if not results:
            return []

        result = results[0]
        names: dict[int, str] = result.names
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return []

        xyxy = boxes.xyxy.cpu().numpy()
        cls = boxes.cls.cpu().numpy().astype(int)
        conf = boxes.conf.cpu().numpy()

        detections: list[Detection] = []
        for i in range(len(xyxy)):
            cid = int(cls[i])
            x1, y1, x2, y2 = (float(v) for v in xyxy[i])
            detections.append(
                Detection(
                    class_id=cid,
                    class_name=str(names.get(cid, str(cid))).lower(),
                    confidence=float(conf[i]),
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )
        return detections

    def threat_from(self, detections: list[Detection], frame_width: int, frame_height: int) -> ThreatObservation:
        if not detections:
            return ThreatObservation(side=ThreatSide.NONE, best=None, score=0.0)

        considered: list[Detection]
        if self._threat_classes:
            considered = [d for d in detections if d.class_name in self._threat_classes]
        else:
            considered = detections

        if not considered:
            return ThreatObservation(side=ThreatSide.NONE, best=None, score=0.0)

        # Lower objects are generally more urgent for "laser coming down" gameplay.
        def score(det: Detection) -> float:
            y_weight = max(0.0, min(1.0, det.cy / max(frame_height, 1)))
            return det.confidence * (0.35 + y_weight)

        best = max(considered, key=score)
        best_score = score(best)
        side = ThreatSide.LEFT if best.cx < (frame_width * 0.5) else ThreatSide.RIGHT
        return ThreatObservation(side=side, best=best, score=best_score)

