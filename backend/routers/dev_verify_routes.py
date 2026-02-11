from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import os
import shutil
import uuid

from models.citizenship_ocr_model import extract_ocr_fields, verify_citizenship_card
from models.face_pipeline import (
    check_liveness_single_image,
    check_liveness_video,
    verify_faces,
    verify_faces_from_video,
)

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

        ocr_fields = extract_ocr_fields(front_path)
        verify_result = verify_citizenship_card(
            image_path=front_path,
            input_full_name=full_name,
            input_dob=date_of_birth,
            input_citizenship_no=citizenship_no,
        )

        return {
            "ocr": ocr_fields,
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
            face_result = verify_faces(
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
