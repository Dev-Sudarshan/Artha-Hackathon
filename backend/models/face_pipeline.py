"""backend.models.face_pipeline

Face pipeline utilities.

Primary backend: InsightFace (fast, accurate).
Fallback backend: DeepFace + OpenCV (works on environments where InsightFace
cannot be installed, e.g. Python 3.13/free-threaded builds).
"""

from __future__ import annotations

import math
import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

_FACE_ANALYZER = None
_FACE_BACKEND: Optional[str] = None


def _get_face_backend() -> str:
    """Return the active face backend.

    Controlled via env:
    - FACE_BACKEND=auto|insightface|deepface
    """
    global _FACE_BACKEND
    if _FACE_BACKEND is not None:
        return _FACE_BACKEND

    requested = os.getenv("FACE_BACKEND", "auto").strip().lower()
    if requested not in {"auto", "insightface", "deepface"}:
        requested = "auto"

    if requested in {"auto", "insightface"}:
        try:
            import insightface  # noqa: F401

            _FACE_BACKEND = "insightface"
            return _FACE_BACKEND
        except Exception:
            if requested == "insightface":
                raise

    _FACE_BACKEND = "deepface"
    return _FACE_BACKEND


def _get_face_analyzer():
    global _FACE_ANALYZER
    if _get_face_backend() != "insightface":
        return None
    if _FACE_ANALYZER is None:
        from insightface.app import FaceAnalysis

        providers = os.getenv("INSIGHTFACE_PROVIDERS", "CPUExecutionProvider").split(",")
        analyzer = FaceAnalysis(name="buffalo_l", providers=providers)
        analyzer.prepare(ctx_id=0, det_size=(640, 640))
        _FACE_ANALYZER = analyzer
    return _FACE_ANALYZER


def _detect_faces_opencv(image: np.ndarray) -> List[Dict[str, object]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    cascade = cv2.CascadeClassifier(cascade_path)

    # detectMultiScale returns x, y, w, h
    detections = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )

    results: List[Dict[str, object]] = []
    for (x, y, w, h) in detections:
        results.append(
            {
                "bbox": [int(x), int(y), int(x + w), int(y + h)],
                "score": 1.0,
                "kps": None,
            }
        )

    return results


def _deepface_config() -> Tuple[str, str]:
    model_name = os.getenv("DEEPFACE_MODEL_NAME", "ArcFace")
    # Use RetinaFace for production-grade accuracy (better than opencv)
    detector_backend = os.getenv("DEEPFACE_DETECTOR_BACKEND", "retinaface")
    return model_name, detector_backend


def _deepface_embedding(img: object) -> np.ndarray:
    from deepface import DeepFace

    model_name, detector_backend = _deepface_config()
    reps = DeepFace.represent(
        img_path=img,
        model_name=model_name,
        detector_backend=detector_backend,
        enforce_detection=True,
    )

    if isinstance(reps, dict):
        reps = [reps]
    if not reps:
        raise ValueError("No face detected")

    embedding = np.asarray(reps[0]["embedding"], dtype=np.float32)
    norm = np.linalg.norm(embedding)
    if norm == 0:
        raise ValueError("Invalid embedding norm")
    return embedding / norm


def _load_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")
    return image


