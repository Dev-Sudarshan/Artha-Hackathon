"""Phase 1 — Canonical Geometric Normalization.

Detects the thick black rectangular border in the upper portion of
a Nepal citizenship card and applies a perspective (homography) warp
to produce a fixed-size canonical image (default 1200×600 px).

The output guarantees that the SAME field always appears at the SAME
pixel coordinates regardless of the source resolution or camera angle.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np


# ---------------------------------------------------------------- config ---

@dataclass
class CanonicalConfig:
    """Tunable parameters for border detection and warping."""
    # Output dimensions (width × height) of the canonical image.
    canonical_width: int = 1200
    canonical_height: int = 600

    # Morphology / edge parameters
    blur_ksize: int = 5
    canny_low: int = 30
    canny_high: int = 120
    dilate_iterations: int = 3
    morph_ksize: int = 5

    # Contour filtering — the black border rectangle should occupy
    # a significant portion of the image.
    min_area_ratio: float = 0.10   # contour area / image area
    max_area_ratio: float = 0.95
    approx_epsilon_ratio: float = 0.02  # cv2.approxPolyDP epsilon

    aspect_ratio_range: Tuple[float, float] = (1.3, 5.0)

    # Adaptive thresholding fallback
    adaptive_block_size: int = 51
    adaptive_c: int = 10

    # Whether to try multiple strategies and pick the best
    multi_strategy: bool = True


# ---------------------------------------------------------------- result ---

@dataclass
class WarpMetadata:
    """Metadata about the perspective transform performed."""
    original_corners: List[List[int]]       # 4 corners in original image coords
    canonical_size: Tuple[int, int]          # (width, height)
    homography_matrix: Optional[List[List[float]]] = None
    strategy_used: str = ""
    explanation: str = ""


@dataclass
class CanonicalResult:
    """Output of Phase 1."""
    canonical_image: np.ndarray             # The warped, fixed-size image
    metadata: WarpMetadata
    success: bool = True
    error: Optional[str] = None


# -------------------------------------------------------------- helpers ---

def _load_bgr(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return img


def _preprocess_for_detection(image_bgr: np.ndarray) -> np.ndarray:
    """Apply CLAHE and light sharpening to improve edge detection
    across varying lighting, contrast and image quality."""
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    enhanced = cv2.merge([l_ch, a_ch, b_ch])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    return enhanced


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as [top-left, top-right, bottom-right, bottom-left].

    Uses the sum and difference heuristic:
      - top-left has the smallest sum (x+y)
      - bottom-right has the largest sum
      - top-right has the smallest difference (y-x)
      - bottom-left has the largest difference
    """
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    rect[0] = pts[np.argmin(s)]   # top-left
    rect[2] = pts[np.argmax(s)]   # bottom-right
    rect[1] = pts[np.argmin(d)]   # top-right
    rect[3] = pts[np.argmax(d)]   # bottom-left
    return rect


def _compute_homography(src_corners: np.ndarray,
                        dst_w: int, dst_h: int) -> Tuple[np.ndarray, np.ndarray]:
    """Return (homography_matrix, destination_corners)."""
    dst = np.array([
        [0, 0],
        [dst_w - 1, 0],
        [dst_w - 1, dst_h - 1],
        [0, dst_h - 1],
    ], dtype=np.float32)
    M, _ = cv2.findHomography(src_corners, dst)
    return M, dst


def _valid_quad(pts: np.ndarray, img_area: float,
                cfg: CanonicalConfig) -> bool:
    """Check that the quadrilateral is roughly rectangular and large enough."""
    area = cv2.contourArea(pts)
    ratio = area / max(1.0, img_area)
    if ratio < cfg.min_area_ratio or ratio > cfg.max_area_ratio:
        return False
    ordered = _order_points(pts.reshape(4, 2))
    w_top = np.linalg.norm(ordered[1] - ordered[0])
    w_bot = np.linalg.norm(ordered[2] - ordered[3])
    h_left = np.linalg.norm(ordered[3] - ordered[0])
    h_right = np.linalg.norm(ordered[2] - ordered[1])
    avg_w = (w_top + w_bot) / 2
    avg_h = (h_left + h_right) / 2
    if avg_h < 1:
        return False
    ar = avg_w / avg_h
    return cfg.aspect_ratio_range[0] <= ar <= cfg.aspect_ratio_range[1]


# ------------------------------------------------ detection strategies ---

