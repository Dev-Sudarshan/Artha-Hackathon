from fastapi import APIRouter, HTTPException, Depends
from auth.auth_dependency import get_current_user
from services.kyc_service import (
    submit_basic_info,
    submit_id_documents,
    submit_declaration_video,
)
from schemas.kyc_schemas import (
    KYCPageOneSchema,
    KYCPageTwoSchema,
    KYCPageThreeSchema,
)

router = APIRouter(prefix="/kyc", tags=["kyc"])


@router.post("/basic-info")
def kyc_basic_info(
    payload: KYCPageOneSchema,
    current_user=Depends(get_current_user),
):
    try:
        payload.user_id = current_user
        print(f"[KYC] Received Basic Info for: {current_user}")
        print(f"[KYC] Payload: {payload.dict()}")
        submit_basic_info(payload)
        return {"message": "Basic KYC info saved"}
    except Exception as e:
        print(f"[KYC] Error in Step 1: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/id-documents")
def kyc_id_documents(
    payload: KYCPageTwoSchema,
    current_user=Depends(get_current_user),
):
    try:
        payload.user_id = current_user
        submit_id_documents(payload)
        return {"message": "ID documents saved. Complete final step to verify."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/declaration-video")
def kyc_declaration_video(
    payload: KYCPageThreeSchema,
    current_user=Depends(get_current_user),
):
    try:
        payload.user_id = current_user
        submit_declaration_video(payload)
        return {"message": "KYC complete. Running verification checks (OCR, face match, liveness)..."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