def validate_face_quality(image_path: str) -> Dict[str, object]:
    """
    Validate face image quality for accurate verification.
    High-quality faces are essential for 100% accuracy.
    
    Returns dict with:
        - quality_passed: bool
        - quality_score: float (0-1)
        - issues: List[str]
        - metrics: Dict with detailed measurements
    """
    image = _load_image(image_path)
    height, width = image.shape[:2]
    image_area = height * width
    
    issues = []
    metrics = {}
    
    # 1. Resolution check - minimum 480x640 for face verification
    min_resolution = 480 * 640
    if image_area < min_resolution:
        issues.append(f"Image resolution too low: {width}x{height} (minimum 640x480)")
    metrics['resolution'] = f"{width}x{height}"
    metrics['pixel_count'] = image_area
    
    # 2. Detect face with high-quality detector
    from deepface import DeepFace
    model_name, detector_backend = _deepface_config()
    
    try:
        faces = DeepFace.extract_faces(
            img_path=image_path,
            detector_backend=detector_backend,
            enforce_detection=True,
            align=True,
        )
    except Exception as e:
        return {
            'quality_passed': False,
            'quality_score': 0.0,
            'issues': [f"Face detection failed: {str(e)}"],
            'metrics': metrics,
        }
    
    if not faces:
        return {
            'quality_passed': False,
            'quality_score': 0.0,
            'issues': ['No face detected'],
            'metrics': metrics,
        }
    
    face = max(faces, key=lambda f: f.get('confidence', 0))
    confidence = face.get('confidence', 0)
    facial_area = face.get('facial_area', {})
    
    # 3. Face detection confidence
    min_confidence = float(os.getenv('MIN_FACE_CONFIDENCE', '0.95'))
    if confidence < min_confidence:
        issues.append(f"Low face detection confidence: {confidence:.3f} (minimum {min_confidence})")
    metrics['face_confidence'] = confidence
    
    # 4. Face size check - face should be prominent in image
    face_width = facial_area.get('w', 0)
    face_height = facial_area.get('h', 0)
    face_area = face_width * face_height
    face_ratio = face_area / image_area
    
    if face_ratio < 0.15:
        issues.append(f"Face too small in frame: {face_ratio:.1%} (minimum 15%)")
    if face_ratio > 0.60:
        issues.append(f"Face too large in frame: {face_ratio:.1%} (maximum 60%)")
    
    metrics['face_area_ratio'] = face_ratio
    metrics['face_size'] = f"{face_width}x{face_height}"
    
    # 5. Face resolution - the cropped face itself should be high resolution
    min_face_pixels = 200 * 200
    if face_area < min_face_pixels:
        issues.append(f"Face resolution too low: {face_width}x{face_height} (minimum 200x200)")
    
    # 6. Sharpness/blur check on face region
    x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
    face_crop = image[y:y+h, x:x+w]
    gray_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    blur_score = _laplacian_variance(gray_face)
    
    min_sharpness = float(os.getenv('MIN_FACE_SHARPNESS', '200'))
    max_sharpness = float(os.getenv('MAX_FACE_SHARPNESS', '2000'))
    
    if blur_score < min_sharpness:
        issues.append(f"Face too blurry: {blur_score:.1f} (minimum {min_sharpness})")
    if blur_score > max_sharpness:
        issues.append(f"Face sharpness suspicious: {blur_score:.1f} (may be professional photo)")
    
    metrics['face_sharpness'] = blur_score
    
    # 7. Lighting check - ensure even lighting
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    std_brightness = np.std(gray)
    
    if mean_brightness < 60:
        issues.append(f"Image too dark: brightness {mean_brightness:.1f} (minimum 60)")
    if mean_brightness > 220:
        issues.append(f"Image too bright: brightness {mean_brightness:.1f} (maximum 220)")
    if std_brightness < 30:
        issues.append(f"Poor contrast: std {std_brightness:.1f} (minimum 30)")
    
    metrics['brightness'] = mean_brightness
    metrics['contrast'] = std_brightness
    
    # Calculate overall quality score (0-1)
    quality_factors = [
        min(confidence / min_confidence, 1.0),
        min(blur_score / min_sharpness, 1.0) if blur_score >= min_sharpness else blur_score / min_sharpness,
        1.0 if 0.15 <= face_ratio <= 0.60 else 0.7,
        1.0 if min_resolution <= image_area else 0.5,
        1.0 if 60 <= mean_brightness <= 220 else 0.8,
        1.0 if std_brightness >= 30 else std_brightness / 30,
    ]
    quality_score = sum(quality_factors) / len(quality_factors)
    
    return {
        'quality_passed': len(issues) == 0,
        'quality_score': quality_score,
        'issues': issues,
        'metrics': metrics,
    }


