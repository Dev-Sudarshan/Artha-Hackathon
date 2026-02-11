"""
TEXT RECOGNITION (OCR STAGE 2)
------------------------------
Convert image text into actual characters.

Models:
- CRNN
- Transformer OCR
- TrOCR
"""

import os
from dataclasses import dataclass


# =========================
# INPUT DATA STRUCTURE
# =========================

@dataclass
class TextRecognitionInput:
    image_path: str


# =========================
# TEXT RECOGNITION
# =========================

def _check_file_exists(image_path: str) -> None:
    if not os.path.exists(image_path):
        raise FileNotFoundError("Uploaded image not found")


def _dummy_recognition_result() -> list:
    # Placeholder output of raw OCR lines
    return [
        "Name: Ram Bahadur Thapa",
        "DOB: 1990-05-12",
        "ID No: 12345678",
        "Gender: M",
        "Address: Kathmandu",
    ]


def recognize_text(payload: TextRecognitionInput) -> dict:
    """
    Recognize text using CRNN/Transformer/TrOCR (placeholder).
    """
    _check_file_exists(payload.image_path)

    lines = _dummy_recognition_result()

    return {
        "raw_text_lines": lines,
        "num_lines": len(lines),
        "model": "TrOCR",
    }


# =========================
# LOCAL TEST
# =========================

if __name__ == "__main__":
    sample = TextRecognitionInput(image_path="sample_id.jpg")
    result = recognize_text(sample)
    print("TEXT RECOGNITION RESULT:")
    print(result)
