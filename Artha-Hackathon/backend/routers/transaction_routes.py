from fastapi import APIRouter, HTTPException, Depends
from auth.auth_dependency import get_current_user
from schemas.transaction_schemas import TransactionReceiptSchema
from services.transaction_service import process_fund_transfer

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/fund-transfer")
def fund_transfer(
    payload: TransactionReceiptSchema,
    current_user=Depends(get_current_user),
):
    try:
        return process_fund_transfer(payload, lender_id=current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
