"""
VIDEO VERIFICATION MODEL (FINAL)
--------------------------------
Verifies:
- Person face in video matches their live photo

NO LIVENESS (hackathon scope)

Pipeline:
- Video → frames
- Face match (ArcFace via DeepFace with RetinaFace detector)
"""

import cv2
import os
import tempfile
from typing import List

# No additional setup needed for face verification only


# =========================
# VIDEO → FRAME EXTRACTION
# =========================

def extract_frames(video_path: str) -> List[str]:
    """
    Extract frames at start, 25%, 50%, 75%, end of video
    """
    print(f"\n[DEBUG] Extracting frames from: {video_path}")
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        raise Exception("Invalid or empty video")

    # Extract 5 frames for better chance of clear face
    indices = [
        0,
        total_frames // 4,
        total_frames // 2,
        (total_frames * 3) // 4,
        total_frames - 1
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
    print(f"[DEBUG] Extracted {len(frame_paths)} frames: {frame_paths}")
    return frame_paths


# =========================
# FACE MATCH (ARC FACE)
# =========================

def face_match(video_frame_path: str, photo_path: str) -> tuple[bool, float]:
    """
    Compare face from video frame with live photo
    Returns: (match_success, distance_score)
    """
    from deepface import DeepFace
    try:
        result = DeepFace.verify(
            img1_path=video_frame_path,
            img2_path=photo_path,
            model_name="ArcFace",
            detector_backend="retinaface",  # More robust than opencv
            enforce_detection=True,
            align=True
        )
        
        verified = result["verified"]
        distance = result["distance"]
        threshold = result["threshold"]
        
        print(f"[DEBUG] Face Match: {verified}")
        print(f"  Frame: {os.path.basename(video_frame_path)}")
        print(f"  Distance: {distance:.4f} (Threshold: {threshold:.4f})")
        
        return verified, distance

    except ValueError as e:
        print(f"[DEBUG] Face detection failed for {os.path.basename(video_frame_path)}: {e}")
        return False, None
    except Exception as e:
        print(f"[DEBUG] Face Match Error for {os.path.basename(video_frame_path)}: {e}")
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
    print("="*40)
    print("STARTING VIDEO VERIFICATION (FACE ONLY)")
    print("="*40)

    # Extract frames from video
    frames = extract_frames(video_path)
    
    print(f"\n[DEBUG] Verifying face against reference photo: {reference_photo_path}")
    face_verified = False
    best_face_distance = None
    matched_frame = None
    matched_frame_path = None
    
    for frame in frames:
        match_result, distance = face_match(frame, reference_photo_path)
        
        # Track best distance even if not verified
        if distance is not None:
            if best_face_distance is None or distance < best_face_distance:
                best_face_distance = distance
        
        if match_result:
            face_verified = True
            matched_frame = os.path.basename(frame)
            matched_frame_path = frame
            print(f"[DEBUG] Face verified on frame {matched_frame}!")
            break
    
    # Save frame if requested (use first frame if no match found)
    saved_frame_ref = None
    if save_frame_to:
        frame_to_save = matched_frame_path if matched_frame_path else (frames[0] if frames else None)
        if frame_to_save:
            try:
                import shutil
                os.makedirs(os.path.dirname(save_frame_to), exist_ok=True)
                shutil.copy2(frame_to_save, save_frame_to)
                # Return relative path from static directory
                if 'static' in save_frame_to:
                    saved_frame_ref = '/static' + save_frame_to.split('static', 1)[1].replace('\\', '/')
                print(f"[DEBUG] Saved frame to: {save_frame_to}")
            except Exception as e:
                print(f"[DEBUG] Failed to save frame: {e}")
    
    if not face_verified:
        print("\n[RESULT] Face verification FAILED")
    else:
        print("\n[RESULT] Face verification PASSED")

    final_status = "APPROVED" if face_verified else "REJECTED"
    reason = None if face_verified else "Face does not match reference photo"

    return {
        "face_match": face_verified,
        "face_distance": best_face_distance,
        "matched_frame": matched_frame,
        "saved_frame_ref": saved_frame_ref,
        "final_status": final_status,
        "reason": reason,
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