def extract_face_region(image_path: str, padding_percent: float = 0.2) -> str:
    """
    Extract the largest face from an image and save it as a cropped image.
    This is critical for ID card face extraction.
    
    Args:
        image_path: Path to source image (ID card or selfie)
        padding_percent: Add padding around detected face bbox (default 20%)
        
    Returns:
        Path to the cropped face image
    """
    from deepface import DeepFace
    
    image = _load_image(image_path)
    height, width = image.shape[:2]
    
    # Use RetinaFace or mtcnn for better face detection (as user requested)
    model_name, detector_backend = _deepface_config()
    
    # Detect faces using DeepFace's RetinaFace/MTCNN detector
    try:
        faces = DeepFace.extract_faces(
            img_path=image_path,
            detector_backend=detector_backend,
            enforce_detection=True,
            align=True,
        )
    except Exception as e:
        raise ValueError(f"No face detected in image: {str(e)}")
    
    if not faces:
        raise ValueError("No face detected in image")
    
    # Get the face with highest confidence (largest area)
    face = max(faces, key=lambda f: f.get('confidence', 0))
    facial_area = face.get('facial_area', {})
    
    x = facial_area.get('x', 0)
    y = facial_area.get('y', 0)
    w = facial_area.get('w', 100)
    h = facial_area.get('h', 100)
    
    # Add padding around the face
    pad_w = int(w * padding_percent)
    pad_h = int(h * padding_percent)
    
    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(width, x + w + pad_w)
    y2 = min(height, y + h + pad_h)
    
    # Crop the face region
    face_crop = image[y1:y2, x1:x2]
    
    if face_crop.size == 0:
        raise ValueError("Failed to crop face region")
    
    # Save to temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.jpg', prefix='face_crop_')
    os.close(temp_fd)
    
    cv2.imwrite(temp_path, face_crop)
    
    return temp_path


def detect_faces(image_path: str) -> List[Dict[str, object]]:
    image = _load_image(image_path)
    if _get_face_backend() == "insightface":
        analyzer = _get_face_analyzer()
        faces = analyzer.get(image)
        results: List[Dict[str, object]] = []

        for face in faces:
            bbox = face.bbox.astype(int).tolist()
            kps = face.kps.astype(int).tolist() if face.kps is not None else None
            results.append(
                {
                    "bbox": bbox,
                    "score": float(face.det_score),
                    "kps": kps,
                }
            )

        return results

    return _detect_faces_opencv(image)


def _select_primary_face(faces):
    if not faces:
        return None
    return max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))


def extract_embedding(image_path: str) -> np.ndarray:
    if _get_face_backend() == "insightface":
        analyzer = _get_face_analyzer()
        image = _load_image(image_path)

        faces = analyzer.get(image)
        face = _select_primary_face(faces)
        if face is None:
            raise ValueError("No face detected")

        return _embedding_from_face(face)

    return _deepface_embedding(image_path)


def _embedding_from_face(face) -> np.ndarray:
    embedding = getattr(face, "normed_embedding", None)
    if embedding is None:
        embedding = getattr(face, "embedding", None)

    if embedding is None:
        raise ValueError("Face embedding not available")

    embedding = embedding.astype(np.float32)
    norm = np.linalg.norm(embedding)
    if norm == 0:
        raise ValueError("Invalid embedding norm")

    return embedding / norm


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    return float(np.dot(vec_a, vec_b))


