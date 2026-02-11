"""
CITIZENSHIP OCR VERIFICATION MODEL
---------------------------------
- Extracts text from citizenship card using Tesseract
- Matches OCR text with Page-1 user input
- Returns ONLY verification flags (no raw OCR text leakage)
"""

import re

import cv2
import pytesseract
from difflib import SequenceMatcher

# =========================
# OCR (TESSERACT)
# =========================

def _ocr_lines_tesseract(image_path: str) -> list:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to read image for OCR")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    try:
        text = pytesseract.image_to_string(thresh, lang="nep+eng")
    except pytesseract.TesseractNotFoundError as e:
        raise Exception("Tesseract OCR not installed or not on PATH") from e

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


def extract_ocr_fields(image_path: str) -> dict:
    ocr_texts = _ocr_lines_tesseract(image_path)
    normalized_lines = [normalize_text(t) for t in ocr_texts]
    paired_lines = [
        {"raw": raw, "norm": norm}
        for raw, norm in zip(ocr_texts, normalized_lines)
    ]

    ocr_name = extract_name(paired_lines)
    ocr_dob = extract_date_of_birth(paired_lines)
    ocr_cit_no = extract_citizenship_number(paired_lines)

    return {
        "raw_lines": ocr_texts,
        "normalized_lines": normalized_lines,
        "name": ocr_name,
        "dob": ocr_dob,
        "citizenship_no": ocr_cit_no,
    }


# =========================
# NORMALIZATION UTILITIES
# =========================

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


# =========================
# FIELD EXTRACTION
# =========================

_MONTH_MAP = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "sept": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def _extract_after_label(raw: str, labels: list[str]) -> str | None:
    lowered = raw.lower()
    for label in labels:
        if label in lowered:
            if ":" in raw:
                return raw.split(":", 1)[1].strip()
            return re.sub(label, "", lowered).strip()
    return None


def extract_citizenship_number(lines):
    keyword_matches = []
    fallback_matches = []

    for line in lines:
        norm = line["norm"]
        raw = line["raw"]

        has_keyword = "citizen" in norm or "citizeaship" in norm or "certificate" in norm
        if has_keyword:
            matches = re.findall(r"\d[\d\-/]{6,}", raw)
            if matches:
                keyword_matches.extend(matches)

        if not has_keyword:
            matches = re.findall(r"\d[\d\-/]{7,}", raw)
            if matches:
                fallback_matches.extend(matches)

    if keyword_matches:
        return keyword_matches[0]
    if fallback_matches:
        return fallback_matches[0]
    return None


def extract_date_of_birth(lines):
    dob_lines = [line for line in lines if "date of birth" in line["norm"] or "dob" in line["norm"]]
    day_line = next((line for line in lines if line["norm"].startswith("day ") or "day" in line["norm"]), None)

    for line in dob_lines:
        raw = line["raw"]
        year_match = re.search(r"(19|20)\d{2}", raw)
        year = year_match.group(0) if year_match else None

        month = None
        month_match = re.search(r"month[:\s-]*([A-Za-z]{3,}|\d{1,2})", raw, re.IGNORECASE)
        if month_match:
            month_val = month_match.group(1).strip().lower()
            if month_val.isdigit():
                month = month_val.zfill(2)
            else:
                month = _MONTH_MAP.get(month_val[:4], _MONTH_MAP.get(month_val[:3]))

        day = None
        day_match = re.search(r"day[:\s-]*(\d{1,2})", raw, re.IGNORECASE)
        if day_match:
            day = day_match.group(1).zfill(2)
        elif day_line:
            day_inline = re.search(r"(\d{1,2})", day_line["raw"])
            if day_inline:
                day = day_inline.group(1).zfill(2)

        if year and month and day:
            return f"{year}-{month}-{day}"

    return None


def extract_name(lines):
    for line in lines:
        norm = line["norm"]
        raw = line["raw"]
        if "name" in norm and "father" not in norm and "mother" not in norm and "certificate" not in norm:
            extracted = _extract_after_label(raw, ["full name", "fall name", "name"])
            if extracted:
                return extracted.strip()

    stop_words = [
        "certificate",
        "address",
        "district",
        "ward",
        "place",
        "date of birth",
        "birth",
        "sex",
    ]

    candidates = []
    for line in lines:
        norm = line["norm"]
        if any(word in norm for word in stop_words):
            continue
        if len(norm) > 5 and not re.search(r"\d", norm):
            candidates.append(line["raw"])

    return max(candidates, key=len) if candidates else None


def extract_thumbprint(image_path: str) -> bool:
    """
    Mock thumbprint detection from back image
    """
    # In a real system, use OpenCV to detect fingerprint patterns
    return True # Simulate detection


def detect_face_on_card(image_path: str) -> bool:
    """
    Verify a face exists on the ID card
    """
    try:
        from models.face_pipeline import detect_faces

        faces = detect_faces(image_path)
        return len(faces) > 0
    except Exception:
        return False


# =========================
# MAIN VERIFICATION FUNCTION
# =========================

def verify_citizenship_card(
    image_path: str,
    input_full_name: str,
    input_dob: str,
    input_citizenship_no: str,
) -> dict:
    """
    OCR + verification against Page-1 user input
    """

    # 1️⃣ OCR extraction
    ocr_fields = extract_ocr_fields(image_path)
    ocr_name = ocr_fields["name"]
    ocr_dob = ocr_fields["dob"]
    ocr_cit_no = ocr_fields["citizenship_no"]

    # 3️⃣ Normalize user input
    input_name_norm = normalize_text(input_full_name)
    input_dob_norm = normalize_text(input_dob)
    input_cit_no_norm = normalize_text(input_citizenship_no)

    # 4️⃣ Matching rules
    name_match = (
        similarity(normalize_text(ocr_name), input_name_norm) >= 0.85
        if ocr_name else False
    )

    dob_match = (
        normalize_text(ocr_dob) == input_dob_norm
        if ocr_dob else False
    )

    cit_no_match = (
        normalize_text(ocr_cit_no) == input_cit_no_norm
        if ocr_cit_no else False
    )

    # 5️⃣ Final OCR decision
    final_status = name_match and dob_match and cit_no_match

    return {
        "name_match": name_match,
        "dob_match": dob_match,
        "citizenship_no_match": cit_no_match,
        "final_ocr_status": "PASSED" if final_status else "FAILED",
    }


# =========================
# LOCAL TEST
# =========================

if __name__ == "__main__":
    result = verify_citizenship_card(
        image_path="citizenship_front.jpg",
        input_full_name="Ram Bahadur Thapa",
        input_dob="1990-05-12",
        input_citizenship_no="12345678",
    )

    print("OCR RESULT:")
    print(result)
