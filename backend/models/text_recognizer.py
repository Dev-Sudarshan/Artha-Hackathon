"""Text recognition fallback — EasyOCR / TrOCR / PaddleOCR wrappers.

These are used by the pipeline when the primary PaddleOCR engine is
unavailable and the EasyOCR fallback is selected.
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
class TextRecognizerConfig:
    """Tunable parameters for the recognition module."""
    languages: List[str] = field(default_factory=lambda: ["en", "ne"])
    gpu: bool = False
    min_confidence: float = 0.10


# ---------------------------------------------------------------- result ---

@dataclass
class RecognitionResult:
    text: str = ""
    confidence: float = 0.0
    polygon: Optional[List[List[int]]] = None


# ------------------------------------------------------------ recognizer ---

class TextRecognizer:
    """Thin wrapper around recognition backends."""

    def __init__(self, cfg: Optional[TextRecognizerConfig] = None):
        self.cfg = cfg or TextRecognizerConfig()
        self._reader: Optional[easyocr.Reader] = None

    # ---- EasyOCR ---------------------------------------------------

    def _get_easyocr_reader(self) -> "easyocr.Reader":
        if self._reader is None:
            if easyocr is None:
                raise RuntimeError("easyocr is not installed")
            self._reader = easyocr.Reader(
                self.cfg.languages, gpu=self.cfg.gpu,
            )
        return self._reader

    def _easyocr_recognize(self, image: np.ndarray) -> List[RecognitionResult]:
        """Full detect+recognise pass via EasyOCR."""
        reader = self._get_easyocr_reader()
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        raw = reader.readtext(rgb)
        out: List[RecognitionResult] = []
        for (polygon, text, conf) in raw:
            if conf < self.cfg.min_confidence:
                continue
            pts = [[int(p[0]), int(p[1])] for p in polygon]
            out.append(RecognitionResult(text=text, confidence=conf, polygon=pts))
        return out

    # ---- TrOCR stub ------------------------------------------------

    def _trocr_recognize(self, image: np.ndarray) -> List[RecognitionResult]:
        """TrOCR recognition — currently a stub."""
        raise NotImplementedError("TrOCR backend is not implemented")

    # ---- PaddleOCR stub --------------------------------------------

    def _paddle_recognize(self, image: np.ndarray) -> List[RecognitionResult]:
        """PaddleOCR recognition — currently a stub.

        The main pipeline uses PaddleOCR directly, not through this wrapper.
        """
        raise NotImplementedError("Use pipeline.py PaddleOCR integration instead")

    # ---- public API ------------------------------------------------

    def recognize(self, image: np.ndarray,
                  backend: str = "easyocr") -> List[RecognitionResult]:
        """Recognise text in *image* using the specified backend."""
        if backend == "easyocr":
            return self._easyocr_recognize(image)
        elif backend == "trocr":
            return self._trocr_recognize(image)
        elif backend == "paddleocr":
            return self._paddle_recognize(image)
        else:
            raise ValueError(f"Unknown backend: {backend}")
