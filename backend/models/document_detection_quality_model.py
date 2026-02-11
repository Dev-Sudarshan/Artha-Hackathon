"""
DOCUMENT DETECTION & QUALITY CHECK
---------------------------------
Confirms the uploaded image is an ID document and is usable.

Uses (placeholders / light heuristics):
- MobileNet / EfficientNet classifier
- CLIP zero-shot
- Traditional CV checks (blur, glare, crop)
"""

import os
from dataclasses import dataclass


# =========================
# INPUT DATA STRUCTURE
# =========================

@dataclass
class DocumentQualityInput:
    image_path: str


# =========================
# CORE QUALITY CHECKS
# =========================

def _check_file_exists(image_path: str) -> None:
    if not os.path.exists(image_path):
        raise FileNotFoundError("Uploaded image not found")


def _dummy_classifier_score() -> float:
    # Placeholder score for MobileNet/EfficientNet classifier
    return 0.82


def _dummy_clip_score() -> float:
    # Placeholder score for CLIP zero-shot ("id card" prompt)
    return 0.78


def _simple_quality_flags() -> dict:
    # Placeholder for blur/glare/crop checks
    return {
        "blurred": False,
        "overexposed": False,
        "cropped": False,
        "screenshot_or_photocopy": False,
    }


def verify_document_quality(payload: DocumentQualityInput) -> dict:
    """
    Verify image looks like an ID document and is usable.
    """
    _check_file_exists(payload.image_path)

    classifier_score = _dummy_classifier_score()
    clip_score = _dummy_clip_score()
    quality_flags = _simple_quality_flags()

    is_document = classifier_score >= 0.70 and clip_score >= 0.70
    has_quality_issues = any(quality_flags.values())

    return {
        "is_document": is_document,
        "classifier_score": classifier_score,
        "clip_score": clip_score,
        "quality_flags": quality_flags,
        "final_status": "APPROVED" if is_document and not has_quality_issues else "REJECTED",
    }


# =========================
# LOCAL TEST
# =========================

if __name__ == "__main__":
    sample = DocumentQualityInput(image_path="sample_id.jpg")
    result = verify_document_quality(sample)
    print("DOCUMENT QUALITY RESULT:")
    print(result)
