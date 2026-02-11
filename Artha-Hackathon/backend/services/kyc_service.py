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
    - Store ID documents only
    - NO verification yet (verification happens in Page 3 after all data is collected)
    """
    user_id = payload.user_id
    print(f"[KYC DEBUG] Starting Step 2 for user: {user_id}")

    kyc_data = get_item("kyc", user_id)
    if not kyc_data or "basic_info" not in kyc_data:
        print("[KYC DEBUG] Error: Basic info missing in DB")
        raise Exception("Basic KYC info not submitted")

    # ---- Store ID documents without running verification ----
    front_img = _resolve_upload_ref(payload.id_images.front_image_ref)
    back_img = _resolve_upload_ref(payload.id_images.back_image_ref)
    print(f"[KYC DEBUG] Image paths stored: {front_img}, {back_img}")

    kyc_data["id_documents"] = payload.dict()
    kyc_data["stage"] = STAGE_ID

    put_item("kyc", user_id, kyc_data)
    print(f"[KYC DEBUG] Step 2 complete for {user_id} - documents stored, verification deferred to final step")

    return {
        "user_id": user_id,
        "message": "ID documents saved. Complete final step to verify.",
    }


from models.image_verification_model import verify_face_identity
from models.face_pipeline import check_liveness_single_image, check_liveness_video, verify_faces_from_video
import threading

# =========================
# PAGE 3 — VIDEO + FINAL KYC (Actually Face Photo Match)
# =========================

def submit_declaration_video(payload: KYCPageThreeSchema):
    """
    Page 3 (FINAL STEP):
    - Save declaration data immediately and return fast
    - AI verification (OCR, face match, liveness) runs in background thread
    """
    user_id = payload.user_id
    print(f"[KYC DEBUG] Starting Step 3 for user: {user_id}")

    kyc_data = get_item("kyc", user_id)
    if not kyc_data or "id_documents" not in kyc_data:
        print("[KYC DEBUG] Error: ID documents missing in DB")
        raise Exception("ID documents (Page 2) not submitted")

    if not kyc_data.get("basic_info"):
        raise Exception("Basic info (Page 1) not submitted")

    live_photo_ref = _resolve_upload_ref(payload.declaration_video.selfie_image_ref)
    live_video_ref = _resolve_upload_ref(payload.declaration_video.video_ref)

    if not live_photo_ref and not live_video_ref:
        raise Exception("Selfie image or video not provided")

    # ---- SAVE DECLARATION DATA IMMEDIATELY ----
    kyc_data["declaration"] = payload.dict()
    kyc_data["stage"] = STAGE_VIDEO
    kyc_data["status"] = "PROCESSING"
    put_item("kyc", user_id, kyc_data)

    # ---- Initialize credit score ONCE ----
    existing_score = get_item("credit_scores", user_id)
    if existing_score is None:
        put_item("credit_scores", user_id, INITIAL_CREDIT_SCORE)

    # ---- LAUNCH BACKGROUND VERIFICATION ----
    thread = threading.Thread(
        target=_run_verification_background,
        args=(user_id,),
        daemon=True,
    )
    thread.start()
    print(f"[KYC DEBUG] Background verification launched for {user_id}")

    return {
        "user_id": user_id,
        "kyc_status": "PROCESSING",
        "message": "KYC submitted successfully. Verification is running in the background.",
    }


def _run_verification_background(user_id: str):
    """
    Runs ALL AI verification in a background thread so the HTTP response is instant.
    """
    try:
        print(f"[KYC BG] Starting background verification for {user_id}")
        kyc_data = get_item("kyc", user_id)
        if not kyc_data:
            print(f"[KYC BG] ERROR: No KYC data found for {user_id}")
            return

        basic_info = kyc_data["basic_info"]
        front_image_ref = _resolve_upload_ref(kyc_data["id_documents"]["id_images"]["front_image_ref"])
        back_image_ref = _resolve_upload_ref(kyc_data["id_documents"]["id_images"]["back_image_ref"])
        live_photo_ref = _resolve_upload_ref(kyc_data["declaration"]["declaration_video"]["selfie_image_ref"])
        live_video_ref = _resolve_upload_ref(kyc_data["declaration"]["declaration_video"].get("video_ref"))

        # ============================================================
        # STEP 1: OCR VERIFICATION (citizenship card)
        # ============================================================
        print("[KYC BG] === STEP 1: Running OCR verification ===")

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
        citizenship_no = kyc_data["id_documents"]["id_details"]["id_number"]

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

            ocr_result = verify_citizenship_card(
                image_path=back_image_ref,
                input_full_name=full_name,
                input_dob=dob,
                input_citizenship_no=citizenship_no,
            )
            print(f"[KYC BG] OCR Result: {ocr_result}")

            thumbprint_detected = extract_thumbprint(back_image_ref)
            face_detected = detect_face_on_card(front_image_ref)
            print(f"[KYC BG] Detections: Thumb:{thumbprint_detected}, Face:{face_detected}")

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
            print(f"[KYC BG] OCR verification failed (non-blocking): {ai_err}")
            ai_results["ocr_error"] = str(ai_err)

        # ============================================================
        # STEP 2: FACE MATCHING (selfie vs ID card)
        # ============================================================
        print("[KYC BG] === STEP 2: Running face matching ===")

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
            print(f"[KYC BG] Face result: {face_result}")
        except Exception as face_err:
            print(f"[KYC BG] Face AI failed: {face_err}")
            face_result = {
                "face_match": False,
                "distance": 1.0,
                "final_status": "REJECTED",
                "reason": f"Face AI error: {str(face_err)}"
            }

        # ============================================================
        # STEP 3: LIVENESS CHECK
        # ============================================================
        print("[KYC BG] === STEP 3: Running liveness detection ===")

        try:
            if live_video_ref:
                liveness_result = check_liveness_video(live_video_ref)
            else:
                liveness_result = check_liveness_single_image(live_photo_ref)
            print(f"[KYC BG] Liveness result: {liveness_result}")
        except Exception as live_err:
            print(f"[KYC BG] Liveness check failed: {live_err}")
            liveness_result = {
                "liveness_passed": False,
                "reason": f"Liveness error: {str(live_err)}",
            }

        # ============================================================
        # FINAL: MERGE ALL RESULTS
        # ============================================================
        print("[KYC BG] === Merging all verification results ===")
        ocr_ok = ai_results.get("gov_id_verified", False)
        face_ok = bool(face_result.get("face_match"))
        live_ok = bool(liveness_result.get("liveness_passed"))

        ai_suggested_status = "APPROVED" if (ocr_ok and face_ok and live_ok) else "REJECTED"

        reasons = []
        if not ocr_ok:
            reasons.append("OCR verification failed")
        if not face_ok:
            reasons.append("Face mismatch")
        if not live_ok:
            reasons.append("Liveness failed")

        final_kyc_result = {
            **ai_results,
            "face_match_score": face_result.get("distance", 0.0),
            "face_similarity": face_result.get("similarity"),
            "speech_verified": True,
            "liveness_passed": liveness_result.get("liveness_passed"),
            "liveness_reason": liveness_result.get("reason"),
            "ai_suggested_status": ai_suggested_status,
            "reason": "; ".join(reasons) if reasons else face_result.get("reason")
        }

        print(f"[KYC BG] Final result: OCR={ocr_ok}, Face={face_ok}, Liveness={live_ok}")
        print(f"[KYC BG] AI suggested status: {ai_suggested_status}")

        # ---- BLOCKCHAIN WRITE ----
        try:
            print("[KYC BG] Recording to blockchain...")
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
            print(f"[KYC BG] Blockchain write failed (ignoring for dev): {bc_err}")

        # ---- UPDATE DB STATE ----
        kyc_data = get_item("kyc", user_id)  # Re-read in case of concurrent changes
        kyc_data["final_result"] = final_kyc_result
        kyc_data["stage"] = STAGE_DONE
        kyc_data["status"] = "PENDING_ADMIN_REVIEW"
        put_item("kyc", user_id, kyc_data)

        print(f"[KYC BG] Background verification COMPLETE for {user_id}")

    except Exception as e:
        print(f"[KYC BG] CRITICAL ERROR in background verification for {user_id}: {e}")
        import traceback
        traceback.print_exc()
        # Mark as failed so user can retry
        try:
            kyc_data = get_item("kyc", user_id)
            if kyc_data:
                kyc_data["status"] = "PENDING_ADMIN_REVIEW"
                kyc_data["stage"] = STAGE_DONE
                kyc_data["final_result"] = {"error": str(e), "ai_suggested_status": "NEEDS_REVIEW"}
                put_item("kyc", user_id, kyc_data)
        except Exception:
            pass
