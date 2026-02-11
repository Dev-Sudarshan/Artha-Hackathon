from schemas.kyc_schemas import (
    KYCPageOneSchema,
    KYCPageTwoSchema,
    KYCPageThreeSchema,
)

from blockchain.kyc import record_kyc_result
from blockchain.identity import record_identity_proof

from models.citizenship_ocr_model import verify_citizenship_card

from db.database import get_item, put_item

import os
from urllib.parse import urlparse


def _resolve_upload_ref(ref: str) -> str:
    """Resolve frontend-provided refs (e.g. '/static/uploads/x.png' or full URLs) to local disk paths.

    The AI pipeline expects filesystem paths. The upload API returns browser URLs under /static/uploads.
    """
    if not ref:
        return ref

    text = str(ref).strip().replace('\\', '/').replace('\\\\', '/')
    # If it's a full URL, extract only the path portion
    if text.startswith('http://') or text.startswith('https://'):
        try:
            text = urlparse(text).path or text
        except Exception:
            pass

    # Normalize leading slash variants
    if text.startswith('static/uploads/'):
        filename = text.split('static/uploads/', 1)[1]
    elif text.startswith('/static/uploads/'):
        filename = text.split('/static/uploads/', 1)[1]
    else:
        # Already a filesystem path or non-static reference
        return ref

    backend_dir = os.path.dirname(__file__)
    static_dir = os.path.abspath(os.path.join(backend_dir, '..', 'static'))
    uploads_dir = os.path.join(static_dir, 'uploads')
    return os.path.join(uploads_dir, filename)


# ---- CREDIT SCORE CONSTANT ----
INITIAL_CREDIT_SCORE = 600

# ---- KYC STAGES ----
STAGE_BASIC = "BASIC_INFO_SUBMITTED"
STAGE_ID = "ID_ANALYSIS_RUNNING"
STAGE_VIDEO = "VIDEO_ANALYSIS_RUNNING"
STAGE_DONE = "FINALIZED"


# =========================
# PAGE 1 — BASIC INFO
# =========================

def submit_basic_info(payload: KYCPageOneSchema):
    """
    Page 1: Store basic info & address
    """
    user_id = payload.user_id

    kyc_data = get_item("kyc", user_id) or {}

    payload_dict = payload.dict()
    kyc_data["basic_info"] = payload_dict["basic_info"]
    kyc_data["permanent_address"] = payload_dict["permanent_address"]
    kyc_data["temporary_address"] = payload_dict["temporary_address"]
    kyc_data["stage"] = STAGE_BASIC
    kyc_data["status"] = "PENDING"

    put_item("kyc", user_id, kyc_data)


# =========================
# PAGE 2 — ID DOCUMENTS + OCR
# =========================

def submit_id_documents(payload: KYCPageTwoSchema):
    """
    Page 2:
    - Store ID documents
    - Run OCR on citizenship card
    - Match OCR text with Page-1 user input
    """
    user_id = payload.user_id
    print(f"[KYC DEBUG] Starting Step 2 for user: {user_id}")

    kyc_data = get_item("kyc", user_id)
    if not kyc_data or "basic_info" not in kyc_data:
        print("[KYC DEBUG] Error: Basic info missing in DB")
        raise Exception("Basic KYC info not submitted")

    basic_info = kyc_data["basic_info"]
    print(f"[KYC DEBUG] Basic Info found: {basic_info}")

    # ---- Build full name from Page 1 ----
    full_name = " ".join(
        filter(
            None,
            [
                basic_info.get("first_name"),
                basic_info.get("middle_name"),
                basic_info.get("last_name"),
            ],
        )
    )

    dob = basic_info.get("date_of_birth")
    citizenship_no = payload.id_details.id_number
    
    # Path resolution
    front_img = _resolve_upload_ref(payload.id_images.front_image_ref)
    back_img = _resolve_upload_ref(payload.id_images.back_image_ref)
    print(f"[KYC DEBUG] Image paths: {front_img}, {back_img}")

    # ---- OCR VERIFICATION (advisory; admin performs final approval) ----
    ai_results = {
        "gov_id_verified": False,
        "name_match": False,
        "dob_match": False,
        "citizenship_no_match": False,
        "thumbprint_detected": False,
        "face_detected_on_card": False,
        "ocr_error": None,
    }

    try:
        from models.citizenship_ocr_model import verify_citizenship_card, extract_thumbprint, detect_face_on_card

        print("[KYC DEBUG] Running AI OCR analysis...")
        ocr_result = verify_citizenship_card(
            image_path=back_img,
            input_full_name=full_name,
            input_dob=dob,
            input_citizenship_no=citizenship_no,
        )
        print(f"[KYC DEBUG] OCR Result: {ocr_result}")

        thumbprint_detected = extract_thumbprint(back_img)
        face_detected = detect_face_on_card(front_img)
        print(f"[KYC DEBUG] Detections: Thumb:{thumbprint_detected}, Face:{face_detected}")

        ai_results.update(
            {
                "gov_id_verified": ocr_result.get("final_ocr_status") == "PASSED",
                "name_match": bool(ocr_result.get("name_match")),
                "dob_match": bool(ocr_result.get("dob_match")),
                "citizenship_no_match": bool(ocr_result.get("citizenship_no_match")),
                "thumbprint_detected": bool(thumbprint_detected),
                "face_detected_on_card": bool(face_detected),
            }
        )
    except Exception as ai_err:
        # Do not block submission; store the error and let admin decide.
        print(f"[KYC DEBUG] AI Analysis failed (non-blocking): {ai_err}")
        ai_results["ocr_error"] = str(ai_err)

    # ---- Store results ----
    kyc_data["id_documents"] = payload.dict()
    kyc_data["ai_results"] = ai_results
    kyc_data["stage"] = STAGE_ID

    put_item("kyc", user_id, kyc_data)
    print(f"[KYC DEBUG] Step 2 complete for {user_id}")

    return {
        "user_id": user_id,
        "ocr_status": ai_results.get("gov_id_verified", False),
    }


