"""Nepal Citizenship Card Extraction Pipeline.

Orchestrates Phase 1 (Canonical Normalization), Phase 2 (Layout + OCR),
and Phase 3 (Semantic Extraction) into a single end-to-end pipeline.

Primary OCR engine: PaddleOCR (PP-OCRv5)
Fallback OCR engine: EasyOCR
"""

from __future__ import annotations

import json
import os
import sys
import time
import threading
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Environment patches for PaddleOCR on Windows ──────────────────────────
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "1"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_new_ir"] = "0"

# Import torch BEFORE paddle to avoid DLL shm conflict on Windows
try:
    import torch  # noqa: F401
except ImportError:
    pass

# Monkey-patch PaddleInfer to disable oneDNN / new-IR that crash on some
# Windows + Paddle 3.x setups.
try:
    from paddlex.inference.common.batch_predictor import PaddleInfer

    _original_create = PaddleInfer._create

    def _patched_create(self, *args, **kwargs):
        self.run_mode = "paddle"
        self.enable_new_ir = False
        return _original_create(self, *args, **kwargs)

    PaddleInfer._create = _patched_create
except Exception:
    pass

import cv2
import numpy as np

from models.canonical_normalizer import CanonicalNormalizer, CanonicalConfig
from models.layout_analyzer import LayoutAnalyzer, LayoutBox, LayoutResult
from models.semantic_extractor import SemanticExtractor, SemanticConfig

# Global lock for PaddlePaddle/PaddleOCR predict calls.
# PaddlePaddle's C++ inference engine is NOT thread-safe;
# concurrent predict() calls corrupt internal state.
_paddle_predict_lock = threading.Lock()


# ---------------------------------------------------------------- config ---

@dataclass
class PipelineConfig:
    """Pipeline-level configuration."""
    # OCR engine selection
    ocr_engine: str = "paddleocr"        # "paddleocr" | "easyocr"

    # PaddleOCR model names (PP-OCRv5)
    paddle_det_model: str = "PP-OCRv5_mobile_det"
    paddle_rec_model: str = "PP-OCRv5_server_rec"

    # EasyOCR settings (fallback)
    easyocr_languages: List[str] = field(default_factory=lambda: ["en", "ne"])
    easyocr_gpu: bool = False

    # Minimum recognition confidence (below this → discard)
    min_confidence: float = 0.10

    # Canonical normalizer config
    canonical: CanonicalConfig = field(default_factory=CanonicalConfig)

    # Semantic extractor config
    semantic: SemanticConfig = field(default_factory=SemanticConfig)


# ---------------------------------------------------------------- result ---

@dataclass
class PipelineResult:
    """Full extraction result from the pipeline."""
    fields: Dict[str, Any] = field(default_factory=dict)
    field_confidences: Dict[str, float] = field(default_factory=dict)
    validation_issues: List[Dict[str, str]] = field(default_factory=list)
    flags_for_review: List[str] = field(default_factory=list)
    box_roles: List[Dict[str, Any]] = field(default_factory=list)
    warp_metadata: Dict[str, Any] = field(default_factory=dict)
    layout_summary: Dict[str, Any] = field(default_factory=dict)
    timing: Dict[str, float] = field(default_factory=dict)
    raw_text: str = ""
    success: bool = True
    error: Optional[str] = None


# ----------------------------------------------------- image helpers ---

def _enhance_for_ocr(image_bgr: np.ndarray) -> np.ndarray:
    """Apply CLAHE + light sharpening to improve OCR accuracy.

    Works across varied lighting, contrast and image quality.
    """
    # CLAHE on L channel for better contrast
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    enhanced = cv2.merge([l_ch, a_ch, b_ch])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    # Light sharpening to crispen text edges
    kernel = np.array([[0, -0.5, 0],
                       [-0.5, 3, -0.5],
                       [0, -0.5, 0]], dtype=np.float32)
    enhanced = cv2.filter2D(enhanced, -1, kernel)
    return enhanced


