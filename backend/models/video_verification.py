"""
VIDEO VERIFICATION MODEL (FINAL — OPTIMIZED)
----------------------------------------------
Verifies:
- Person face in video matches their live photo

NO LIVENESS (hackathon scope)

Pipeline:
- Video → frames (3 key frames instead of 5)
- Face match (ArcFace via DeepFace — reference embedding cached)

Optimizations applied:
- Pre-warm models at import time so first call is fast
- Compute reference-photo embedding ONCE, reuse for all frames
- Reduced to 3 frames (start, middle, end) — sufficient for match
- Use 'ssd' detector (fast DNN) instead of 'retinaface' (heavy)
- Early exit on first match
"""

import cv2
import os
import time as _time
import tempfile
import numpy as np
from typing import List, Optional

# ── Model pre-warming ──────────────────────────────────────────────
# Load ArcFace + SSD detector once at module level so subsequent
# calls don't pay the cold-start cost.

_DETECTOR = "ssd"          # much faster than retinaface, still DNN-based
_MODEL    = "ArcFace"
_MODELS_READY = False

def _warm_models():
    """Pre-load DeepFace models so the first verify() is fast."""
    global _MODELS_READY
    if _MODELS_READY:
        return
    try:
        from deepface import DeepFace
        print("[MODEL WARMUP] Loading ArcFace + SSD detector …")
        t0 = _time.time()
        # build_model caches internally; calling it once is enough
        DeepFace.build_model(_MODEL)
        print(f"[MODEL WARMUP] Done in {_time.time()-t0:.1f}s")
        _MODELS_READY = True
    except Exception as e:
        print(f"[MODEL WARMUP] Warning: {e}")

# Kick off warm-up at import time (runs in the server startup thread)
try:
    _warm_models()
except Exception:
    pass


# =========================
# VIDEO → FRAME EXTRACTION
# =========================

def extract_frames(video_path: str) -> List[str]:
    """
    Extract 3 key frames: start, middle, end of video.
    Fewer frames = faster verification with negligible accuracy loss.
    """
    t0 = _time.time()
    print(f"\n[DEBUG] Extracting frames from: {video_path}")
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        raise Exception("Invalid or empty video")

    # 3 frames is enough for face matching
    indices = [
        0,
        total_frames // 2,
        total_frames - 1,
    ]
    indices = sorted(list(set([min(i, total_frames - 1) for i in indices])))

    frame_paths = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success:
            continue

        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        cv2.imwrite(tmp.name, frame)
        frame_paths.append(tmp.name)

    cap.release()
    elapsed = _time.time() - t0
    print(f"[TIMING] Frame extraction: {elapsed:.2f}s  ({len(frame_paths)} frames)")
    return frame_paths


# =========================
# FACE MATCH (ARC FACE) — OPTIMIZED
# =========================

def _get_reference_embedding(photo_path: str):
    """Compute the reference photo embedding ONCE and cache it."""
    from deepface import DeepFace
    t0 = _time.time()
    embeddings = DeepFace.represent(
        img_path=photo_path,
        model_name=_MODEL,
        detector_backend=_DETECTOR,
        enforce_detection=True,
        align=True,
    )
    elapsed = _time.time() - t0
    print(f"[TIMING] Reference embedding: {elapsed:.2f}s")
    if not embeddings:
        raise ValueError("No face detected in reference photo")
    return np.array(embeddings[0]["embedding"])


def face_match(video_frame_path: str, photo_path: str,
               ref_embedding: Optional[np.ndarray] = None) -> tuple:
    """
    Compare face from video frame with live photo.
    If *ref_embedding* is supplied the reference photo is NOT re-processed,
    saving ~50 % per frame.
    Returns: (match_success, distance_score)
    """
    from deepface import DeepFace
    t0 = _time.time()
    try:
        if ref_embedding is not None:
            # Compute only the frame embedding; compare manually
            frame_embs = DeepFace.represent(
                img_path=video_frame_path,
                model_name=_MODEL,
                detector_backend=_DETECTOR,
                enforce_detection=True,
                align=True,
            )
            if not frame_embs:
                raise ValueError("No face in frame")
            frame_vec = np.array(frame_embs[0]["embedding"])
            # Cosine distance (same metric DeepFace uses for ArcFace)
            distance = float(1 - np.dot(ref_embedding, frame_vec) /
                             (np.linalg.norm(ref_embedding) * np.linalg.norm(frame_vec)))
            threshold = 0.6816  # ArcFace default cosine threshold
            verified = distance <= threshold
        else:
            # Fallback: full DeepFace.verify (computes both embeddings)
            result = DeepFace.verify(
                img1_path=video_frame_path,
                img2_path=photo_path,
                model_name=_MODEL,
                detector_backend=_DETECTOR,
                enforce_detection=True,
                align=True,
            )
            verified = result["verified"]
            distance = result["distance"]
            threshold = result["threshold"]

        elapsed = _time.time() - t0
        print(f"[TIMING] Face match frame: {elapsed:.2f}s  verified={verified}")
        print(f"  Frame: {os.path.basename(video_frame_path)}")
        print(f"  Distance: {distance:.4f} (Threshold: {threshold:.4f})")

        return verified, distance

    except ValueError as e:
        elapsed = _time.time() - t0
        print(f"[TIMING] Face detection failed ({elapsed:.2f}s): {e}")
        return False, None
    except Exception as e:
        elapsed = _time.time() - t0
        print(f"[TIMING] Face match error ({elapsed:.2f}s): {e}")
        return False, None


