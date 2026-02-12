"""
Background Loan Video Verification Service

Runs video face verification asynchronously like KYC verification.
Updates loan record with AI suggestion but leaves final decision to admin.
"""

import os
import time as _time
import threading
from typing import Optional
from urllib.parse import urlparse

from db.database import get_item, put_item
from models.video_verification import verify_video_identity


def _resolve_upload_ref(ref: str) -> str:
    """Resolve frontend-provided refs to local disk paths."""
    if not ref:
        return ref

    text = str(ref).strip().replace('\\', '/').replace('\\\\', '/')
    if text.startswith('http://') or text.startswith('https://'):
        try:
            text = urlparse(text).path or text
        except Exception:
            pass

    if text.startswith('static/uploads/'):
        filename = text.split('static/uploads/', 1)[1]
    elif text.startswith('/static/uploads/'):
        filename = text.split('/static/uploads/', 1)[1]
    else:
        return ref

    backend_dir = os.path.dirname(__file__)
    static_dir = os.path.abspath(os.path.join(backend_dir, '..', 'static'))
    uploads_dir = os.path.join(static_dir, 'uploads')
    return os.path.join(uploads_dir, filename)


def verify_loan_video_background(loan_id: str):
    """
    Background task: Verify loan video against KYC selfie
    Updates loan record with verification result and AI suggestion
    """
    print(f"\n[BG VERIFICATION] Starting video verification for loan {loan_id}")
    _t0 = _time.time()
    
    try:
        # Get loan data
        loan = get_item("loans", loan_id)
        if not loan:
            print(f"[BG VERIFICATION] Loan {loan_id} not found")
            return
        
        video_ref = loan.get("video_verification_ref")
        selfie_ref = loan.get("kyc_selfie_ref")
        
        if not video_ref:
            print(f"[BG VERIFICATION] No video reference for loan {loan_id}")
            loan["ai_suggestion"] = "MANUAL_REVIEW"
            loan["ai_suggestion_reason"] = "No video uploaded"
            put_item("loans", loan_id, loan)
            return
        
        if not selfie_ref:
            print(f"[BG VERIFICATION] No KYC selfie reference for loan {loan_id}")
            loan["ai_suggestion"] = "MANUAL_REVIEW"
            loan["ai_suggestion_reason"] = "No KYC selfie found"
            put_item("loans", loan_id, loan)
            return
        
        # Resolve file paths
        video_path = _resolve_upload_ref(video_ref)
        selfie_path = _resolve_upload_ref(selfie_ref)
        
        print(f"[BG VERIFICATION] Video: {video_path}")
        print(f"[BG VERIFICATION] Selfie: {selfie_path}")
        
        # Check files exist
        if not os.path.exists(video_path):
            print(f"[BG VERIFICATION] Video file not found: {video_path}")
            loan["ai_suggestion"] = "MANUAL_REVIEW"
            loan["ai_suggestion_reason"] = "Video file not found"
            put_item("loans", loan_id, loan)
            return
        
        if not os.path.exists(selfie_path):
            print(f"[BG VERIFICATION] Selfie file not found: {selfie_path}")
            loan["ai_suggestion"] = "MANUAL_REVIEW"
            loan["ai_suggestion_reason"] = "Selfie file not found"
            put_item("loans", loan_id, loan)
            return
        
        # Prepare path to save extracted video frame
        backend_dir = os.path.dirname(__file__)
        static_dir = os.path.abspath(os.path.join(backend_dir, '..', 'static'))
        uploads_dir = os.path.join(static_dir, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Create unique filename for extracted frame
        frame_filename = f"video_frame_{loan_id}_{int(_time.time())}.jpg"
        frame_save_path = os.path.join(uploads_dir, frame_filename)
        
        # Run video verification
        _t_verify = _time.time()
        verification_result = verify_video_identity(
            video_path=video_path,
            reference_photo_path=selfie_path,
            save_frame_to=frame_save_path
        )
        print(f"[TIMING] verify_video_identity: {_time.time()-_t_verify:.2f}s")
        
        print(f"[BG VERIFICATION] Result: {verification_result}")
        
        # Store the extracted frame reference
        if verification_result.get("saved_frame_ref"):
            loan["video_frame_ref"] = verification_result["saved_frame_ref"]
            print(f"[BG VERIFICATION] Saved video frame: {verification_result['saved_frame_ref']}")
        
        # Determine AI suggestion based on face match
        if verification_result.get("face_match"):
            ai_suggestion = "APPROVE"
            ai_reason = "Face matched successfully"
        else:
            ai_suggestion = "REJECT"
            ai_reason = verification_result.get("reason", "Face does not match reference photo")
        
        # Update loan with verification result and AI suggestion
        loan["video_verification_result"] = verification_result
        loan["ai_suggestion"] = ai_suggestion
        loan["ai_suggestion_reason"] = ai_reason
        loan["status"] = "PENDING_ADMIN_APPROVAL"  # Now ready for admin review
        
        put_item("loans", loan_id, loan)
        
        print(f"[BG VERIFICATION] ✓ Completed for loan {loan_id}")
        print(f"[BG VERIFICATION] AI Suggestion: {ai_suggestion} - {ai_reason}")
        print(f"[TIMING] *** Total loan BG verification: {_time.time()-_t0:.2f}s ***")
        
    except Exception as e:
        print(f"[BG VERIFICATION] ERROR for loan {loan_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Update loan with error status
        try:
            loan = get_item("loans", loan_id)
            if loan:
                loan["video_verification_result"] = {
                    "error": str(e),
                    "final_status": "ERROR"
                }
                loan["ai_suggestion"] = "MANUAL_REVIEW"
                loan["ai_suggestion_reason"] = f"Verification error: {str(e)}"
                loan["status"] = "PENDING_ADMIN_APPROVAL"
                put_item("loans", loan_id, loan)
        except Exception as update_err:
            print(f"[BG VERIFICATION] Failed to update error status: {update_err}")


def trigger_background_verification(loan_id: str):
    """
    Trigger background video verification in a separate thread
    """
    thread = threading.Thread(
        target=verify_loan_video_background,
        args=(loan_id,),
        daemon=True
    )
    thread.start()
    print(f"[TRIGGER] Background verification thread started for loan {loan_id}")
