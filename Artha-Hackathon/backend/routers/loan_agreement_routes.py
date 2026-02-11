from fastapi import APIRouter, HTTPException, Depends
from auth.auth_dependency import get_current_user
from schemas.loan_agreement_schemas import SignedAgreementUploadSchema
from services.signature_service import process_signed_agreement

router = APIRouter(prefix="/loans", tags=["loan-agreement"])


@router.post("/{loan_id}/agreement/upload")
def upload_signed_agreement(
    loan_id: str,
    payload: SignedAgreementUploadSchema,
    current_user=Depends(get_current_user),
):
    """
    Upload signed loan agreement PDF.
    - Verifies borrower identity
    - Triggers thumb verification
    - Finalizes loan listing if verified
    """
    try:
        if payload.loan_id != loan_id:
            raise Exception("Loan ID mismatch")

        return process_signed_agreement(payload)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
