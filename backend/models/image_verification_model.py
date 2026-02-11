"""Image Verification Model — Face identity matching.

Exposes:
    verify_face_identity(image_path, citizenship_image_path)

Called by kyc_service.py during Step 3 to compare the live selfie photo
against the face on the citizenship card front image.
"""

from __future__ import annotations

import os
import traceback
from typing import Optional


def verify_face_identity(
    image_path: str,
    citizenship_image_path: str,
) -> dict:
    """Compare the live selfie against the face on the citizenship card.

    Args:
        image_path: Path to the live selfie photo.
        citizenship_image_path: Path to the citizenship card front image.

    Returns:
        dict with:
            face_match: bool
            distance: float  (lower = more similar)
            similarity: float (higher = more similar, 0-1)
            final_status: "APPROVED" | "REJECTED"
            reason: str | None
    """
    result = {
        "face_match": False,
        "distance": 1.0,
        "similarity": 0.0,
        "final_status": "REJECTED",
        "reason": None,
    }

    if not os.path.isfile(image_path):
        result["reason"] = f"Live photo not found: {image_path}"
        return result

    if not os.path.isfile(citizenship_image_path):
        result["reason"] = f"Citizenship card image not found: {citizenship_image_path}"
        return result

    try:
        from deepface import DeepFace

        verification = DeepFace.verify(
            img1_path=image_path,
            img2_path=citizenship_image_path,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=False,  # Don't crash if face not found on card
            align=True,
        )

        verified = verification.get("verified", False)
        distance = verification.get("distance", 1.0)
        threshold = verification.get("threshold", 0.68)

        # Compute a similarity score (1.0 = identical, 0.0 = completely different)
        similarity = max(0.0, 1.0 - (distance / max(threshold * 2, 0.01)))

        result["face_match"] = verified
        result["distance"] = round(distance, 4)
        result["similarity"] = round(similarity, 4)
        result["final_status"] = "APPROVED" if verified else "REJECTED"
        if not verified:
            result["reason"] = f"Face distance {distance:.4f} exceeds threshold {threshold:.4f}"

        print(f"[FACE_VERIFY] Match: {verified}, Distance: {distance:.4f}, Threshold: {threshold:.4f}")

    except ValueError as ve:
        result["reason"] = f"Face not detected: {str(ve)}"
        print(f"[FACE_VERIFY] Detection failed: {ve}")

    except ImportError:
        result["reason"] = "deepface library not installed"
        print("[FACE_VERIFY] deepface not available — install with: pip install deepface")

    except Exception as e:
        result["reason"] = f"Face verification error: {str(e)}"
        traceback.print_exc()

    return result