def _strategy_canny(image_bgr: np.ndarray,
                    cfg: CanonicalConfig) -> List[np.ndarray]:
    """Detect border via Canny edge detection + contour approximation."""
    enhanced = _preprocess_for_detection(image_bgr)
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (cfg.blur_ksize, cfg.blur_ksize), 0)
    edges = cv2.Canny(blurred, cfg.canny_low, cfg.canny_high)
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (cfg.morph_ksize, cfg.morph_ksize))
    edges = cv2.dilate(edges, kernel, iterations=cfg.dilate_iterations)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)
    return _all_quads(contours, image_bgr.shape, cfg)


def _strategy_adaptive_threshold(image_bgr: np.ndarray,
                                 cfg: CanonicalConfig) -> List[np.ndarray]:
    """Detect border via adaptive thresholding for varied lighting."""
    enhanced = _preprocess_for_detection(image_bgr)
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (cfg.blur_ksize, cfg.blur_ksize), 0)
    block = cfg.adaptive_block_size
    if block % 2 == 0:
        block += 1
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, block, cfg.adaptive_c)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (cfg.morph_ksize, cfg.morph_ksize))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    thresh = cv2.dilate(thresh, kernel, iterations=cfg.dilate_iterations)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)
    return _all_quads(contours, image_bgr.shape, cfg)


def _strategy_color_border(image_bgr: np.ndarray,
                           cfg: CanonicalConfig) -> List[np.ndarray]:
    """Detect the *black* border specifically via HSV color filtering."""
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    # Black: low saturation, low value
    mask = cv2.inRange(hsv, (0, 0, 0), (180, 100, 80))
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (cfg.morph_ksize, cfg.morph_ksize))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    mask = cv2.dilate(mask, kernel, iterations=cfg.dilate_iterations)

    contours, _ = cv2.findContours(mask, cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)
    return _all_quads(contours, image_bgr.shape, cfg)