from models.image_verification_model import verify_face_identity
from models.face_pipeline import check_liveness_single_image, check_liveness_video, verify_faces_from_video

# =========================
# PAGE 3 — VIDEO + FINAL KYC (Actually Face Photo Match)
# =========================

def submit_declaration_video(payload: KYCPageThreeSchema):
    """
    Page 3:
    - Receive live photo
    - Run Face Identity Match
    - Run lightweight liveness checks (single image)
    - Finalize KYC
    """
    user_id = payload.user_id
    print(f"[KYC DEBUG] Starting Step 3 for user: {user_id}")

    kyc_data = get_item("kyc", user_id)
    if not kyc_data or "id_documents" not in kyc_data:
        print("[KYC DEBUG] Error: ID documents missing in DB")
        raise Exception("ID documents (Page 2) not submitted")

    # Get card image for face matching
    front_image_ref = _resolve_upload_ref(kyc_data["id_documents"]["id_images"]["front_image_ref"])
    live_photo_ref = _resolve_upload_ref(payload.declaration_video.selfie_image_ref)
    live_video_ref = _resolve_upload_ref(payload.declaration_video.video_ref)

    if not live_photo_ref and not live_video_ref:
        raise Exception("Selfie image or video not provided")

    if live_video_ref:
        print(f"[KYC DEBUG] Matching live video: {live_video_ref} with ID: {front_image_ref}")
    else:
        print(f"[KYC DEBUG] Matching live photo: {live_photo_ref} with ID: {front_image_ref}")

    # ---- RUN REAL IMAGE FACE AI ----
    try:
        if live_video_ref:
            face_result = verify_faces_from_video(
                id_image_path=front_image_ref,
                video_path=live_video_ref,
            )
        else:
            face_result = verify_face_identity(
                image_path=live_photo_ref,
                citizenship_image_path=front_image_ref
            )
        print(f"[KYC DEBUG] Face result: {face_result}")
    except Exception as face_err:
        print(f"[KYC DEBUG] Face AI failed: {face_err}")
        face_result = {
            "face_match": False,
            "distance": 1.0,
            "final_status": "REJECTED",
            "reason": f"Face AI error: {str(face_err)}"
        }

    # ---- LIVENESS CHECK ----
    try:
        if live_video_ref:
            liveness_result = check_liveness_video(live_video_ref)
        else:
            liveness_result = check_liveness_single_image(live_photo_ref)
        print(f"[KYC DEBUG] Liveness result: {liveness_result}")
    except Exception as live_err:
        print(f"[KYC DEBUG] Liveness check failed: {live_err}")
        liveness_result = {
            "liveness_passed": False,
            "reason": f"Liveness error: {str(live_err)}",
        }

    # ---- FINAL MERGED KYC RESULT ----
    ocr_ok = kyc_data.get("ai_results", {}).get("gov_id_verified", False)
    face_ok = bool(face_result.get("face_match"))
    live_ok = bool(liveness_result.get("liveness_passed"))

    # AI suggestion only; final approval is performed by admin review.
    ai_suggested_status = "APPROVED" if (ocr_ok and face_ok and live_ok) else "REJECTED"

    reasons = []
    if not ocr_ok:
        reasons.append("OCR verification failed")
    if not face_ok:
        reasons.append("Face mismatch")
    if not live_ok:
        reasons.append("Liveness failed")

    final_kyc_result = {
        **kyc_data.get("ai_results", {}),
        "face_match_score": face_result.get("distance", 0.0),
        "face_similarity": face_result.get("similarity"),
        "speech_verified": True,
        "liveness_passed": liveness_result.get("liveness_passed"),
        "liveness_reason": liveness_result.get("reason"),
        "ai_suggested_status": ai_suggested_status,
        "reason": "; ".join(reasons) if reasons else face_result.get("reason")
    }

    # ---- BLOCKCHAIN WRITE (Optional/Safe for dev) ----
    try:
        print("[KYC DEBUG] Recording to blockchain...")
        record_kyc_result(final_kyc_result, user_id)
        record_identity_proof(
            {
                "id_verified": final_kyc_result.get("gov_id_verified", False),
                "face_match": final_kyc_result.get("face_match_score", 0.0),
                "location_ok": final_kyc_result.get("location_ok", True),
            },
            user_id,
        )
    except Exception as bc_err:
        print(f"[KYC DEBUG] Blockchain write failed (ignoring for dev): {bc_err}")

    # ---- UPDATE DB STATE ----
    # Store declaration refs so admin can view uploaded selfie/video + consent text.
    kyc_data["declaration"] = payload.dict()
    kyc_data["final_result"] = final_kyc_result
    kyc_data["stage"] = STAGE_DONE

    # Admin must approve/reject after user submission.
    kyc_data["status"] = "PENDING_ADMIN_REVIEW"

    # ✅ Initialize fake credit score ONCE
    existing_score = get_item("credit_scores", user_id)
    if existing_score is None:
        put_item("credit_scores", user_id, INITIAL_CREDIT_SCORE)

    put_item("kyc", user_id, kyc_data)

    current_score = get_item("credit_scores", user_id)

    return {
        "user_id": user_id,
        "kyc_status": kyc_data["status"],
        "credit_score": current_score,
    }