def _nms_boxes(boxes: list, iou_threshold: float = 0.5) -> list:
    """Non-maximum suppression: remove overlapping boxes, keep higher conf."""
    if len(boxes) <= 1:
        return boxes

    # Sort by confidence descending
    boxes_sorted = sorted(boxes, key=lambda b: b.confidence, reverse=True)
    keep = []

    for b in boxes_sorted:
        is_dup = False
        for kept in keep:
            # Compute IoU using axis-aligned bounding boxes
            x_left = max(b.x0, kept.x0)
            y_top = max(b.y0, kept.y0)
            x_right = min(b.x1, kept.x1)
            y_bot = min(b.y1, kept.y1)
            if x_right > x_left and y_bot > y_top:
                inter = (x_right - x_left) * (y_bot - y_top)
                area_b = max(1, (b.x1 - b.x0) * (b.y1 - b.y0))
                area_k = max(1, (kept.x1 - kept.x0) * (kept.y1 - kept.y0))
                iou = inter / min(area_b, area_k)  # use min for containment
                if iou > iou_threshold:
                    is_dup = True
                    break
        if not is_dup:
            keep.append(b)
    return keep


# ------------------------------------------------------------ pipeline ---

class CitizenshipPipeline:
    """End-to-end Nepal citizenship card extraction."""

    def __init__(self, cfg: Optional[PipelineConfig] = None):
        self.cfg = cfg or PipelineConfig()
        self._normalizer = CanonicalNormalizer(self.cfg.canonical)
        self._analyzer = LayoutAnalyzer()
        self._extractor = SemanticExtractor(self.cfg.semantic)
        self._paddle_ocr = None
        self._easyocr_reader = None

    # ── PaddleOCR ──────────────────────────────────────────────────

    def _init_paddleocr(self):
        """Lazy-initialise PaddleOCR with tuned detection parameters.

        Uses tighter box params for precise word-level detection.
        Falls back to defaults if custom params are rejected.
        Thread-safe: uses the global predict lock during init too.
        """
        if self._paddle_ocr is not None:
            return
        from paddleocr import PaddleOCR
        with _paddle_predict_lock:
            # Double-check after acquiring lock
            if self._paddle_ocr is not None:
                return
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    self._paddle_ocr = PaddleOCR(
                        text_detection_model_name=self.cfg.paddle_det_model,
                        text_recognition_model_name=self.cfg.paddle_rec_model,
                        use_textline_orientation=False,
                        # Tighter boxes: lower unclip_ratio = less padding
                        det_db_thresh=0.3,
                        det_db_box_thresh=0.5,
                        det_db_unclip_ratio=1.3,
                    )
                except Exception:
                    # Fallback to defaults if params not supported
                    self._paddle_ocr = PaddleOCR(
                        text_detection_model_name=self.cfg.paddle_det_model,
                        text_recognition_model_name=self.cfg.paddle_rec_model,
                        use_textline_orientation=False,
                    )

    def _paddleocr_detect_recognize(self, image: np.ndarray) -> List[LayoutBox]:
        """Run PaddleOCR on an enhanced BGR image and return LayoutBox list."""
        self._init_paddleocr()
        boxes: List[LayoutBox] = []

        # Enhance image for better OCR accuracy
        enhanced = _enhance_for_ocr(image)

        # Serialize PaddlePaddle predict calls across all threads
        with _paddle_predict_lock:
            results = self._paddle_ocr.predict(enhanced)

        for result in results:
            # result is a dict-like OCRResult — access via dict()
            rd = dict(result)
            dt_polys = rd.get("dt_polys", [])
            rec_texts = rd.get("rec_texts", [])
            rec_scores = rd.get("rec_scores", [])

            for i, poly in enumerate(dt_polys):
                text = rec_texts[i] if i < len(rec_texts) else ""
                conf = rec_scores[i] if i < len(rec_scores) else 0.0
                if conf < self.cfg.min_confidence:
                    continue
                if not text.strip():
                    continue
                # poly is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                pts = [[float(p[0]), float(p[1])] for p in poly]
                boxes.append(LayoutBox.from_box_points(pts, text, conf))

        return boxes

    # ── EasyOCR ────────────────────────────────────────────────────

    def _init_easyocr(self):
        """Lazy-initialise EasyOCR reader."""
        if self._easyocr_reader is not None:
            return
        import easyocr
        self._easyocr_reader = easyocr.Reader(
            self.cfg.easyocr_languages, gpu=self.cfg.easyocr_gpu,
        )

    def _easyocr_detect_recognize(self, image: np.ndarray) -> List[LayoutBox]:
        """Run EasyOCR on an enhanced BGR image and return LayoutBox list."""
        self._init_easyocr()
        enhanced = _enhance_for_ocr(image)
        rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        results = self._easyocr_reader.readtext(rgb)
        boxes: List[LayoutBox] = []
        for (polygon, text, conf) in results:
            if conf < self.cfg.min_confidence:
                continue
            if not text.strip():
                continue
            pts = [[float(p[0]), float(p[1])] for p in polygon]
            boxes.append(LayoutBox.from_box_points(pts, text, conf))
        return boxes

    # ── run pipeline ───────────────────────────────────────────────

    def run(self, image_path: str) -> PipelineResult:
        """Execute the full 3-phase pipeline on *image_path*."""
        t_start = time.time()
        result = PipelineResult()

        # ── Phase 1: Canonical Normalization ──
        t1 = time.time()
        try:
            canon = self._normalizer.normalize(image_path)
        except Exception as exc:
            result.success = False
            result.error = f"Phase 1 failed: {exc}"
            return result

        if not canon.success:
            result.success = False
            result.error = f"Phase 1 failed: {canon.error}"
            return result

        canonical_img = canon.canonical_image
        result.warp_metadata = {
            "original_corners": canon.metadata.original_corners,
            "canonical_size": list(canon.metadata.canonical_size),
            "strategy_used": canon.metadata.strategy_used,
            "explanation": canon.metadata.explanation,
        }
        t1_end = time.time()

        # ── Phase 2: Layout Discovery + OCR ──
        t2 = time.time()
        try:
            if self.cfg.ocr_engine == "paddleocr":
                ocr_boxes = self._paddleocr_detect_recognize(canonical_img)
            elif self.cfg.ocr_engine == "easyocr":
                ocr_boxes = self._easyocr_detect_recognize(canonical_img)
            else:
                raise ValueError(f"Unknown OCR engine: {self.cfg.ocr_engine}")
        except Exception as exc:
            # Try fallback to EasyOCR if PaddleOCR fails
            if self.cfg.ocr_engine == "paddleocr":
                print(f"[WARN] PaddleOCR failed ({exc}), falling back to EasyOCR")
                try:
                    self.cfg.ocr_engine = "easyocr"
                    ocr_boxes = self._easyocr_detect_recognize(canonical_img)
                except Exception as exc2:
                    result.success = False
                    result.error = f"Phase 2 failed: {exc2}"
                    return result
            else:
                result.success = False
                result.error = f"Phase 2 failed: {exc}"
                return result

        # De-duplicate overlapping boxes via NMS
        ocr_boxes = _nms_boxes(ocr_boxes, iou_threshold=0.5)

        layout = self._analyzer.analyze(ocr_boxes)
        t2_end = time.time()

        result.layout_summary = {
            "num_boxes": len(layout.all_boxes),
            "avg_box_height": round(layout.avg_box_height, 1),
            "avg_box_width": round(layout.avg_box_width, 1),
            "num_lines": len(layout.lines),
        }

        # Raw text (all OCR text joined)
        result.raw_text = "\n".join(
            b.text for b in layout.all_boxes if b.text.strip())

        # ── Phase 3: Semantic Extraction ──
        t3 = time.time()
        try:
            semantic = self._extractor.extract(
                layout, float(self.cfg.canonical.canonical_height))
        except Exception as exc:
            result.success = False
            result.error = f"Phase 3 failed: {exc}"
            return result
        t3_end = time.time()

        result.fields = semantic.fields
        result.field_confidences = semantic.field_confidences
        result.validation_issues = [
            {"field": v.field, "severity": v.severity, "message": v.message}
            for v in semantic.validation_issues
        ]
        result.flags_for_review = semantic.flags_for_review
        result.box_roles = [
            {
                "text": b.text,
                "role": b.role,
                "box": b.box_points,
                "confidence": round(b.confidence, 3),
            }
            for b in layout.all_boxes if b.text.strip()
        ]

        t_end = time.time()
        result.timing = {
            "phase1_normalization_s": round(t1_end - t1, 3),
            "phase2_layout_ocr_s": round(t2_end - t2, 3),
            "phase3_semantic_s": round(t3_end - t3, 3),
            "total_s": round(t_end - t_start, 3),
        }

        return result

    # ── save outputs ───────────────────────────────────────────────

    def save_results(self, result: PipelineResult,
                     canonical_img: np.ndarray,
                     output_dir: str) -> None:
        """Save canonical.png, debug_overlay.png, and extraction.json."""
        os.makedirs(output_dir, exist_ok=True)

        # Canonical image
        cv2.imwrite(os.path.join(output_dir, "canonical.png"), canonical_img)

        # Debug overlay — draw boxes on canonical
        overlay = canonical_img.copy()
        for br in result.box_roles:
            pts = br.get("box")
            role = br.get("role", "")
            text = br.get("text", "")
            if not pts:
                continue
            color = (0, 255, 0) if role == "VALUE" else \
                    (255, 0, 0) if role == "LABEL" else (128, 128, 128)
            poly = np.array(pts, dtype=np.int32)
            cv2.polylines(overlay, [poly], True, color, 2)
            # Put text label
            x, y = int(poly[0][0]), int(poly[0][1]) - 5
            cv2.putText(overlay, f"{role}: {text[:30]}",
                        (x, max(y, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
        cv2.imwrite(os.path.join(output_dir, "debug_overlay.png"), overlay)

        # JSON
        out_data = {
            "warp_metadata": result.warp_metadata,
            "layout_summary": result.layout_summary,
            "fields": result.fields,
            "field_confidences": result.field_confidences,
            "validation_issues": result.validation_issues,
            "flags_for_review": result.flags_for_review,
            "box_roles": result.box_roles,
            "timing": result.timing,
            "raw_text": result.raw_text,
        }
        json_path = os.path.join(output_dir, "extraction.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2, ensure_ascii=False)

        print(f"JSON saved → {json_path}")


# ----------------------------------------------------------------- CLI ---

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Nepal Citizenship Card Extraction Pipeline")
    parser.add_argument("image", help="Path to the citizenship card image")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="Output directory (default: output_<stem>)")
    parser.add_argument("--ocr-engine", choices=["paddleocr", "easyocr"],
                        default="paddleocr",
                        help="OCR engine to use (default: paddleocr)")
    args = parser.parse_args()

    image_path = args.image
    if not os.path.isfile(image_path):
        print(f"ERROR: File not found: {image_path}")
        sys.exit(1)

    stem = Path(image_path).stem
    output_dir = args.output_dir or f"output_{stem}"

    cfg = PipelineConfig(ocr_engine=args.ocr_engine)
    pipeline = CitizenshipPipeline(cfg)

    print(f"Processing: {image_path}")
    print(f"OCR engine: {cfg.ocr_engine}")
    print()

    result = pipeline.run(image_path)

    if not result.success:
        print(f"FAILED: {result.error}")
        sys.exit(1)

    # Get canonical image for saving
    canon = pipeline._normalizer.normalize(image_path)
    pipeline.save_results(result, canon.canonical_image, output_dir)

    # Print results
    sep = "=" * 60
    print(f"\n{sep}")
    print("  EXTRACTION RESULTS")
    print(sep)
    for k, v in result.fields.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for sk, sv in v.items():
                print(f"    {sk}: {sv}")
        else:
            print(f"  {k}: {v}")

    if result.validation_issues:
        print(f"\n  Validation Issues:")
        for issue in result.validation_issues:
            print(f"    [{issue['severity']}] {issue['field']}: {issue['message']}")

    if result.flags_for_review:
        print(f"\n  Flags for Review:")
        for flag in result.flags_for_review:
            print(f"    - {flag}")

    print(f"\n  Timing: {result.timing}")
    print(sep)


if __name__ == "__main__":
    main()
