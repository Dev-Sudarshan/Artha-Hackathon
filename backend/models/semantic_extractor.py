"""Phase 3 — Semantic Extraction & Field Mapping.

Takes LayoutResult (boxes from OCR) on the canonical 1200×600 image and
extracts structured fields:
  - citizenship_certificate_number
  - sex
  - full_name
  - date_of_birth  (year / month / day)
  - birth_place    (district / municipality / ward)
  - permanent_address (district / municipality / ward)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None  # type: ignore

from models.layout_analyzer import LayoutBox, LayoutLine, LayoutResult
from models.nepal_geography import (
    fuzzy_match_district,
    fuzzy_match_municipality,
    validate_district,
    validate_municipality,
)


# ---------------------------------------------------------------- config ---

@dataclass
class SemanticConfig:
    """Tunable parameters for field extraction."""
    label_fuzzy_threshold: float = 70.0
    row_y_tolerance_factor: float = 1.0
    right_max_distance_factor: float = 0.70
    below_max_gap_factor: float = 2.5
    below_x_align_tolerance: float = 0.8
    noise_max_chars: int = 2
    noise_min_confidence: float = 0.30


# ----------------------------------------------------- canonical anchors ---

# Expected Y-band (fraction of canonical_height) for each field label.
# Format: (y_min_frac, y_max_frac) — labels outside this band are penalised.
CANONICAL_ANCHORS: Dict[str, Tuple[float, float]] = {
    "cert_no":           (0.00, 0.35),
    "sex":               (0.00, 0.40),
    "full_name":         (0.00, 0.45),
    "dob":               (0.05, 0.65),
    "birth_place":       (0.10, 0.85),
    "permanent_address": (0.20, 1.00),
}


# ------------------------------------------------------- label patterns ---

# Each field has a list of text patterns (substrings / fuzzy targets) that
# identify its label on the card.
LABEL_PATTERNS: Dict[str, List[str]] = {
    "cert_no": [
        "citizenship certificate no",
        "citizenship certicate no",        # common OCR typo
        "citizenship certificale no",
        "certificate no",
        "certicate no",
        "cert no",
        "certificate number",
    ],
    "sex": [
        "sex",
    ],
    "full_name": [
        "full name",
        "fullname",
        "name",
    ],
    "dob": [
        "date of birth",
        "date of bith",
        "dale of birth",
        "date ofbirth",
        "date of birth (ad)",
        "birth(ad)",
        "birth (ad)",
        "d.o.b",
        "dob",
    ],
    "birth_place": [
        "birth place",
        "birthplace",
        "place of birth",
    ],
    "permanent_address": [
        "permanent address",
        "permanent adress",
        "permanentaddress",
    ],
}

# Sub-field labels for structured sections
DOB_SUBLABELS: Dict[str, List[str]] = {
    "year":  ["year", "yr"],
    "month": ["month", "mon"],
    "day":   ["day", "dy"],
}

ADDR_SUBLABELS: Dict[str, List[str]] = {
    "district":     ["district", "dist", "disrict"],
    "municipality": ["municipality", "r m", "r.m.", "r.m",
                     "rural municipality",
                     "metro", "metropolitan", "metropolit",
                     "sub metropolitan", "sub-metropolitan",
                     "sub metropolit", "sub-metropolit",
                     "muncipality", "municipallty",
                     "municipaity", "v.d.c", "vdc", "gaupalika",
                     "nagarpalika"],
    "ward":         ["ward no", "ward", "w.no", "wno"],
}


# --------------------------------------------------- validation helpers ---

CERT_NO_RE = re.compile(r"(\d{1,5}[-/]\d{1,5}(?:[-/]\d{1,5})+)")
# More lenient pattern: allows OCR noise (spaces, dots) between digit groups
CERT_NO_LOOSE_RE = re.compile(
    r"(\d{1,5})\s*[-/.\s]\s*(\d{1,5})\s*[-/.\s]\s*(\d{1,5})\s*[-/.\s]\s*(\d{1,6})"
)
SEX_ENUM = {"male", "female", "other"}
_SEX_ORDERED = ["female", "male", "other"]   # check "female" before "male"

YEAR_RE = re.compile(r"((?:19|20)\d{2})")
DAY_RE = re.compile(r"(\d{1,2})")
WARD_RE = re.compile(r"(\d{1,3})")

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct",
    "nov", "dec",
    "baisakh", "jestha", "ashadh", "shrawan", "bhadra", "ashwin",
    "kartik", "mangsir", "poush", "magh", "falgun", "chaitra",
]


# -------------------------------------------------- Devanagari digits ---

_DEVANAGARI_DIGITS = "".join(chr(0x0966 + i) for i in range(10))
_DEVANAGARI_MAP = str.maketrans(_DEVANAGARI_DIGITS, "0123456789")


# ----------------------------------------------------------- results ---

@dataclass
class AnchorInfo:
    field_key: str = ""
    label_box: Optional[LayoutBox] = None
    label_text: str = ""
    match_score: float = 0.0


@dataclass
class ValidationIssue:
    field: str = ""
    severity: str = "warning"   # "warning" | "error"
    message: str = ""


@dataclass
class SemanticResult:
    fields: Dict[str, Any] = field(default_factory=dict)
    field_confidences: Dict[str, float] = field(default_factory=dict)
    anchors: Dict[str, AnchorInfo] = field(default_factory=dict)
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    flags_for_review: List[str] = field(default_factory=list)
    box_roles: Dict[str, str] = field(default_factory=dict)  # box_text → role


# -------------------------------------------------------------- helpers ---

def _devanagari_to_ascii(text: str) -> str:
    """Translate Devanagari digits (U+0966…U+096F) to ASCII 0-9.

    Also fix common OCR confusions adjacent to digit runs:
    o/O → 0, l/I → 1.
    """
    text = text.translate(_DEVANAGARI_MAP)
    out = list(text)
    for i, ch in enumerate(out):
        if ch in "oO":
            # If adjacent to a digit, treat as 0
            prev_dig = i > 0 and out[i - 1].isdigit()
            next_dig = i < len(out) - 1 and out[i + 1].isdigit()
            if prev_dig or next_dig:
                out[i] = "0"
        elif ch in "lI":
            prev_dig = i > 0 and out[i - 1].isdigit()
            next_dig = i < len(out) - 1 and out[i + 1].isdigit()
            if prev_dig or next_dig:
                out[i] = "1"
    return "".join(out)


def _norm(text: str) -> str:
    """Lowercase, strip, collapse whitespace."""
    return " ".join(text.lower().split())


def _label_match(text: str, patterns: List[str],
                 threshold: float = 70.0) -> float:
    """Return the best fuzzy-match score of *text* against *patterns*."""
    t = _norm(text)
    best = 0.0
    for pat in patterns:
        # Exact substring check first
        if pat in t:
            return 100.0
        if fuzz is not None:
            score = fuzz.partial_ratio(t, pat)
            # Short patterns (≤4 chars) produce high partial_ratio on
            # unrelated text (e.g. "dist" vs "sristi").  Require near-
            # perfect score for them to avoid false positive label tags.
            if len(pat) <= 4 and score < 90:
                continue
            if score > best:
                best = score
    return best


def _flex_re(label: str) -> re.Pattern:
    """Build a regex that inserts optional whitespace/punctuation between
    characters of *label*, allowing for OCR spacing errors.

    Example: "certificate" → r"c[\s.]*e[\s.]*r[\s.]*t …"
    """
    chars = list(label.lower())
    parts = [re.escape(ch) for ch in chars]
    return re.compile(r"[\s.]*".join(parts), re.IGNORECASE)


def _inline_value(text: str, patterns: List[str]) -> Optional[str]:
    """Extract the value portion from a string like ``Label: Value``.

    Tries flex_re first (longest match wins), then colon-split, then substring removal.
    """
    lower = text.lower()

    # 1. flex_re extraction — find where the label ends
    #    Try ALL patterns and pick the one whose match extends farthest
    #    so that "sub-metropolitan" beats "metro".
    best_end = -1
    for pat in patterns:
        rx = _flex_re(pat)
        m = rx.search(lower)
        if m and m.end() > best_end:
            best_end = m.end()
    if best_end > 0:
        after = text[best_end:].strip()
        after = re.sub(r"^[\s:.\-]+", "", after).strip()
        if after:
            return after

    # 2. Colon split
    if ":" in text:
        _, _, rhs = text.partition(":")
        rhs = rhs.strip()
        if rhs:
            return rhs

    # 3. Substring removal (use longest matching pattern)
    best_pat = ""
    for pat in patterns:
        if pat in lower and len(pat) > len(best_pat):
            best_pat = pat
    if best_pat:
        idx = lower.index(best_pat)
        after = text[idx + len(best_pat):].strip()
        after = re.sub(r"^[\s:.\-]+", "", after).strip()
        if after:
            return after

    return None


def _has_alnum(text: str) -> bool:
    """Return True if *text* contains at least one alphanumeric character."""
    return any(ch.isalnum() for ch in text)


def _is_any_label(text: str, threshold: float = 70.0) -> bool:
    """Return True if *text* fuzzy matches ANY known label."""
    for pats in LABEL_PATTERNS.values():
        if _label_match(text, pats, threshold) >= threshold:
            return True
    for sub_labels in [DOB_SUBLABELS, ADDR_SUBLABELS]:
        for pats in sub_labels.values():
            if _label_match(text, pats, threshold) >= threshold:
                return True
    return False


def _normalize_month(raw: str) -> str:
    """Try to normalise a month string to its canonical short form."""
    raw_l = raw.strip().lower()
    month_map = {
        "january": "JAN", "february": "FEB", "march": "MAR",
        "april": "APR", "may": "MAY", "june": "JUN",
        "july": "JUL", "august": "AUG", "september": "SEP",
        "october": "OCT", "november": "NOV", "december": "DEC",
        "jan": "JAN", "feb": "FEB", "mar": "MAR", "apr": "APR",
        "jun": "JUN", "jul": "JUL", "aug": "AUG", "sep": "SEP",
        "oct": "OCT", "nov": "NOV", "dec": "DEC",
    }
    if raw_l in month_map:
        return month_map[raw_l]
    # Try prefix match
    for k, v in month_map.items():
        if raw_l.startswith(k[:3]):
            return v
    # Return cleaned numeric if it looks like a number
    digits = re.sub(r"\D", "", raw)
    if digits:
        return digits
    return raw.upper()


# ============================================================ extractor ===

class SemanticExtractor:
    """Extract structured citizenship card fields from OCR layout."""

    def __init__(self, cfg: Optional[SemanticConfig] = None):
        self.cfg = cfg or SemanticConfig()

    # ---- classify boxes --------------------------------------------

    def classify_boxes(self, layout: LayoutResult) -> None:
        """Assign role = LABEL / VALUE / NOISE to each box."""
        for b in layout.all_boxes:
            text = b.text.strip()
            # NOISE: very low OCR confidence (random artefacts)
            if b.confidence < self.cfg.noise_min_confidence:
                b.role = "NOISE"
                continue
            # NOISE: very short non-digit text (punctuation, stray marks)
            clean = re.sub(r"[^a-zA-Z0-9]", "", text)
            if len(clean) <= self.cfg.noise_max_chars and not clean.isdigit():
                b.role = "NOISE"
                continue
            # LABEL: matches any known label pattern
            if _is_any_label(text, self.cfg.label_fuzzy_threshold):
                b.role = "LABEL"
                continue
            # VALUE: everything else
            b.role = "VALUE"

    # ---- anchor labels ---------------------------------------------

    def anchor_labels(self, layout: LayoutResult,
                      canonical_h: float) -> Dict[str, AnchorInfo]:
        """For each field, find the best-matching label box in its Y-band."""
        anchors: Dict[str, AnchorInfo] = {}

        for field_key, patterns in LABEL_PATTERNS.items():
            y_min, y_max = CANONICAL_ANCHORS[field_key]
            tolerance = 0.15  # allow slight overshoot
            best_score = 0.0
            best_box = None

            for b in layout.all_boxes:
                if b.role == "NOISE":
                    continue
                frac_y = b.cy / max(1.0, canonical_h)
                if frac_y < y_min - tolerance or frac_y > y_max + tolerance:
                    continue
                score = _label_match(b.text, patterns,
                                     self.cfg.label_fuzzy_threshold)
                if score > best_score:
                    best_score = score
                    best_box = b

            if best_box is not None and best_score >= self.cfg.label_fuzzy_threshold:
                anchors[field_key] = AnchorInfo(
                    field_key=field_key,
                    label_box=best_box,
                    label_text=best_box.text,
                    match_score=best_score,
                )
        return anchors

    # ---- spatial value resolution ----------------------------------

    def _same_row(self, a: LayoutBox, b: LayoutBox,
                  avg_h: float) -> bool:
        tol = avg_h * self.cfg.row_y_tolerance_factor
        return abs(a.cy - b.cy) <= tol

    def _right_of(self, label: LayoutBox, candidate: LayoutBox,
                  avg_w: float) -> bool:
        if candidate.cx <= label.cx:
            return False
        # Cap at 4x avg box width for same-row association
        max_dist = avg_w * self.cfg.right_max_distance_factor * 6
        return (candidate.x0 - label.x1) < max_dist

    def _below_aligned(self, label: LayoutBox, candidate: LayoutBox,
                       avg_h: float) -> bool:
        if candidate.cy <= label.cy:
            return False
        gap = candidate.y0 - label.y1
        if gap > avg_h * self.cfg.below_max_gap_factor:
            return False
        x_overlap = max(0, min(label.x1, candidate.x1) -
                        max(label.x0, candidate.x0))
        label_w = max(1, label.x1 - label.x0)
        cand_w = max(1, candidate.x1 - candidate.x0)
        # Use the larger of the two widths as denominator for relative overlap
        ref_w = max(label_w, cand_w)
        return (x_overlap / ref_w) > 0.15 or \
               abs(candidate.x0 - label.x0) < avg_h * 2.5

    def _resolve_value(self, label_box: LayoutBox,
                       labels: Dict[str, AnchorInfo],
                       layout: LayoutResult,
                       field_key: str = "") -> Optional[str]:
        """Resolve the value for a label box using spatial heuristics.

        Steps:
          1)  Inline value (label text contains the value).
          1b) Field-specific regex scan on the label text.
          2)  Right-of on same row (closest non-label box).
          3)  Below-aligned (closest non-label box).
        """
        avg_h = max(1, layout.avg_box_height)
        avg_w = max(1, layout.avg_box_width)

        label_box_ids = {id(a.label_box) for a in labels.values() if a.label_box}

        # Step 1: inline value
        for field_k, pats in LABEL_PATTERNS.items():
            if _label_match(label_box.text, pats,
                            self.cfg.label_fuzzy_threshold) >= self.cfg.label_fuzzy_threshold:
                val = _inline_value(label_box.text, pats)
                if val and _has_alnum(val):
                    return val
                break

        # Step 1b: field-specific regex directly on label text
        text_clean = _devanagari_to_ascii(label_box.text)
        if field_key == "cert_no":
            m = CERT_NO_RE.search(text_clean)
            if m:
                return m.group(1)
            # Try loose regex for OCR spacing errors
            m = CERT_NO_LOOSE_RE.search(text_clean)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}-{m.group(4)}"
        elif field_key == "sex":
            lower = _norm(text_clean)
            for sex_val in _SEX_ORDERED:    # "female" before "male"
                if sex_val in lower:
                    return sex_val.upper()
            # Handle partial OCR: "Ma" -> "Male", "Fe" -> "Female"
            if fuzz is not None:
                for sex_val in _SEX_ORDERED:
                    if fuzz.partial_ratio(lower, sex_val) >= 75:
                        return sex_val.upper()
            # Simple prefix match for common truncations
            stripped = re.sub(r'[^a-zA-Z]', '', text_clean).lower()
            for sex_val in _SEX_ORDERED:
                if sex_val.startswith(stripped) and len(stripped) >= 2:
                    return sex_val.upper()

        # Step 2: right-of on same row
        candidates = []
        for b in layout.all_boxes:
            if b is label_box or id(b) in label_box_ids:
                continue
            if b.role == "NOISE":
                continue
            if not _has_alnum(b.text):
                continue
            if self._same_row(label_box, b, avg_h) and \
               self._right_of(label_box, b, avg_w):
                dist = b.x0 - label_box.x1
                candidates.append((dist, b))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            val = candidates[0][1].text.strip()
            if _has_alnum(val) and not _is_any_label(val):
                return val

        # Step 3: below-aligned
        candidates = []
        for b in layout.all_boxes:
            if b is label_box or id(b) in label_box_ids:
                continue
            if b.role == "NOISE":
                continue
            if not _has_alnum(b.text):
                continue
            if self._below_aligned(label_box, b, avg_h):
                gap = b.y0 - label_box.y1
                candidates.append((gap, b))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            val = candidates[0][1].text.strip()
            if _has_alnum(val) and not _is_any_label(val):
                return val

        return None

    # ---- sub-field extraction (DOB / address) ----------------------

    def _next_header_y(self, current_y: float,
                       labels: Dict[str, AnchorInfo]) -> float:
        """Return the Y of the next major field label below *current_y*."""
        next_y = 1e9
        for a in labels.values():
            if a.label_box and a.label_box.cy > current_y + 5:
                next_y = min(next_y, a.label_box.cy)
        return next_y

    def _extract_sub_fields(self, header_box: LayoutBox,
                            sub_labels: Dict[str, List[str]],
                            labels: Dict[str, AnchorInfo],
                            layout: LayoutResult,
                            canonical_h: float) -> Dict[str, str]:
        """Extract sub-fields (year/month/day or district/municipality/ward)
        within a section bounded by *header_box* and the next major label.
        """
        avg_h = max(1, layout.avg_box_height)
        avg_w = max(1, layout.avg_box_width)
        label_box_ids = {id(a.label_box) for a in labels.values() if a.label_box}
        next_y = self._next_header_y(header_box.cy, labels)

        # Gather all boxes in the section (at or below header, above next label)
        section_boxes = []
        for b in layout.all_boxes:
            if b.cy >= header_box.cy - avg_h * 0.5 and b.cy < next_y:
                section_boxes.append(b)

        result: Dict[str, str] = {}
        for sub_key, patterns in sub_labels.items():
            # Find the sub-label box
            best_box = None
            best_score = 0.0
            for b in section_boxes:
                score = _label_match(b.text, patterns,
                                     self.cfg.label_fuzzy_threshold)
                if score > best_score:
                    best_score = score
                    best_box = b

            if best_box is None or best_score < self.cfg.label_fuzzy_threshold:
                continue

            # Try inline value in the sub-label text
            val = _inline_value(best_box.text, patterns)
            if val and _has_alnum(val):
                # For DOB sub-fields, OCR sometimes merges month+day
                # into one box (e.g. "Month:07Da:28").  Keep only the
                # leading numeric or alphabetic token.
                if sub_key in ("year", "month", "day"):
                    m_tok = re.match(r'^(\d{1,4}|[a-zA-Z]+)', val.strip())
                    if m_tok:
                        val = m_tok.group(1)
                    else:
                        continue  # nothing useful
                result[sub_key] = val
                continue

            # Right-of on same row
            row_cands = []
            for b in section_boxes:
                if b is best_box or id(b) in label_box_ids:
                    continue
                if b.role == "NOISE" or not _has_alnum(b.text):
                    continue
                if self._same_row(best_box, b, avg_h) and \
                   self._right_of(best_box, b, avg_w):
                    dist = b.x0 - best_box.x1
                    row_cands.append((dist, b))
            if row_cands:
                row_cands.sort(key=lambda x: x[0])
                val = row_cands[0][1].text.strip()
                if _has_alnum(val) and not _is_any_label(val):
                    result[sub_key] = val
                    continue

            # Below-aligned
            below_cands = []
            for b in section_boxes:
                if b is best_box or id(b) in label_box_ids:
                    continue
                if b.role == "NOISE" or not _has_alnum(b.text):
                    continue
                if self._below_aligned(best_box, b, avg_h):
                    gap = b.y0 - best_box.y1
                    below_cands.append((gap, b))
            if below_cands:
                below_cands.sort(key=lambda x: x[0])
                val = below_cands[0][1].text.strip()
                if _has_alnum(val) and not _is_any_label(val):
                    result[sub_key] = val

        return result

    # ---- fallbacks -------------------------------------------------

    def _fallback_cert_no(self, layout: LayoutResult,
                          canonical_h: float) -> Optional[str]:
        """Scan all boxes (prioritising top region) for a cert-number pattern."""
        # First pass: strict regex in top 40%
        for b in layout.all_boxes:
            if b.cy / max(1, canonical_h) > 0.40:
                continue
            cleaned = _devanagari_to_ascii(b.text)
            m = CERT_NO_RE.search(cleaned)
            if m:
                return m.group(1)
        # Second pass: loose regex in top 40% (handles OCR spacing errors)
        for b in layout.all_boxes:
            if b.cy / max(1, canonical_h) > 0.40:
                continue
            cleaned = _devanagari_to_ascii(b.text)
            m = CERT_NO_LOOSE_RE.search(cleaned)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}-{m.group(4)}"
        # Third pass: strict regex anywhere (for zoomed/cropped images)
        for b in layout.all_boxes:
            cleaned = _devanagari_to_ascii(b.text)
            m = CERT_NO_RE.search(cleaned)
            if m:
                return m.group(1)
        return None

    def _fallback_full_name(self, layout: LayoutResult,
                            canonical_h: float) -> Optional[str]:
        """Find an all-caps VALUE box in the top region → likely the name."""
        for b in layout.all_boxes:
            if b.role != "VALUE":
                continue
            if b.cy / max(1, canonical_h) > 0.50:
                continue
            text = b.text.strip()
            alpha = re.sub(r"[^a-zA-Z ]", "", text)
            if len(alpha) >= 3 and alpha == alpha.upper():
                return text
        return None

    def _fallback_sex(self, layout: LayoutResult,
                      canonical_h: float) -> Optional[str]:
        """Scan all boxes for a sex keyword."""
        for b in layout.all_boxes:
            if b.cy / max(1, canonical_h) > 0.50:
                continue
            lower = _norm(b.text)
            # Check ordered to avoid "male" matching inside "female"
            for sex_val in _SEX_ORDERED:
                if sex_val in lower:
                    return sex_val.upper()
        # Fuzzy word-level check + partial match for truncated OCR
        for b in layout.all_boxes:
            if b.cy / max(1, canonical_h) > 0.50:
                continue
            lower = _norm(b.text)
            # Check after stripping "sex" label prefix
            after_sex = re.sub(r"^.*sex[\s:.\-]*", "", lower).strip()
            if after_sex:
                for sex_val in _SEX_ORDERED:
                    if sex_val.startswith(after_sex) and len(after_sex) >= 2:
                        return sex_val.upper()
            for word in lower.split():
                if fuzz is not None:
                    for sex_val in _SEX_ORDERED:
                        if fuzz.ratio(word, sex_val) >= 65:
                            return sex_val.upper()
        return None

    # ---- validation ------------------------------------------------

    def _validate(self, fields: Dict[str, Any]) -> List[ValidationIssue]:
        """Run validation rules and return issues."""
        issues: List[ValidationIssue] = []

        # Cert number format
        cert = fields.get("citizenship_certificate_number", "")
        if cert:
            cleaned = _devanagari_to_ascii(cert)
            if not CERT_NO_RE.fullmatch(cleaned):
                issues.append(ValidationIssue(
                    field="citizenship_certificate_number",
                    severity="warning",
                    message=f"cert_no '{cert}' doesn't match expected pattern XX-XX-XX-XXXXX",
                ))

        # Sex
        sex = fields.get("sex", "")
        if sex and sex.lower() not in SEX_ENUM:
            issues.append(ValidationIssue(
                field="sex", severity="warning",
                message=f"sex '{sex}' not in {SEX_ENUM}",
            ))

        # DOB
        dob = fields.get("date_of_birth", {})
        if isinstance(dob, dict):
            yr = str(dob.get("year", ""))
            if yr and not YEAR_RE.fullmatch(yr):
                issues.append(ValidationIssue(
                    field="date_of_birth.year", severity="warning",
                    message=f"year '{yr}' doesn't look like a 4-digit year",
                ))
            dy = str(dob.get("day", ""))
            if dy:
                dy_digits = re.sub(r"\D", "", dy)
                if dy_digits:
                    val = int(dy_digits)
                    if val < 1 or val > 32:
                        issues.append(ValidationIssue(
                            field="date_of_birth.day", severity="warning",
                            message=f"day '{dy}' out of range",
                        ))

        # Geography cross-reference
        for addr_key in ["birth_place", "permanent_address"]:
            addr = fields.get(addr_key, {})
            if not isinstance(addr, dict):
                continue
            dist = addr.get("district", "")
            muni = addr.get("municipality", "")
            # Try fuzzy correction
            if dist and not validate_district(dist):
                corrected = fuzzy_match_district(dist)
                if corrected:
                    addr["district"] = corrected
                    dist = corrected
                else:
                    issues.append(ValidationIssue(
                        field=f"{addr_key}.district", severity="warning",
                        message=f"district '{dist}' not recognised",
                    ))
            if muni and dist:
                if not validate_municipality(muni, dist):
                    corrected = fuzzy_match_municipality(muni, dist)
                    if corrected:
                        addr["municipality"] = corrected
                    else:
                        issues.append(ValidationIssue(
                            field=f"{addr_key}.municipality", severity="warning",
                            message=f"municipality '{muni}' not found in district '{dist}'",
                        ))

        return issues

    # ---- main entry point ------------------------------------------

    def extract(self, layout: LayoutResult,
                canonical_h: float) -> SemanticResult:
        """Run the full extraction pipeline: classify → anchor → resolve → validate."""

        # Step 1: classify boxes
        self.classify_boxes(layout)

        # Step 2: anchor labels
        anchors = self.anchor_labels(layout, canonical_h)

        fields: Dict[str, Any] = {}
        confidences: Dict[str, float] = {}

        # Step 3: resolve scalar fields
        for field_key in ["cert_no", "sex", "full_name"]:
            if field_key in anchors:
                a = anchors[field_key]
                val = self._resolve_value(a.label_box, anchors, layout,
                                          field_key=field_key)
                if val:
                    fields[self._field_name(field_key)] = val
                    confidences[self._field_name(field_key)] = a.match_score / 100.0

        # Step 3b: fallbacks for scalar fields
        fn = self._field_name
        if fn("cert_no") not in fields:
            fb = self._fallback_cert_no(layout, canonical_h)
            if fb:
                fields[fn("cert_no")] = fb
                confidences[fn("cert_no")] = 0.5

        if fn("full_name") not in fields:
            fb = self._fallback_full_name(layout, canonical_h)
            if fb:
                fields[fn("full_name")] = fb
                confidences[fn("full_name")] = 0.4

        if fn("sex") not in fields:
            fb = self._fallback_sex(layout, canonical_h)
            if fb:
                fields[fn("sex")] = fb
                confidences[fn("sex")] = 0.4

        # Clean up cert_no — ensure only the numeric pattern
        cert_raw = fields.get(fn("cert_no"), "")
        if cert_raw:
            cleaned = _devanagari_to_ascii(cert_raw)
            m = CERT_NO_RE.search(cleaned)
            if m:
                fields[fn("cert_no")] = m.group(1)
            else:
                # Try loose regex for OCR noise
                m = CERT_NO_LOOSE_RE.search(cleaned)
                if m:
                    fields[fn("cert_no")] = (
                        f"{m.group(1)}-{m.group(2)}-{m.group(3)}-{m.group(4)}"
                    )

        # Step 4: DOB sub-fields
        if "dob" in anchors:
            dob_subs = self._extract_sub_fields(
                anchors["dob"].label_box, DOB_SUBLABELS,
                anchors, layout, canonical_h,
            )
            dob_dict: Dict[str, str] = {}
            if "year" in dob_subs:
                yr = _devanagari_to_ascii(dob_subs["year"])
                m = YEAR_RE.search(yr)
                dob_dict["year"] = m.group(1) if m else yr
            if "month" in dob_subs:
                dob_dict["month"] = _normalize_month(dob_subs["month"])
            if "day" in dob_subs:
                dy = _devanagari_to_ascii(dob_subs["day"])
                m = DAY_RE.search(dy)
                dob_dict["day"] = m.group(1) if m else dy

            # Fallback: scan section boxes for year/day if missing
            if "year" not in dob_dict or "day" not in dob_dict:
                dob_anchor = anchors["dob"].label_box
                next_y = self._next_header_y(dob_anchor.cy, anchors)
                section = [b for b in layout.all_boxes
                           if dob_anchor.cy - 5 <= b.cy < next_y
                           and b.role != "NOISE"]
                for b in section:
                    cleaned = _devanagari_to_ascii(b.text)
                    if "year" not in dob_dict:
                        m = YEAR_RE.search(cleaned)
                        if m:
                            dob_dict["year"] = m.group(1)
                    if "day" not in dob_dict:
                        # Only take small 1-2 digit numbers
                        nums = re.findall(r"\b(\d{1,2})\b", cleaned)
                        for n in nums:
                            v = int(n)
                            if 1 <= v <= 32:
                                dob_dict["day"] = n
                                break

            if dob_dict:
                # Build ISO-style string
                yr = dob_dict.get("year", "????")
                mo = dob_dict.get("month", "??")
                dy = dob_dict.get("day", "??")
                fields["date_of_birth"] = f"{yr}-{mo}-{dy}"
                fields["date_of_birth_parts"] = dob_dict
                confidences["date_of_birth"] = anchors["dob"].match_score / 100.0

        # Step 5: address sections
        for addr_key in ["birth_place", "permanent_address"]:
            if addr_key not in anchors:
                continue
            addr_subs = self._extract_sub_fields(
                anchors[addr_key].label_box, ADDR_SUBLABELS,
                anchors, layout, canonical_h,
            )
            addr_dict: Dict[str, str] = {}
            if "district" in addr_subs:
                addr_dict["district"] = addr_subs["district"]
            if "municipality" in addr_subs:
                addr_dict["municipality"] = addr_subs["municipality"]
            if "ward" in addr_subs:
                wd = _devanagari_to_ascii(addr_subs["ward"])
                m = WARD_RE.search(wd)
                addr_dict["ward"] = m.group(1) if m else wd

            if addr_dict:
                fields[addr_key] = addr_dict
                confidences[addr_key] = anchors[addr_key].match_score / 100.0

        # Step 5b: cross-fill missing address sub-fields
        # If birth_place and permanent_address share the same district,
        # copy missing sub-fields from one to the other (very common on
        # Nepal citizenship cards).
        bp = fields.get("birth_place", {})
        pa = fields.get("permanent_address", {})
        if isinstance(bp, dict) and isinstance(pa, dict):
            bp_dist = bp.get("district", "").lower()
            pa_dist = pa.get("district", "").lower()
            if bp_dist and pa_dist and bp_dist == pa_dist:
                for sub in ("municipality", "ward"):
                    if sub not in bp and sub in pa:
                        bp[sub] = pa[sub]
                    elif sub not in pa and sub in bp:
                        pa[sub] = bp[sub]

        # Step 6: validate and correct
        issues = self._validate(fields)

        # Build box_roles map
        box_roles = {b.text: b.role for b in layout.all_boxes if b.text.strip()}

        # Flags for review
        flags = []
        expected = ["citizenship_certificate_number", "sex", "full_name",
                    "date_of_birth", "birth_place", "permanent_address"]
        for f in expected:
            if f not in fields:
                flags.append(f"MISSING: {f}")

        return SemanticResult(
            fields=fields,
            field_confidences=confidences,
            anchors=anchors,
            validation_issues=issues,
            flags_for_review=flags,
            box_roles=box_roles,
        )

    @staticmethod
    def _field_name(key: str) -> str:
        """Map internal key to output field name."""
        mapping = {
            "cert_no": "citizenship_certificate_number",
            "sex": "sex",
            "full_name": "full_name",
            "dob": "date_of_birth",
            "birth_place": "birth_place",
            "permanent_address": "permanent_address",
        }
        return mapping.get(key, key)


# ----------------------------------------------------------------- CLI ---

if __name__ == "__main__":
    from models.layout_analyzer import LayoutAnalyzer

    # Synthetic test boxes (simulating OCR output on a canonical image)
    boxes = [
        LayoutBox.from_box_points(
            [[10, 50], [500, 50], [500, 80], [10, 80]],
            "Citizenship Certificate No: 42-02-81-00802", 0.95),
        LayoutBox.from_box_points(
            [[600, 50], [750, 50], [750, 80], [600, 80]],
            "Sex: Female", 0.90),
        LayoutBox.from_box_points(
            [[10, 120], [300, 120], [300, 150], [10, 150]],
            "Full Name", 0.95),
        LayoutBox.from_box_points(
            [[310, 120], [600, 120], [600, 150], [310, 150]],
            "SRISTI BHATTARAI", 0.92),
        LayoutBox.from_box_points(
            [[10, 200], [200, 200], [200, 230], [10, 230]],
            "Date of Birth", 0.95),
        LayoutBox.from_box_points(
            [[210, 200], [350, 200], [350, 230], [210, 230]],
            "Year", 0.90),
        LayoutBox.from_box_points(
            [[360, 200], [450, 200], [450, 230], [360, 230]],
            "2063", 0.88),
        LayoutBox.from_box_points(
            [[460, 200], [560, 200], [560, 230], [460, 230]],
            "Month", 0.90),
        LayoutBox.from_box_points(
            [[570, 200], [650, 200], [650, 230], [570, 230]],
            "08", 0.85),
        LayoutBox.from_box_points(
            [[660, 200], [720, 200], [720, 230], [660, 230]],
            "Day", 0.90),
        LayoutBox.from_box_points(
            [[730, 200], [790, 200], [790, 230], [730, 230]],
            "07", 0.85),
    ]

    analyzer = LayoutAnalyzer()
    layout = analyzer.analyze(boxes)

    extractor = SemanticExtractor()
    result = extractor.extract(layout, canonical_h=600)

    print("Fields:")
    for k, v in result.fields.items():
        print(f"  {k}: {v}")
    print("Confidences:", result.field_confidences)
    print("Issues:", [(i.field, i.message) for i in result.validation_issues])
    print("Flags:", result.flags_for_review)
