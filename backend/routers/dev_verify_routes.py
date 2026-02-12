from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import os
import shutil
import uuid

from models.citizenship_ocr_model import verify_citizenship_card
from models.face_pipeline import (
    check_liveness_single_image,
    check_liveness_video,
    verify_faces_from_video,
)
from models.image_verification_model import verify_face_identity

router = APIRouter(prefix="/dev", tags=["dev"])

UPLOAD_DIR = os.path.join("static", "uploads", "dev")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_upload(file: UploadFile) -> str:
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "bin"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


@router.post("/ocr")
async def dev_ocr_check(
    front_image: UploadFile = File(...),
    full_name: str = Form(...),
    date_of_birth: str = Form(...),
    citizenship_no: str = Form(...),
):
    try:
        front_path = _save_upload(front_image)

        verify_result = verify_citizenship_card(
            image_path=front_path,
            input_full_name=full_name,
            input_dob=date_of_birth,
            input_citizenship_no=citizenship_no,
        )

        return {
            "ocr": verify_result.get("extracted_fields", {}),
            "verification": verify_result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/face-match")
async def dev_face_match(
    id_image: UploadFile = File(...),
    selfie_image: UploadFile | None = File(None),
    selfie_video: UploadFile | None = File(None),
):
    try:
        id_path = _save_upload(id_image)

        if selfie_video is not None:
            video_path = _save_upload(selfie_video)
            face_result = verify_faces_from_video(
                id_image_path=id_path,
                video_path=video_path,
            )
            liveness_result = check_liveness_video(video_path)
        elif selfie_image is not None:
            selfie_path = _save_upload(selfie_image)
            face_result = verify_face_identity(
                id_image_path=id_path,
                selfie_image_path=selfie_path,
            )
            liveness_result = check_liveness_single_image(selfie_path)
        else:
            raise Exception("Provide selfie_image or selfie_video")

        return {
            "face": face_result,
            "liveness": liveness_result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/kyc-validation")
async def dev_kyc_validation(
    front_image: UploadFile = File(...),
    back_image: UploadFile = File(...),
    full_name: str = Form(...),
    date_of_birth: str = Form(...),
    citizenship_no: str = Form(...),
):
    """Test endpoint to validate KYC data by running the pipeline on citizenship images."""
    try:
        print(f"[KYC-Validation] Received request for: {full_name}")
        front_path = _save_upload(front_image)
        back_path = _save_upload(back_image)
        print(f"[KYC-Validation] Images saved: front={front_path}, back={back_path}")

        # Use the same working logic as /dev/ocr endpoint
        print("[KYC-Validation] Running OCR verification...")
        verify_result = verify_citizenship_card(
            image_path=back_path,
            input_full_name=full_name,
            input_dob=date_of_birth,
            input_citizenship_no=citizenship_no,
        )
        print(f"[KYC-Validation] OCR completed. Status: {verify_result.get('final_ocr_status')}")

        if verify_result.get("error"):
            return {
                "success": False,
                "match": False,
                "error": verify_result["error"],
                "message": "OCR extraction failed"
            }

        # Extract results
        extracted_fields = verify_result.get("extracted_fields", {})
        all_match = verify_result.get("final_ocr_status") == "PASSED"

        return {
            "success": True,
            "match": all_match,
            "extracted_data": {
                "full_name": extracted_fields.get("full_name", ""),
                "date_of_birth": extracted_fields.get("date_of_birth", ""),
                "citizenship_no": extracted_fields.get("citizenship_certificate_number", ""),
            },
            "provided_data": {
                "full_name": full_name,
                "date_of_birth": date_of_birth,
                "citizenship_no": citizenship_no,
            },
            "field_matches": {
                "name_match": verify_result.get("name_match", False),
                "dob_match": verify_result.get("dob_match", False),
                "citizenship_match": verify_result.get("citizenship_no_match", False),
            },
            "field_confidences": verify_result.get("confidence", {}),
            "validation_issues": verify_result.get("validation_issues", []),
            "flags_for_review": [],
            "raw_text": verify_result.get("raw_text", ""),
        }
    except Exception as e:
        print(f"[KYC-Validation] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
