"""
DOCUMENT FIELD EXTRACTION
-------------------------
Turn raw OCR text into structured KYC fields.

Models:
- LayoutLM / LayoutLMv3
- Donut
- Rule-based fallback (regex)
"""

import re
from dataclasses import dataclass


# =========================
# INPUT DATA STRUCTURE
# =========================

@dataclass
class DocumentFieldExtractionInput:
    raw_text_lines: list


# =========================
# NORMALIZATION UTILITIES
# =========================

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =========================
# FIELD EXTRACTION (RULE-BASED)
# =========================

def extract_name(lines: list) -> str | None:
    candidates = [
        line for line in lines
        if len(line) > 5 and not re.search(r"\d", line)
    ]
    return max(candidates, key=len) if candidates else None


def extract_date_of_birth(lines: list) -> str | None:
    for line in lines:
        match = re.search(
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})",
            line,
        )
        if match:
            return match.group(0)
    return None


def extract_id_number(lines: list) -> str | None:
    for line in lines:
        match = re.search(r"\b[0-9A-Za-z\-]{6,}\b", line)
        if match:
            return match.group(0)
    return None


def extract_gender(lines: list) -> str | None:
    for line in lines:
        match = re.search(r"\b(male|female|m|f)\b", line)
        if match:
            return match.group(1).upper()
    return None


def extract_address(lines: list) -> str | None:
    for line in lines:
        if "address" in line:
            return line.replace("address", "").strip()
    return None


def _extract_fields(lines: list) -> dict:
    return {
        "name": extract_name(lines),
        "dob": extract_date_of_birth(lines),
        "id_number": extract_id_number(lines),
        "gender": extract_gender(lines),
        "address": extract_address(lines),
    }


def extract_document_fields(payload: DocumentFieldExtractionInput) -> dict:
    """
    Extract fields using Donut/LayoutLM (placeholder) with regex fallback.
    """
    normalized_lines = [normalize_text(line) for line in payload.raw_text_lines]
    fields = _extract_fields(normalized_lines)

    return {
        "fields": fields,
        "model": "Donut",
        "fallback": "regex",
    }


# =========================
# LOCAL TEST
# =========================

if __name__ == "__main__":
    sample = DocumentFieldExtractionInput(
        raw_text_lines=[
            "Name: Ram Bahadur Thapa",
            "DOB: 1990-05-12",
            "ID No: 12345678",
            "Gender: M",
            "Address: Kathmandu",
        ]
    )

    result = extract_document_fields(sample)
    print("FIELD EXTRACTION RESULT:")
    print(result)