# =========================
# MAIN VERIFICATION FUNCTION
# =========================

def verify_video_identity(
    video_path: str,
    reference_photo_path: str,
    save_frame_to: str = None
) -> dict:
    """
    Video identity verification - Face matching only
    Compares video frames against a live reference photo

    Args:
        video_path: Path to video file
        reference_photo_path: Path to reference photo (KYC selfie)
        save_frame_to: Optional path to save the extracted frame for display
    """
    t_total = _time.time()
    print("=" * 40)
    print("STARTING VIDEO VERIFICATION (OPTIMIZED)")
    print("=" * 40)

    # Ensure models are loaded
    _warm_models()

    # ── 1. Extract frames from video ──
    frames = extract_frames(video_path)

    # ── 2. Compute reference embedding ONCE ──
    print(f"\n[DEBUG] Computing reference embedding: {reference_photo_path}")
    try:
        ref_embedding = _get_reference_embedding(reference_photo_path)
    except Exception as e:
        print(f"[ERROR] Cannot get reference embedding: {e}")
        ref_embedding = None  # will fall back to full verify per frame

    # ── 3. Match each frame (early exit) ──
    face_verified = False
    best_face_distance = None
    matched_frame = None
    matched_frame_path = None

    for frame in frames:
        match_result, distance = face_match(
            frame, reference_photo_path, ref_embedding=ref_embedding
        )

        if distance is not None:
            if best_face_distance is None or distance < best_face_distance:
                best_face_distance = distance

        if match_result:
            face_verified = True
            matched_frame = os.path.basename(frame)
            matched_frame_path = frame
            print(f"[DEBUG] Face verified on frame {matched_frame}!")
            break

    # ── 4. Save extracted frame ──
    saved_frame_ref = None
    if save_frame_to:
        frame_to_save = matched_frame_path if matched_frame_path else (frames[0] if frames else None)
        if frame_to_save:
            try:
                import shutil
                os.makedirs(os.path.dirname(save_frame_to), exist_ok=True)
                shutil.copy2(frame_to_save, save_frame_to)
                if 'static' in save_frame_to:
                    saved_frame_ref = '/static' + save_frame_to.split('static', 1)[1].replace('\\', '/')
                print(f"[DEBUG] Saved frame to: {save_frame_to}")
            except Exception as e:
                print(f"[DEBUG] Failed to save frame: {e}")

    # ── Cleanup temp frames ──
    for f in frames:
        try:
            os.unlink(f)
        except OSError:
            pass

    elapsed_total = _time.time() - t_total
    status_label = "PASSED" if face_verified else "FAILED"
    print(f"\n[RESULT] Face verification {status_label}")
    print(f"[TIMING] *** Total video verification: {elapsed_total:.2f}s ***")

    final_status = "APPROVED" if face_verified else "REJECTED"
    reason = None if face_verified else "Face does not match reference photo"

    return {
        "face_match": face_verified,
        "face_distance": best_face_distance,
        "matched_frame": matched_frame,
        "saved_frame_ref": saved_frame_ref,
        "final_status": final_status,
        "reason": reason,
        "verification_time_seconds": round(elapsed_total, 2),
    }


# =========================
# LOCAL TESTING
# =========================

if __name__ == "__main__":
    result = verify_video_identity(
        video_path="bacha.mp4",
        reference_photo_path="photo.jpeg",
    )

    print("\n" + "="*40)
    print("VIDEO VERIFICATION RESULT:")
    print("="*40)
    for key, value in result.items():
        print(f"{key}: {value}")