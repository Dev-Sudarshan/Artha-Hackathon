"""Text detection fallback — EasyOCR-based.

Used when PaddleOCR is unavailable.  Returns raw detection boxes
for a given image (no recognition — that comes from text_recognizer).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

try:
    import easyocr
except ImportError:
    easyocr = None


# ---------------------------------------------------------------- config ---

@dataclass
class TextDetectorConfig:
    """Tunable parameters for EasyOCR text detection."""
    languages: List[str] = field(default_factory=lambda: ["en", "ne"])
    gpu: bool = False
    min_recognition_confidence: float = 0.10
    suppress_lower_region: bool = False
    suppress_upper_region: bool = False
    lower_region_ratio: float = 0.85
    upper_region_ratio: float = 0.05


# ---------------------------------------------------------------- result ---

@dataclass
class DetectionBox:
    """A single detected text region."""
    polygon: List[List[int]]       # 4-corner polygon [[x1,y1],...]
    text: str = ""
    confidence: float = 0.0


@dataclass
class DetectionResult:
    boxes: List[DetectionBox] = field(default_factory=list)
    image_shape: Tuple[int, int] = (0, 0)
    error: Optional[str] = None


# -------------------------------------------------------------- detector ---

class TextDetector:
    """Detect + recognise text regions via EasyOCR."""

    def __init__(self, cfg: Optional[TextDetectorConfig] = None):
        self.cfg = cfg or TextDetectorConfig()
        self._reader: Optional[easyocr.Reader] = None

    def _get_reader(self) -> "easyocr.Reader":
        if self._reader is None:
            if easyocr is None:
                raise RuntimeError("easyocr is not installed")
            self._reader = easyocr.Reader(
                self.cfg.languages, gpu=self.cfg.gpu,
            )
        return self._reader

    def detect(self, image: np.ndarray) -> DetectionResult:
        """Run detection + recognition on a BGR image array."""
        h, w = image.shape[:2]
        try:
            reader = self._get_reader()
        except RuntimeError as exc:
            return DetectionResult(image_shape=(h, w), error=str(exc))

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = reader.readtext(rgb)

        boxes: List[DetectionBox] = []
        for (polygon, text, conf) in results:
            if conf < self.cfg.min_recognition_confidence:
                continue

            # polygon is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            pts = [[int(p[0]), int(p[1])] for p in polygon]
            cy = sum(p[1] for p in pts) / 4.0

            if self.cfg.suppress_lower_region and cy > h * self.cfg.lower_region_ratio:
                continue
            if self.cfg.suppress_upper_region and cy < h * self.cfg.upper_region_ratio:
                continue

            boxes.append(DetectionBox(polygon=pts, text=text, confidence=conf))

        return DetectionResult(boxes=boxes, image_shape=(h, w))
