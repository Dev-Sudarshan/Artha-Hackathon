"""Layout analysis utilities.

Provides LayoutBox (individual OCR detection), LayoutLine (row grouping),
LayoutResult (aggregate summary), and LayoutAnalyzer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ---------------------------------------------------------------- box ---

@dataclass
class LayoutBox:
    """A single detected text region with its bounding rectangle,
    centre point, OCR text, confidence and semantic role.
    """
    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0
    cx: float = 0.0
    cy: float = 0.0
    text: str = ""
    confidence: float = 0.0
    role: str = ""                  # LABEL / VALUE / NOISE — set by semantic extractor
    box_points: Optional[List[List[float]]] = None  # original 4-corner polygon

    @classmethod
    def from_box_points(cls, pts, text: str, conf: float) -> "LayoutBox":
        """Create a LayoutBox from a 4-corner polygon ``[[x1,y1],…,[x4,y4]]``.

        Computes the axis-aligned bounding rectangle and centre.
        """
        arr = np.array(pts, dtype=np.float64)
        x_min, y_min = arr.min(axis=0)
        x_max, y_max = arr.max(axis=0)
        return cls(
            x0=float(x_min), y0=float(y_min),
            x1=float(x_max), y1=float(y_max),
            cx=float((x_min + x_max) / 2),
            cy=float((y_min + y_max) / 2),
            text=text,
            confidence=conf,
            box_points=[list(map(float, p)) for p in pts],
        )


# --------------------------------------------------------------- line ---

@dataclass
class LayoutLine:
    """A group of boxes on the same text row, sorted left-to-right."""
    boxes: List[LayoutBox] = field(default_factory=list)
    y_centre: float = 0.0


# ------------------------------------------------------------- result ---

@dataclass
class LayoutResult:
    """Aggregate layout information."""
    all_boxes: List[LayoutBox] = field(default_factory=list)
    lines: List[LayoutLine] = field(default_factory=list)
    avg_box_height: float = 0.0
    avg_box_width: float = 0.0


# ----------------------------------------------------------- analyzer ---

class LayoutAnalyzer:
    """Compute layout statistics and line groupings from a list of boxes."""

    def analyze(self, boxes: List[LayoutBox]) -> LayoutResult:
        if not boxes:
            return LayoutResult()

        heights = [b.y1 - b.y0 for b in boxes]
        widths = [b.x1 - b.x0 for b in boxes]
        avg_h = float(np.mean(heights)) if heights else 0.0
        avg_w = float(np.mean(widths)) if widths else 0.0

        # Group into lines by y-centre clustering
        row_tol = avg_h * 0.6 if avg_h > 0 else 10.0
        sorted_boxes = sorted(boxes, key=lambda b: b.cy)
        lines: List[LayoutLine] = []
        cur_line: List[LayoutBox] = []
        cur_y = -1e9
        for b in sorted_boxes:
            if abs(b.cy - cur_y) > row_tol and cur_line:
                line_y = float(np.mean([bb.cy for bb in cur_line]))
                cur_line.sort(key=lambda bb: bb.cx)
                lines.append(LayoutLine(boxes=cur_line, y_centre=line_y))
                cur_line = []
            cur_line.append(b)
            cur_y = b.cy if not cur_line or len(cur_line) == 1 else np.mean([bb.cy for bb in cur_line])
        if cur_line:
            line_y = float(np.mean([bb.cy for bb in cur_line]))
            cur_line.sort(key=lambda bb: bb.cx)
            lines.append(LayoutLine(boxes=cur_line, y_centre=line_y))

        return LayoutResult(
            all_boxes=list(boxes),
            lines=lines,
            avg_box_height=avg_h,
            avg_box_width=avg_w,
        )