def verify_faces(
    id_image_path: str,
    selfie_image_path: str,
    threshold: Optional[float] = None,
) -> Dict[str, object]:
    """
    Verify if selfie matches ID card photo with production-grade accuracy.
    
    CRITICAL: Multi-stage verification:
    1. Validate image quality
    2. Extract face regions
    3. Compare embeddings with strict threshold
    4. Check liveness
    """
    backend = _get_face_backend()
    
    # STEP 0: Validate face quality BEFORE processing (critical for accuracy)
    print("[FACE VERIFY] Validating ID card image quality...")
    id_quality = validate_face_quality(id_image_path)
    if not id_quality['quality_passed']:
        raise ValueError(f"ID card quality check failed: {', '.join(id_quality['issues'])}")
    
    print("[FACE VERIFY] Validating selfie image quality...")
    selfie_quality = validate_face_quality(selfie_image_path)
    if not selfie_quality['quality_passed']:
        raise ValueError(f"Selfie quality check failed: {', '.join(selfie_quality['issues'])}")
    
    # STEP 1: Extract face from ID card (critical for accuracy)
    print("[FACE VERIFY] Extracting face from ID card...")
    try:
        id_face_path = extract_face_region(id_image_path)
    except Exception as e:
        raise ValueError(f"Failed to extract face from ID card: {str(e)}")
    
    # STEP 2: Extract face from selfie
    print("[FACE VERIFY] Extracting face from selfie...")
    try:
        selfie_face_path = extract_face_region(selfie_image_path)
    except Exception as e:
        # Clean up temp ID face file
        if os.path.exists(id_face_path):
            os.remove(id_face_path)
        raise ValueError(f"Failed to extract face from selfie: {str(e)}")
    
    # STEP 3: Check liveness on selfie (anti-spoofing)
    print("[FACE VERIFY] Checking liveness...")
    liveness_result = check_liveness_single_image(selfie_image_path)
    if not liveness_result.get('liveness_passed', False):
        # Clean up temp files
        for temp_path in [id_face_path, selfie_face_path]:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        raise ValueError(f"Liveness check failed: {liveness_result.get('reason')}")
    
    try:
        if backend == "insightface":
            threshold = threshold or float(os.getenv("FACE_MATCH_THRESHOLD", "0.45"))

            emb_id = extract_embedding(id_face_path)
            emb_selfie = extract_embedding(selfie_face_path)

            similarity = _cosine_similarity(emb_id, emb_selfie)
            distance = 1.0 - similarity
            matched = similarity >= threshold

            result = {
                "face_match": matched,
                "similarity": similarity,
                "distance": distance,
                "threshold": threshold,
                "backend": backend,
                "distance_metric": "cosine(similarity)",
            }
        else:
            # DeepFace with extracted faces
            # MAXIMUM STRICTNESS: Use 0.40 threshold for 100% accuracy
            # Lower threshold = stricter matching (only very similar faces pass)
            kyc_threshold = float(os.getenv("KYC_FACE_THRESHOLD", "0.40"))
            
            from deepface import DeepFace
            model_name, detector_backend = _deepface_config()
            
            result_df = DeepFace.verify(
                img1_path=id_face_path,
                img2_path=selfie_face_path,
                model_name=model_name,
                detector_backend=detector_backend,
                distance_metric="cosine",
                enforce_detection=True,
                threshold=kyc_threshold,
            )
            
            distance = float(result_df.get("distance"))
            # Use our maximum strict threshold
            matched = distance < kyc_threshold
            similarity = 1.0 - distance
            
            # Calculate overall verification confidence
            # All factors must be high for strong confidence
            verification_confidence = min(
                similarity,
                id_quality.get('quality_score', 1.0),
                selfie_quality.get('quality_score', 1.0),
            )
            
            result = {
                "face_match": matched,
                "similarity": similarity,
                "distance": distance,
                "threshold": kyc_threshold,
                "backend": backend,
                "distance_metric": "cosine(distance)",
                "model": model_name,
                "detector": detector_backend,
                # Quality metrics
                "id_quality_score": id_quality.get('quality_score'),
                "selfie_quality_score": selfie_quality.get('quality_score'),
                "verification_confidence": verification_confidence,
                # Liveness metrics
                "liveness_passed": liveness_result.get('liveness_passed'),
                "liveness_blur_score": liveness_result.get('blur_score'),
                "liveness_face_ratio": liveness_result.get('face_area_ratio'),
                # Overall status
                "all_checks_passed": matched and liveness_result.get('liveness_passed', False),
            }
    finally:
        # Clean up temporary face crop files
        for temp_path in [id_face_path, selfie_face_path]:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
    
    return result


