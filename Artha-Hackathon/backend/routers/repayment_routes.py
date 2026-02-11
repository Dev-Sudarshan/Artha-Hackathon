from fastapi import APIRouter, HTTPException, Depends
from schemas.repayment_schemas import RepaymentSchema
from services.repayment_service import process_repayment
from auth.auth_dependency import get_current_user


router = APIRouter(prefix="/repayments", tags=["repayments"])


@router.post("/")
def repay_loan(payload: RepaymentSchema,
    current_user=Depends(get_current_user),):
    """
    Record loan repayment (partial or full)
    """
    try:
        payload.paid_by = current_user
        return process_repayment(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
