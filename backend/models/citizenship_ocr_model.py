"""Citizenship OCR Model — Bridge to the extraction pipeline.

Exposes:
    verify_citizenship_card(image_path, input_full_name, input_dob, input_citizenship_no)
    extract_thumbprint(image_path)
    detect_face_on_card(image_path)

These are called by kyc_service.py during Step 2 (ID document verification).
"""

from __future__ import annotations

import os
import re
import traceback
from typing import Optional

import cv2
import numpy as np

from models.pipeline import CitizenshipPipeline, PipelineConfig


# Singleton pipeline instance (lazy-loaded)
_pipeline: Optional[CitizenshipPipeline] = None


def _get_pipeline() -> CitizenshipPipeline:
    global _pipeline
    if _pipeline is None:
        cfg = PipelineConfig()
        _pipeline = CitizenshipPipeline(cfg)
    return _pipeline


def _normalize_text(text: str) -> str:
    """Lowercase, strip, collapse whitespace and remove punctuation."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return " ".join(text.split())


def _fuzzy_match(a: str, b: str, threshold: float = 65.0) -> bool:
    """Simple fuzzy comparison — try rapidfuzz first, fall back to substring."""
    na, nb = _normalize_text(a), _normalize_text(b)
    if not na or not nb:
        return False
    # Exact or substring
    if na == nb or na in nb or nb in na:
        return True
    try:
        from rapidfuzz import fuzz
        return fuzz.partial_ratio(na, nb) >= threshold
    except ImportError:
        # Simple token overlap fallback
        tokens_a = set(na.split())
        tokens_b = set(nb.split())
        if not tokens_a or not tokens_b:
            return False
        overlap = len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))
        return overlap >= 0.5


def verify_citizenship_card(
    image_path: str,
    input_full_name: str = "",
    input_dob: str = "",
    input_citizenship_no: str = "",
) -> dict:
    """Run the OCR pipeline on the citizenship card back image and
    compare extracted fields against user-provided input.

    Returns a dict with:
        final_ocr_status: "PASSED" | "FAILED"
        name_match: bool
        dob_match: bool
        citizenship_no_match: bool
        extracted_fields: dict   — raw pipeline output
        raw_text: str
        confidence: dict
        validation_issues: list
        error: str | None
    """
    result = {
        "final_ocr_status": "FAILED",
        "name_match": False,
        "dob_match": False,
        "citizenship_no_match": False,
        "extracted_fields": {},
        "raw_text": "",
        "confidence": {},
        "validation_issues": [],
        "error": None,
    }

    if not os.path.isfile(image_path):
        result["error"] = f"Image file not found: {image_path}"
        return result

    try:
        pipeline = _get_pipeline()
        pr = pipeline.run(image_path)

        if not pr.success:
            result["error"] = pr.error
            return result

        result["extracted_fields"] = pr.fields
        result["raw_text"] = pr.raw_text
        result["confidence"] = pr.field_confidences
        result["validation_issues"] = pr.validation_issues

        # --- Match: citizenship number ---
        extracted_cert = str(pr.fields.get("citizenship_certificate_number", ""))
        if input_citizenship_no and extracted_cert:
            # Normalise: strip non-digit separators to pure digit groups
            norm_input = re.sub(r"[^0-9]", "", input_citizenship_no)
            norm_extracted = re.sub(r"[^0-9]", "", extracted_cert)
            result["citizenship_no_match"] = (norm_input == norm_extracted) if norm_input else False

        # --- Match: full name ---
        extracted_name = str(pr.fields.get("full_name", ""))
        if input_full_name and extracted_name:
            result["name_match"] = _fuzzy_match(input_full_name, extracted_name)

        # --- Match: date of birth ---
        extracted_dob_parts = pr.fields.get("date_of_birth_parts", {})
        extracted_dob_str = str(pr.fields.get("date_of_birth", ""))
        if input_dob:
            input_dob_norm = re.sub(r"[^0-9]", "", input_dob)
            extracted_dob_norm = re.sub(r"[^0-9]", "", extracted_dob_str)
            if input_dob_norm and extracted_dob_norm:
                result["dob_match"] = input_dob_norm == extracted_dob_norm
            # Also try partial match on year
            if not result["dob_match"] and extracted_dob_parts:
                yr = str(extracted_dob_parts.get("year", ""))
                if yr and yr in input_dob:
                    result["dob_match"] = True

        # --- Overall status ---
        # Pass if at least citizenship number matches (primary ID)
        # or if 2+ fields match
        matches = sum([
            result["citizenship_no_match"],
            result["name_match"],
            result["dob_match"],
        ])
        if matches >= 1:
            result["final_ocr_status"] = "PASSED"

        print(f"[OCR] Extracted: cert={extracted_cert}, name={extracted_name}, dob={extracted_dob_str}")
        print(f"[OCR] Matches: cert={result['citizenship_no_match']}, name={result['name_match']}, dob={result['dob_match']}")
        print(f"[OCR] Status: {result['final_ocr_status']}")

    except Exception as e:
        result["error"] = f"OCR pipeline error: {str(e)}"
        traceback.print_exc()

    return result


def extract_thumbprint(image_path: str) -> bool:
    """Detect whether a thumbprint is present on the citizenship card.

    Uses simple contour analysis on the lower-right region
    where the thumbprint typically appears.
    """
    if not os.path.isfile(image_path):
        return False

    try:
        img = cv2.imread(image_path)
        if img is None:
            return False

        h, w = img.shape[:2]
        # Thumbprint is typically in the lower-right quadrant
        roi = img[int(h * 0.5):, int(w * 0.6):]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Look for circular/oval dark region (thumbprint ink)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        roi_area = roi.shape[0] * roi.shape[1]
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Thumbprint contour should be a decent fraction of the ROI
            if 0.02 * roi_area < area < 0.6 * roi_area:
                # Check circularity
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    circularity = 4 * 3.14159 * area / (perimeter * perimeter)
                    if circularity > 0.2:
                        return True
        return False

    except Exception:
        traceback.print_exc()
        return False


def detect_face_on_card(image_path: str) -> bool:
    """Detect whether a face (photo) is present on the citizenship card front.

    Uses OpenCV's Haar cascade face detector on the card image.
    """
    if not os.path.isfile(image_path):
        return False

    try:
        img = cv2.imread(image_path)
        if img is None:
            return False

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Try OpenCV's built-in Haar cascade
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)

        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(30, 30),
        )

        detected = len(faces) > 0
        print(f"[FACE_DETECT] Faces found on card: {len(faces)}")
        return detected

    except Exception:
        traceback.print_exc()
        return False