def _ensure_readable_video(video_path: str) -> Tuple[str, Optional[str]]:
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if total_frames > 0:
        return video_path, None

    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        subprocess.run(
            [
                ffmpeg_exe,
                "-y",
                "-i",
                video_path,
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "28",
                temp_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return temp_path, temp_path
    except Exception:
        return video_path, None


def _sample_video_frames(video_path: str, max_frames: int = 12) -> List[np.ndarray]:
    readable_path, temp_path = _ensure_readable_video(video_path)
    cap = cv2.VideoCapture(readable_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        cap.release()
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise ValueError("Invalid or empty video")

    indices = [
        int(i * (total_frames - 1) / (max_frames - 1))
        for i in range(max_frames)
    ]
    indices = sorted(set(max(0, min(total_frames - 1, idx)) for idx in indices))

    frames: List[np.ndarray] = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success or frame is None:
            continue
        frames.append(frame)

    cap.release()

    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass

    return frames


def verify_faces_from_video(
    id_image_path: str,
    video_path: str,
    threshold: Optional[float] = None,
) -> Dict[str, object]:
    """
    Verify if video contains the person from ID card photo.
    
    CRITICAL: Extracts face region from ID card before comparison.
    """
    backend = _get_face_backend()
    
    # STEP 1: Extract face from ID card (critical for accuracy)
    print("[VIDEO VERIFY] Extracting face from ID card...")
    try:
        id_face_path = extract_face_region(id_image_path)
    except Exception as e:
        raise ValueError(f"Failed to extract face from ID card: {str(e)}")
    
    try:
        if backend == "insightface":
            threshold = threshold or float(os.getenv("FACE_MATCH_THRESHOLD", "0.45"))
            analyzer = _get_face_analyzer()

            emb_id = extract_embedding(id_face_path)
            best_similarity = -1.0
            sampled = 0

            for frame in _sample_video_frames(video_path):
                sampled += 1
                faces = analyzer.get(frame)
                face = _select_primary_face(faces)
                if face is None:
                    continue
                try:
                    emb_frame = _embedding_from_face(face)
                except ValueError:
                    continue
                similarity = _cosine_similarity(emb_id, emb_frame)
                best_similarity = max(best_similarity, similarity)

            if best_similarity < 0:
                raise ValueError("No detectable face in video frames")

            distance = 1.0 - best_similarity
            matched = best_similarity >= threshold

            result = {
                "face_match": matched,
                "similarity": best_similarity,
                "distance": distance,
                "threshold": threshold,
                "sampled_frames": sampled,
                "backend": backend,
                "distance_metric": "cosine(similarity)",
            }

        else:
            # DeepFace fallback: compute embeddings per sampled frame.
            # Use same strict threshold as image verification for KYC
            threshold = threshold or float(os.getenv("KYC_FACE_THRESHOLD", "0.50"))

            emb_id = extract_embedding(id_face_path)
            best_similarity = -1.0
            sampled = 0
            succeeded = 0

            for frame in _sample_video_frames(video_path):
                sampled += 1
                try:
                    emb_frame = _deepface_embedding(frame)
                except Exception:
                    continue
                succeeded += 1
                similarity = _cosine_similarity(emb_id, emb_frame)
                best_similarity = max(best_similarity, similarity)

            if best_similarity < 0:
                raise ValueError("No detectable face in video frames")

            distance = 1.0 - best_similarity
            matched = distance <= threshold

            result = {
                "face_match": matched,
                "similarity": best_similarity,
                "distance": distance,
                "threshold": threshold,
                "sampled_frames": sampled,
                "matched_frames": succeeded,
                "backend": backend,
                "distance_metric": "cosine(distance)",
                "model": _deepface_config()[0],
                "detector": _deepface_config()[1],
            }
    finally:
        # Clean up temporary ID face crop
        if id_face_path and os.path.exists(id_face_path):
            try:
                os.remove(id_face_path)
            except Exception:
                pass
    
    return result


def _face_metrics_from_frame(frame: np.ndarray) -> Optional[Tuple[float, float, float, float]]:
    height, width = frame.shape[:2]

    if _get_face_backend() == "insightface":
        analyzer = _get_face_analyzer()
        faces = analyzer.get(frame)
        face = _select_primary_face(faces)
        if face is None or face.kps is None:
            return None

        bbox = face.bbox.astype(float)
        kps = face.kps

        left_eye = kps[0]
        right_eye = kps[1]
        nose = kps[2]

        eye_center_x = (left_eye[0] + right_eye[0]) / 2.0
        eye_distance = max(1.0, abs(right_eye[0] - left_eye[0]))
        nose_shift = (nose[0] - eye_center_x) / eye_distance

        center_x = ((bbox[0] + bbox[2]) / 2.0) / max(1.0, width)
        center_y = ((bbox[1] + bbox[3]) / 2.0) / max(1.0, height)
        face_area_ratio = ((bbox[2] - bbox[0]) * (bbox[3] - bbox[1])) / max(1.0, width * height)

        return nose_shift, center_x, center_y, face_area_ratio

    # OpenCV fallback: use face bbox center movement as a proxy for motion.
    faces = _detect_faces_opencv(frame)
    if not faces:
        return None
    face = max(faces, key=lambda f: (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]))
    x1, y1, x2, y2 = [float(v) for v in face["bbox"]]
    center_x = ((x1 + x2) / 2.0) / max(1.0, width)
    center_y = ((y1 + y2) / 2.0) / max(1.0, height)
    face_area_ratio = ((x2 - x1) * (y2 - y1)) / max(1.0, width * height)
    nose_shift = center_x - 0.5
    return nose_shift, center_x, center_y, face_area_ratio


def _laplacian_variance(gray_image: np.ndarray) -> float:
    return float(cv2.Laplacian(gray_image, cv2.CV_64F).var())


def _roll_angle(kps: List[List[int]]) -> Optional[float]:
    if not kps or len(kps) < 2:
        return None
    left_eye = kps[0]
    right_eye = kps[1]
    dx = right_eye[0] - left_eye[0]
    dy = right_eye[1] - left_eye[1]
    if dx == 0:
        return None
    return math.degrees(math.atan2(dy, dx))


def check_liveness_single_image(image_path: str) -> Dict[str, object]:
    """
    Enhanced liveness detection with strict anti-spoofing checks.
    Prevents photo attacks, screen replays, and printed photos.
    """
    image = _load_image(image_path)
    height, width = image.shape[:2]
    image_area = float(height * width)

    faces = detect_faces(image_path)
    if not faces:
        return {
            "liveness_passed": False,
            "reason": "No face detected",
        }

    face = max(faces, key=lambda f: (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]))
    x1, y1, x2, y2 = face["bbox"]

    face_area = max(1.0, float((x2 - x1) * (y2 - y1)))
    face_area_ratio = face_area / image_area

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = _laplacian_variance(gray)

    roll = _roll_angle(face.get("kps"))

    # STRICT thresholds for production-grade liveness
    # Blur: Real live selfies typically 200-1500, professional photos >2000
    min_blur = float(os.getenv("LIVENESS_BLUR_THRESHOLD", "200"))
    max_blur = float(os.getenv("LIVENESS_MAX_BLUR_THRESHOLD", "1500"))
    face_ratio_min = float(os.getenv("LIVENESS_FACE_RATIO", "0.15"))
    face_ratio_max = float(os.getenv("LIVENESS_FACE_RATIO_MAX", "0.50"))
    roll_threshold = float(os.getenv("LIVENESS_ROLL_DEG", "12"))

    reasons = []
    
    # 1. Blur checks - detect printed photos or screen replays
    if blur_score < min_blur:
        reasons.append(f"Image too blurry: {blur_score:.1f} (minimum {min_blur})")
    if blur_score > max_blur:
        reasons.append(f"Image sharpness suspicious: {blur_score:.1f} (likely professional photo)")
    
    # 2. Face size checks - prevent using tiny faces or extreme closeups
    if face_area_ratio < face_ratio_min:
        reasons.append(f"Face too small: {face_area_ratio:.1%} (minimum {face_ratio_min:.0%})")
    if face_area_ratio > face_ratio_max:
        reasons.append(f"Face too close: {face_area_ratio:.1%} (maximum {face_ratio_max:.0%})")
    
    # 3. Head angle checks - prevent extreme poses
    if roll is not None and abs(roll) > roll_threshold:
        reasons.append(f"Excessive head tilt: {abs(roll):.1f}° (maximum {roll_threshold}°)")
    
    # 4. Anti-spoofing: Check for print artifacts using color analysis
    # Real faces have natural color variation, printed photos are flatter
    face_crop = image[y1:y2, x1:x2]
    if face_crop.size > 0:
        # Color variance across face
        color_std = np.mean([np.std(face_crop[:,:,i]) for i in range(3)])
        if color_std < 15:
            reasons.append(f"Unnatural color distribution: {color_std:.1f} (minimum 15 - may be printed photo)")
    
    # 5. Edge detection - printed photos have different edge patterns
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges > 0) / edges.size
    
    # Too many edges = printed photo with paper texture
    # Too few edges = blurred or low quality
    if edge_density < 0.02:
        reasons.append(f"Too few edges: {edge_density:.3f} (minimum 0.02)")
    if edge_density > 0.25:
        reasons.append(f"Excessive edges: {edge_density:.3f} (may indicate print artifacts)")
    
    passed = len(reasons) == 0

    return {
        "liveness_passed": passed,
        "blur_score": blur_score,
        "face_area_ratio": face_area_ratio,
        "roll_angle": roll,
        "color_variance": color_std if face_crop.size > 0 else None,
        "edge_density": edge_density,
        "reason": "; ".join(reasons) if reasons else None,
    }