def _strategy_hough_lines(image_bgr: np.ndarray,
                          cfg: CanonicalConfig) -> Optional[np.ndarray]:
    """Detect border via Hough line intersection for strong straight edges."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (cfg.blur_ksize, cfg.blur_ksize), 0)
    edges = cv2.Canny(blurred, cfg.canny_low, cfg.canny_high)

    h, w = edges.shape[:2]
    min_line_len = min(h, w) // 4
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80,
                            minLineLength=min_line_len, maxLineGap=20)
    if lines is None or len(lines) < 4:
        return None

    # Separate horizontal and vertical lines
    horizontals = []
    verticals = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if angle < 15 or angle > 165:
            horizontals.append((y1, y2, x1, x2, length))
        elif 75 < angle < 105:
            verticals.append((x1, x2, y1, y2, length))

    if len(horizontals) < 2 or len(verticals) < 2:
        return None

    # Pick top/bottom horizontals and left/right verticals
    horizontals.sort(key=lambda l: (l[0] + l[1]) / 2)
    verticals.sort(key=lambda l: (l[0] + l[1]) / 2)

    top_y = (horizontals[0][0] + horizontals[0][1]) / 2
    bot_y = (horizontals[-1][0] + horizontals[-1][1]) / 2
    left_x = (verticals[0][0] + verticals[0][1]) / 2
    right_x = (verticals[-1][0] + verticals[-1][1]) / 2

    pts = np.array([
        [left_x, top_y],
        [right_x, top_y],
        [right_x, bot_y],
        [left_x, bot_y],
    ], dtype=np.float32)
    img_area = float(h * w)
    if _valid_quad(pts.reshape(4, 1, 2).astype(np.int32), img_area, cfg):
        return pts
    return None


def _strategy_line_reconstruct(image_bgr: np.ndarray,
                               cfg: CanonicalConfig) -> Optional[np.ndarray]:
    """Reconstruct the inner info-box from horizontal line clusters.

    When contour-based detection fails (broken vertical edges), this
    strategy finds two strong horizontal edge clusters in the upper
    portion of the image and uses their x-extents to form the rectangle.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (cfg.blur_ksize, cfg.blur_ksize), 0)
    edges = cv2.Canny(blurred, cfg.canny_low, cfg.canny_high)

    h, w = image_bgr.shape[:2]
    min_line_len = w // 6
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=60,
                            minLineLength=min_line_len, maxLineGap=25)
    if lines is None or len(lines) < 4:
        return None

    # Collect horizontal-ish line segments in the upper 75% of the image.
    # Store all four endpoint coordinates so we can fit lines later.
    HLine = Tuple[float, float, float, float, float, float]
    # (avg_y, length, x1, y1, x2, y2)
    horiz: List[HLine] = []
    for ln in lines:
        x1, y1, x2, y2 = ln[0]
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if angle < 15 or angle > 165:
            avg_y = (y1 + y2) / 2.0
            if avg_y < 0.75 * h:
                length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                horiz.append((avg_y, length,
                              float(x1), float(y1), float(x2), float(y2)))

    if len(horiz) < 4:
        return None

    # Cluster by y-position (gap relative to image height = new cluster)
    cluster_gap = max(15, int(h * 0.025))  # ~2.5% of image height
    horiz.sort(key=lambda l: l[0])
    clusters: List[List[HLine]] = []
    cur: List[HLine] = [horiz[0]]
    for i in range(1, len(horiz)):
        if horiz[i][0] - cur[-1][0] > cluster_gap:
            clusters.append(cur)
            cur = []
        cur.append(horiz[i])
    clusters.append(cur)

    # ---- Two-pass cluster analysis ----
    # Pass 1: Build initial cluster info using each cluster's own
    # longest segment as reference.
    def _cluster_info_from(segs, ref_left=None, ref_right=None):
        """Build cluster info dict.  If ref_left/ref_right given, filter
        segments so both endpoints lie within [ref_left-pad, ref_right+pad]."""
        if ref_left is not None and ref_right is not None:
            pad = 0.15 * (ref_right - ref_left)
            segs = [s for s in segs
                    if min(s[2], s[4]) >= ref_left - pad
                    and max(s[2], s[4]) <= ref_right + pad]
        if not segs:
            return None
        best = max(segs, key=lambda s: s[1])
        best_left = min(best[2], best[4])
        best_right = max(best[2], best[4])
        filt_x: List[float] = []
        filt_y: List[float] = []
        for seg in segs:
            filt_x.extend([seg[2], seg[4]])
            filt_y.extend([seg[3], seg[5]])
        return {
            'left_x': best_left,
            'right_x': best_right,
            'span': best_right - best_left,
            'pts_x': np.array(filt_x),
            'pts_y': np.array(filt_y),
            'segs': segs,
        }

    initial = []
    for c in clusters:
        info = _cluster_info_from(c)
        if info and info['span'] > 0.40 * w:
            info['mean_y'] = float(np.mean(info['pts_y']))
            initial.append((info, c))  # keep raw segs for pass 2
    if len(initial) < 2:
        return None

    # Sort by mean y — topmost cluster is the reference
    initial.sort(key=lambda x: x[0]['mean_y'])
    top_c = initial[0][0]
    ref_left = top_c['left_x']
    ref_right = top_c['right_x']

    # Pass 2: rebuild bottom cluster(s) using the TOP cluster's x-range
    # as a filter so outer-card lines extending beyond the inner box
    # are excluded.
    bot_c = None
    for info, raw_segs in initial[1:]:
        rebuilt = _cluster_info_from(raw_segs, ref_left, ref_right)
        if rebuilt and rebuilt['span'] > 0.30 * w:
            rebuilt['mean_y'] = float(np.mean(rebuilt['pts_y']))
            if bot_c is None or rebuilt['mean_y'] > bot_c['mean_y']:
                bot_c = rebuilt
    if bot_c is None:
        return None

    # The two clusters should be separated enough vertically
    height_gap = bot_c['mean_y'] - top_c['mean_y']
    if height_gap < 0.15 * h:
        return None

    # Fit a line y = a*x + b through each cluster's filtered endpoints
    # to capture the actual tilt of the edge.
    def _fit_line(pts_x, pts_y):
        """Return (slope, intercept) via least-squares."""
        if len(pts_x) < 2:
            return 0.0, float(np.mean(pts_y))
        A = np.vstack([pts_x, np.ones(len(pts_x))]).T
        result = np.linalg.lstsq(A, pts_y, rcond=None)
        slope, intercept = result[0]
        return float(slope), float(intercept)

    top_slope, top_b = _fit_line(top_c['pts_x'], top_c['pts_y'])
    bot_slope, bot_b = _fit_line(bot_c['pts_x'], bot_c['pts_y'])

    # Start with the TOP cluster's x-range, then EXTEND outward by
    # following the fitted border lines: check if dark pixels exist
    # near the predicted top/bottom y positions.
    left_x = ref_left
    right_x = ref_right

    step = 20
    search_band = 35  # ±px around predicted y (covers full border thickness)
    thresh_dark = 140

    # Extend rightward
    for x_probe in range(int(right_x) + step, w, step):
        pred_top_y = int(top_slope * x_probe + top_b)
        pred_bot_y = int(bot_slope * x_probe + bot_b)
        top_ok = False
        bot_ok = False
        if 0 <= pred_top_y - search_band and pred_top_y + search_band < h:
            strip = gray[max(0, pred_top_y - search_band):
                         pred_top_y + search_band, x_probe]
            top_ok = np.any(strip < thresh_dark)
        if 0 <= pred_bot_y - search_band and pred_bot_y + search_band < h:
            strip = gray[max(0, pred_bot_y - search_band):
                         pred_bot_y + search_band, x_probe]
            bot_ok = np.any(strip < thresh_dark)
        if top_ok or bot_ok:
            right_x = float(x_probe)
        else:
            break

    # Extend leftward
    for x_probe in range(int(left_x) - step, -1, -step):
        if x_probe < 0:
            break
        pred_top_y = int(top_slope * x_probe + top_b)
        pred_bot_y = int(bot_slope * x_probe + bot_b)
        top_ok = False
        bot_ok = False
        if 0 <= pred_top_y - search_band and pred_top_y + search_band < h:
            strip = gray[max(0, pred_top_y - search_band):
                         pred_top_y + search_band, x_probe]
            top_ok = np.any(strip < thresh_dark)
        if 0 <= pred_bot_y - search_band and pred_bot_y + search_band < h:
            strip = gray[max(0, pred_bot_y - search_band):
                         pred_bot_y + search_band, x_probe]
            bot_ok = np.any(strip < thresh_dark)
        if top_ok or bot_ok:
            left_x = float(x_probe)
        else:
            break

    # Evaluate fitted lines at left_x and right_x to get actual corner y's
    tl_y = top_slope * left_x + top_b
    tr_y = top_slope * right_x + top_b
    bl_y = bot_slope * left_x + bot_b
    br_y = bot_slope * right_x + bot_b

    # Validate proportions
    box_w = right_x - left_x
    box_h = ((bl_y - tl_y) + (br_y - tr_y)) / 2.0
    if box_h < 50 or box_w < 100:
        return None
    ar = box_w / box_h
    if ar < cfg.aspect_ratio_range[0] or ar > cfg.aspect_ratio_range[1]:
        return None

    # Ensure it's in the inner-box region (bot < 75% of image)
    if max(bl_y, br_y) >= 0.75 * h:
        return None

    quad = np.array([
        [left_x, tl_y],
        [right_x, tr_y],
        [right_x, br_y],
        [left_x, bl_y],
    ], dtype=np.float32)
    return _order_points(quad)


