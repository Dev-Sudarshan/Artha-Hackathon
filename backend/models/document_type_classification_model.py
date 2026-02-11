"""
DOCUMENT TYPE CLASSIFICATION
----------------------------
Identifies which document is uploaded (passport, ID card, license, etc.).

Uses (placeholders):
- CNN classifier (ResNet / EfficientNet)
- CLIP zero-shot prompts
"""

import os
from dataclasses import dataclass


# =========================
# INPUT DATA STRUCTURE
# =========================

@dataclass
class DocumentTypeInput:
    image_path: str


# =========================
# CORE TYPE CLASSIFIER
# =========================

def _check_file_exists(image_path: str) -> None:
    if not os.path.exists(image_path):
        raise FileNotFoundError("Uploaded image not found")


def _dummy_cnn_prediction() -> dict:
    # Placeholder for CNN classifier output
    return {
        "label": "id_card",
        "confidence": 0.81,
    }


def _dummy_clip_prediction() -> dict:
    # Placeholder for CLIP zero-shot prediction
    return {
        "label": "id_card",
        "confidence": 0.76,
    }


def classify_document_type(payload: DocumentTypeInput) -> dict:
    """
    Classify the document type using model ensemble (CNN + CLIP).
    """
    _check_file_exists(payload.image_path)

    cnn_pred = _dummy_cnn_prediction()
    clip_pred = _dummy_clip_prediction()

    final_label = cnn_pred["label"] if cnn_pred["confidence"] >= clip_pred["confidence"] else clip_pred["label"]
    final_confidence = max(cnn_pred["confidence"], clip_pred["confidence"])

    return {
        "document_type": final_label,
        "confidence": final_confidence,
        "cnn": cnn_pred,
        "clip": clip_pred,
    }


# =========================
# LOCAL TEST
# =========================

if __name__ == "__main__":
    sample = DocumentTypeInput(image_path="sample_id.jpg")
    result = classify_document_type(sample)
    print("DOCUMENT TYPE RESULT:")
    print(result)