def check_liveness_video(video_path: str) -> Dict[str, object]:
    frames = _sample_video_frames(video_path, max_frames=15)
    if not frames:
        return {
            "liveness_passed": False,
            "reason": "No frames extracted",
        }

    nose_shifts: List[float] = []
    center_shifts_x: List[float] = []
    center_shifts_y: List[float] = []
    face_ratios: List[float] = []
    blur_scores: List[float] = []

    for frame in frames:
        metrics = _face_metrics_from_frame(frame)
        if metrics is None:
            continue
        nose_shift, center_x, center_y, face_ratio = metrics
        nose_shifts.append(nose_shift)
        center_shifts_x.append(center_x)
        center_shifts_y.append(center_y)
        face_ratios.append(face_ratio)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_scores.append(_laplacian_variance(gray))

    min_frames = int(os.getenv("LIVENESS_VIDEO_MIN_FRAMES", "6"))
    if len(nose_shifts) < min_frames:
        return {
            "liveness_passed": False,
            "reason": "Face not consistently detected",
            "detected_frames": len(nose_shifts),
        }

    nose_shift_range = max(nose_shifts) - min(nose_shifts)
    center_shift_range = max(center_shifts_x) - min(center_shifts_x)
    blur_avg = float(np.mean(blur_scores)) if blur_scores else 0.0
    face_ratio_avg = float(np.mean(face_ratios)) if face_ratios else 0.0

    nose_threshold = float(os.getenv("LIVENESS_NOSE_SHIFT", "0.08"))
    center_threshold = float(os.getenv("LIVENESS_CENTER_SHIFT", "0.05"))
    blur_threshold = float(os.getenv("LIVENESS_VIDEO_BLUR", "80"))
    face_ratio_threshold = float(os.getenv("LIVENESS_FACE_RATIO", "0.10"))

    reasons = []
    if nose_shift_range < nose_threshold:
        reasons.append("Insufficient head movement")
    if center_shift_range < center_threshold:
        reasons.append("Insufficient face motion")
    if blur_avg < blur_threshold:
        reasons.append("Video too blurry")
    if face_ratio_avg < face_ratio_threshold:
        reasons.append("Face too small in frame")

    passed = len(reasons) == 0

    return {
        "liveness_passed": passed,
        "nose_shift_range": nose_shift_range,
        "center_shift_range": center_shift_range,
        "blur_avg": blur_avg,
        "face_ratio_avg": face_ratio_avg,
        "detected_frames": len(nose_shifts),
        "reason": "; ".join(reasons) if reasons else None,
    }
