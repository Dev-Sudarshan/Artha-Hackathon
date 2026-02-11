"""
TEXT DETECTION (OCR STAGE 1)
----------------------------
Locate text regions in the image.

Industry-standard models:
- DBNet
- CRAFT
- EAST
"""

import os
from dataclasses import dataclass


# =========================
# INPUT DATA STRUCTURE
# =========================

@dataclass
class TextDetectionInput:
    image_path: str


# =========================
# TEXT DETECTION
# =========================

def _check_file_exists(image_path: str) -> None:
    if not os.path.exists(image_path):
        raise FileNotFoundError("Uploaded image not found")


def _dummy_text_boxes() -> list:
    # Placeholder list of bounding boxes: [x1, y1, x2, y2]
    return [
        [40, 60, 320, 120],
        [40, 140, 300, 190],
        [40, 220, 260, 260],
    ]


def detect_text_regions(payload: TextDetectionInput) -> dict:
    """
    Detect text regions using DBNet/CRAFT/EAST (placeholder).
    """
    _check_file_exists(payload.image_path)

    boxes = _dummy_text_boxes()

    return {
        "text_boxes": boxes,
        "num_boxes": len(boxes),
        "model": "DBNet",
    }


# =========================
# LOCAL TEST
# =========================

if __name__ == "__main__":
    sample = TextDetectionInput(image_path="sample_id.jpg")
    result = detect_text_regions(sample)
    print("TEXT DETECTION RESULT:")
    print(result)