def _all_quads(contours, img_shape, cfg: CanonicalConfig) -> List[np.ndarray]:
    """Find ALL valid quadrilateral contours (sorted by area desc).

    Tries multiple epsilon values for approxPolyDP and also uses
    minAreaRect for large contours that don't simplify to 4 vertices.
    """
    h, w = img_shape[:2]
    img_area = float(h * w)
    seen_areas = set()  # deduplicate by rounded area
    candidates = []

    epsilons = [cfg.approx_epsilon_ratio, 0.03, 0.04, 0.05]
    # deduplicate epsilon list while preserving order
    used_eps = []
    for e in epsilons:
        if e not in used_eps:
            used_eps.append(e)

    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        cnt_area = cv2.contourArea(cnt)
        if cnt_area / img_area < cfg.min_area_ratio:
            continue

        found_quad = False
        for eps in used_eps:
            approx = cv2.approxPolyDP(cnt, eps * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                if _valid_quad(approx, img_area, cfg):
                    area = cv2.contourArea(approx)
                    area_key = round(area / 1000)
                    if area_key not in seen_areas:
                        seen_areas.add(area_key)
                        candidates.append((area, approx))
                    found_quad = True
                    break  # first epsilon that works

        # Fallback: minAreaRect for large contours that didn't simplify
        if not found_quad:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box_int = box.astype(np.int32).reshape(4, 1, 2)
            if _valid_quad(box_int, img_area, cfg):
                area = cv2.contourArea(box_int)
                area_key = round(area / 1000)
                if area_key not in seen_areas:
                    seen_areas.add(area_key)
                    candidates.append((area, box_int))

    if not candidates:
        return []

    # Return all valid quads, sorted by area descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [_order_points(c[1].reshape(4, 2)) for c in candidates]


# ---------------------------------------------------------- normalizer ---

class CanonicalNormalizer:
    """Detect the inner English info-box border of a Nepal citizenship card
    and warp it to a fixed 1200×600 canonical image.
    """

    def __init__(self, cfg: Optional[CanonicalConfig] = None):
        self.cfg = cfg or CanonicalConfig()

    # ---- border detection ------------------------------------------

    def _detect_border(self, image_bgr: np.ndarray) -> Tuple[Optional[np.ndarray], str]:
        """Try multiple strategies, collect all quads, prefer inner English box."""
        strategies = [
            ("canny_edge", _strategy_canny),
            ("adaptive_threshold", _strategy_adaptive_threshold),
            ("color_border", _strategy_color_border),
            ("hough_lines", _strategy_hough_lines),
        ]
        if not self.cfg.multi_strategy:
            strategies = strategies[:1]

        h, w = image_bgr.shape[:2]

        # Collect all candidate quads from all strategies
        all_candidates: List[Tuple[np.ndarray, str]] = []
        for name, fn in strategies:
            if name == "hough_lines":
                corners = fn(image_bgr, self.cfg)
                if corners is not None:
                    all_candidates.append((corners, name))
            else:
                quads = fn(image_bgr, self.cfg)
                for q in quads:
                    all_candidates.append((q, name))

        if not all_candidates:
            return None, ""

        # Separate inner (English info-box) vs outer (full card) quads.
        # The inner box sits in the upper portion of the card, so its
        # bottom-y should be < 75% of image height (relaxed for tilted/
        # zoomed images where the box can be lower than expected).
        inner = []
        outer = []
        for corners, name in all_candidates:
            ordered = _order_points(
                corners.reshape(4, 2) if corners.ndim == 3 else corners)
            bottom_y = max(ordered[2][1], ordered[3][1])
            top_y = min(ordered[0][1], ordered[1][1])
            quad_h = bottom_y - top_y
            if bottom_y < 0.75 * h and quad_h < 0.75 * h:
                area = cv2.contourArea(ordered.astype(np.int32))
                # Score by area AND how close aspect ratio is to ~2:1
                w_top = np.linalg.norm(ordered[1] - ordered[0])
                w_bot = np.linalg.norm(ordered[2] - ordered[3])
                h_left = np.linalg.norm(ordered[3] - ordered[0])
                h_right = np.linalg.norm(ordered[2] - ordered[1])
                avg_w = (w_top + w_bot) / 2
                avg_h_q = (h_left + h_right) / 2
                ar = avg_w / max(1, avg_h_q)
                # Ideal AR for Nepal citizenship inner box is ~2.0
                ar_score = 1.0 / (1.0 + abs(ar - 2.0))
                composite_score = area * ar_score
                inner.append((composite_score, ordered, name))
            else:
                area = cv2.contourArea(ordered.astype(np.int32))
                outer.append((area, ordered, name))

        if inner:
            inner.sort(key=lambda x: x[0], reverse=True)
            best = self._refine_corners(inner[0][1], image_bgr)
            return best, inner[0][2]

        # -- Line reconstruction: inner box edges exist but don't
        #    form closed contours (e.g. broken/missing vertical edges).
        line_quad = _strategy_line_reconstruct(image_bgr, self.cfg)
        if line_quad is not None:
            return line_quad, "line_reconstruct"

        # -- Deskew stage: no inner box found directly --
        # The image may be tilted so the inner box contour doesn't close
        # into a clean quad.  Detect the tilt angle from the inner dark
        # rectangular mark itself (via minAreaRect on contours that match
        # inner-box geometry), rotate the image to straighten it, then
        # re-run full inner-box detection.
        tilt = self._detect_inner_rect_tilt(image_bgr)
        if tilt is not None:
            inner2 = self._deskew_and_detect_inner(image_bgr, tilt)
            if inner2 is not None:
                return inner2, "inner_deskew"

        # Fall back to the largest outer box
        if outer:
            outer.sort(key=lambda x: x[0], reverse=True)
            return outer[0][1], outer[0][2]

        return None, ""

    def _detect_inner_rect_tilt(self, image_bgr: np.ndarray) -> Optional[float]:
        """Detect the tilt angle of the inner rectangular border.

        Look for contours that match inner-box geometry (area 12-55%,
        AR 1.3-4.5, centre in upper 60%).  Use minAreaRect to get the
        tilt angle.  Returns angle in degrees if > 0.3°, else None.
        """
        h, w = image_bgr.shape[:2]
        img_area = float(h * w)

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (self.cfg.blur_ksize, self.cfg.blur_ksize), 0)
        edges = cv2.Canny(blurred, self.cfg.canny_low, self.cfg.canny_high)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (self.cfg.morph_ksize, self.cfg.morph_ksize))
        edges = cv2.dilate(edges, kernel, iterations=self.cfg.dilate_iterations)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE,
                                       cv2.CHAIN_APPROX_SIMPLE)

        best_angle = None
        best_area = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            ratio = area / img_area
            if ratio < 0.08 or ratio > 0.65:
                continue
            rect = cv2.minAreaRect(cnt)
            (cx, cy), (rw, rh), angle = rect
            if rw < 1 or rh < 1:
                continue
            long_side = max(rw, rh)
            short_side = min(rw, rh)
            ar = long_side / short_side
            if ar < 1.3 or ar > 4.5:
                continue
            # Centre should be in the upper 75% of the image
            if cy > 0.75 * h:
                continue
            # Normalise angle: minAreaRect returns angle in [-90, 0)
            # We want the deviation from horizontal
            if rw < rh:
                angle = angle + 90
            if angle > 45:
                angle -= 90
            if area > best_area:
                best_area = area
                best_angle = angle

        if best_angle is not None and abs(best_angle) > 0.3:
            return best_angle
        return None

    def _deskew_and_detect_inner(self, image_bgr: np.ndarray,
                                 angle: float) -> Optional[np.ndarray]:
        """Rotate image by -angle and re-detect the inner border.

        Returns the inner-box quad corners mapped back to original image
        coordinates, or None if detection failed.
        """
        h, w = image_bgr.shape[:2]
        cx, cy = w / 2.0, h / 2.0

        # Compute rotation matrix with expanded canvas
        M_rot = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
        cos_a = abs(M_rot[0, 0])
        sin_a = abs(M_rot[0, 1])
        new_w = int(w * cos_a + h * sin_a)
        new_h = int(h * cos_a + w * sin_a)
        M_rot[0, 2] += (new_w - w) / 2.0
        M_rot[1, 2] += (new_h - h) / 2.0

        rotated = cv2.warpAffine(
            image_bgr, M_rot, (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        # Re-run contour-based strategies on the straightened image
        strategies_2 = [
            ("canny_edge", _strategy_canny),
            ("adaptive_threshold", _strategy_adaptive_threshold),
            ("color_border", _strategy_color_border),
        ]

        inner_candidates = []
        for _name, fn in strategies_2:
            quads = fn(rotated, self.cfg)
            for q in quads:
                q2 = _order_points(q.reshape(4, 2) if q.ndim == 3 else q)
                bottom_y = max(q2[2][1], q2[3][1])
                top_y = min(q2[0][1], q2[1][1])
                quad_h = bottom_y - top_y
                if bottom_y < 0.78 * new_h and quad_h < 0.75 * new_h:
                    area = cv2.contourArea(q2.astype(np.int32))
                    inner_candidates.append((area, q2))

        # Also try Hough-line based construction on the rotated image
        if not inner_candidates:
            hough_quad = self._hough_inner_box(rotated)
            if hough_quad is not None:
                area = cv2.contourArea(hough_quad.astype(np.int32))
                inner_candidates.append((area, hough_quad))

        if not inner_candidates:
            return None

        inner_candidates.sort(key=lambda x: x[0], reverse=True)
        inner_rot = inner_candidates[0][1]

        # Map corners back to original image coordinates via inverse affine
        M_full = np.vstack([M_rot, [0, 0, 1]])
        M_inv = np.linalg.inv(M_full)
        pts_h = np.hstack([inner_rot, np.ones((4, 1))])
        original_pts = (M_inv @ pts_h.T).T
        return original_pts[:, :2].astype(np.float32)

    def _hough_inner_box(self, image_bgr: np.ndarray) -> Optional[np.ndarray]:
        """Attempt to construct the inner box from strong Hough lines
        (horizontal edges) and vertical edge projections.
        """
        h, w = image_bgr.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 120)

        min_line_len = w // 4
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80,
                                minLineLength=min_line_len, maxLineGap=20)
        if lines is None or len(lines) < 2:
            return None

        # Collect strong horizontal lines in the upper 75% of the image
        horizontals = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if angle < 15 or angle > 165:
                avg_y = (y1 + y2) / 2.0
                length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                if avg_y < 0.75 * h:
                    horizontals.append((avg_y, length, x1, x2))

        if len(horizontals) < 2:
            return None

        # Cluster by y-position
        horizontals.sort(key=lambda l: l[0])
        clusters = []
        cur_cluster = [horizontals[0]]
        for i in range(1, len(horizontals)):
            if abs(horizontals[i][0] - cur_cluster[-1][0]) < 15:
                cur_cluster.append(horizontals[i])
            else:
                clusters.append(cur_cluster)
                cur_cluster = [horizontals[i]]
        clusters.append(cur_cluster)

        if len(clusters) < 2:
            return None

        # Pick top and bottom clusters by total length
        cluster_info = []
        for c in clusters:
            avg_y = np.mean([l[0] for l in c])
            total_len = sum(l[1] for l in c)
            min_x = min(min(l[2], l[3]) for l in c)
            max_x = max(max(l[2], l[3]) for l in c)
            cluster_info.append((avg_y, total_len, min_x, max_x))

        cluster_info.sort(key=lambda c: c[0])
        top_y = cluster_info[0][0]
        bot_y = cluster_info[-1][0]
        left_x = min(c[2] for c in cluster_info[:2])
        right_x = max(c[3] for c in cluster_info[:2])

        # Validate proportions
        box_h = bot_y - top_y
        box_w = right_x - left_x
        if box_h < 50 or box_w < 100:
            return None
        ar = box_w / box_h
        if ar < 1.3 or ar > 4.5:
            return None

        quad = np.array([
            [left_x, top_y],
            [right_x, top_y],
            [right_x, bot_y],
            [left_x, bot_y],
        ], dtype=np.float32)
        return _order_points(quad)

    # ---- warping ---------------------------------------------------

    def _refine_corners(self, corners: np.ndarray,
                        image_bgr: np.ndarray) -> np.ndarray:
        """Refine corner positions using local horizontal-edge analysis.

        Contour-based detection can place a corner where the border is
        faint or absent (broken edge, shadow, etc.).  This method:

        1.  For each corner, finds the nearest *strong* horizontal edge
            within ±80 pixels using the Sobel gradient magnitude.
        2.  Any corner without a strong nearby edge is predicted from
            the other three corners (same-side height from the opposite
            strong pair).

        This ensures the final four corners lie on actual border edges,
        producing a distortion-free perspective warp.
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        h, w = image_bgr.shape[:2]
        sobel_y = np.abs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5))

        ordered = _order_points(
            corners.reshape(4, 2) if corners.ndim == 3 else corners
        ).astype(np.float64)
        refined = ordered.copy()

        SEARCH_Y = 80       # search ±80 pixels in y
        STRIP_HALF_X = 20   # average over ±20 pixels in x
        STRONG_EDGE = 500    # minimum Sobel magnitude for a "real" edge

        # Phase 1: snap each corner to the nearest strong horizontal edge
        peak_str = np.zeros(4)
        for i in range(4):
            cx, cy = int(ordered[i][0]), int(ordered[i][1])
            x0 = max(0, cx - STRIP_HALF_X)
            x1 = min(w, cx + STRIP_HALF_X)
            y0 = max(0, cy - SEARCH_Y)
            y1 = min(h, cy + SEARCH_Y)
            strip = sobel_y[y0:y1, x0:x1].mean(axis=1)

            # Collect local-maxima peaks above threshold
            peaks = []
            for j in range(1, len(strip) - 1):
                if (strip[j] > strip[j - 1]
                        and strip[j] >= strip[j + 1]
                        and strip[j] >= STRONG_EDGE):
                    peaks.append((abs(y0 + j - cy), y0 + j, strip[j]))

            if peaks:
                peaks.sort()                     # nearest first
                peak_str[i] = peaks[0][2]
                refined[i][1] = float(peaks[0][1])

        # Phase 2: predict weak corners from the strong opposite pair
        # Corners: 0=TL, 1=TR, 2=BR, 3=BL
        left_ok  = peak_str[0] >= STRONG_EDGE and peak_str[3] >= STRONG_EDGE
        right_ok = peak_str[1] >= STRONG_EDGE and peak_str[2] >= STRONG_EDGE

        if right_ok and not left_ok:
            right_h = refined[2][1] - refined[1][1]
            if peak_str[0] >= STRONG_EDGE and peak_str[3] < STRONG_EDGE:
                refined[3][1] = refined[0][1] + right_h
            elif peak_str[3] >= STRONG_EDGE and peak_str[0] < STRONG_EDGE:
                refined[0][1] = refined[3][1] - right_h
        elif left_ok and not right_ok:
            left_h = refined[3][1] - refined[0][1]
            if peak_str[1] >= STRONG_EDGE and peak_str[2] < STRONG_EDGE:
                refined[2][1] = refined[1][1] + left_h
            elif peak_str[2] >= STRONG_EDGE and peak_str[1] < STRONG_EDGE:
                refined[1][1] = refined[2][1] - left_h

        # Clamp to image bounds
        refined[:, 0] = np.clip(refined[:, 0], 0, w - 1)
        refined[:, 1] = np.clip(refined[:, 1], 0, h - 1)

        return refined.astype(np.float32)

    def _pad_corners(self, corners: np.ndarray,
                     img_shape: tuple) -> np.ndarray:
        """Expand the detected inner-box corners outward by a margin
        so that text sitting right on the border line is not cropped.

        The Nepal citizenship card has labels (Citizenship Certificate No.,
        Full Name, etc.) that START right at the inner border.  Without
        padding the warp clips those first few characters.

        Uses axis-aligned padding: 5% of box width on left/right,
        3% of box height on top/bottom.  This is asymmetric because
        labels are tighter to the left/right borders than top/bottom.
        """
        ordered = _order_points(
            corners.reshape(4, 2) if corners.ndim == 3 else corners)
        h_img, w_img = img_shape[:2]

        # Compute box width/height
        w_top = np.linalg.norm(ordered[1] - ordered[0])
        w_bot = np.linalg.norm(ordered[2] - ordered[3])
        h_left = np.linalg.norm(ordered[3] - ordered[0])
        h_right = np.linalg.norm(ordered[2] - ordered[1])
        box_w = (w_top + w_bot) / 2.0
        box_h = (h_left + h_right) / 2.0

        pad_x = box_w * 0.05   # 5% horizontal padding
        pad_y = box_h * 0.04   # 4% vertical padding

        # TL: move left and up
        ordered[0][0] -= pad_x
        ordered[0][1] -= pad_y
        # TR: move right and up
        ordered[1][0] += pad_x
        ordered[1][1] -= pad_y
        # BR: move right and down
        ordered[2][0] += pad_x
        ordered[2][1] += pad_y
        # BL: move left and down
        ordered[3][0] -= pad_x
        ordered[3][1] += pad_y

        # Clamp to image bounds
        ordered[:, 0] = np.clip(ordered[:, 0], 0, w_img - 1)
        ordered[:, 1] = np.clip(ordered[:, 1], 0, h_img - 1)

        return ordered

    def _warp(self, image_bgr: np.ndarray,
              corners: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Perspective-warp the region defined by *corners* to canonical size.

        Applies outward padding first so edge text is not clipped.
        """
        padded = self._pad_corners(corners, image_bgr.shape)
        M, dst = _compute_homography(
            padded, self.cfg.canonical_width, self.cfg.canonical_height)
        warped = cv2.warpPerspective(
            image_bgr, M,
            (self.cfg.canonical_width, self.cfg.canonical_height))
        return warped, M

    # ---- public API ------------------------------------------------

    def normalize(self, image_path: str) -> CanonicalResult:
        """Load an image from disk and produce the canonical output."""
        try:
            img = _load_bgr(image_path)
        except ValueError as exc:
            return CanonicalResult(
                canonical_image=np.zeros((self.cfg.canonical_height,
                                          self.cfg.canonical_width, 3),
                                         dtype=np.uint8),
                metadata=WarpMetadata(
                    original_corners=[], canonical_size=(
                        self.cfg.canonical_width, self.cfg.canonical_height)),
                success=False, error=str(exc),
            )
        return self.normalize_array(img)

    def normalize_array(self, image_bgr: np.ndarray) -> CanonicalResult:
        """Normalise an already-loaded BGR image array."""
        corners, strategy = self._detect_border(image_bgr)

        if corners is None:
            h, w = image_bgr.shape[:2]
            # Fallback: use entire image
            corners = np.array([
                [0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]
            ], dtype=np.float32)
            strategy = "fallback_full_image"

        warped, M = self._warp(image_bgr, corners)

        metadata = WarpMetadata(
            original_corners=corners.astype(int).tolist(),
            canonical_size=(self.cfg.canonical_width, self.cfg.canonical_height),
            homography_matrix=M.tolist() if M is not None else None,
            strategy_used=strategy,
            explanation=f"Border detected via '{strategy}' strategy.",
        )
        return CanonicalResult(canonical_image=warped, metadata=metadata)

    def save_canonical(self, result: CanonicalResult, path: str) -> None:
        """Save the canonical image to *path*."""
        cv2.imwrite(path, result.canonical_image)


# ----------------------------------------------------------------- CLI ---

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python canonical_normalizer.py <image_path> [output_path]")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "canonical.png"

    normalizer = CanonicalNormalizer()
    result = normalizer.normalize(in_path)
    if result.success:
        normalizer.save_canonical(result, out_path)
        print(f"Saved canonical image → {out_path}")
        print(f"  strategy : {result.metadata.strategy_used}")
        print(f"  corners  : {result.metadata.original_corners}")
    else:
        print(f"FAILED: {result.error}")
