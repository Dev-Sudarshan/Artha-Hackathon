from fastapi import APIRouter, HTTPException, Depends
from auth.auth_dependency import get_current_user
from services.audit_service import (
    verify_kyc,
    verify_identity,
    verify_loan_request,
    verify_loan_acceptance,
    verify_transaction,
    verify_repayments,
    verify_agreement_execution,
)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/kyc/{user_id}")
def audit_kyc(user_id: str, current_user=Depends(get_current_user)):
    try:
        return verify_kyc(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/identity/{user_id}")
def audit_identity(user_id: str, current_user=Depends(get_current_user)):
    try:
        return verify_identity(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/loan/request/{loan_id}")
def audit_loan_request(loan_id: str, current_user=Depends(get_current_user)):
    try:
        return verify_loan_request(loan_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/loan/acceptance/{loan_id}")
def audit_loan_acceptance(loan_id: str, current_user=Depends(get_current_user)):
    try:
        return verify_loan_acceptance(loan_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agreement/execution/{loan_id}")
def audit_agreement_execution(loan_id: str, current_user=Depends(get_current_user)):
    """
    Verify signed agreement execution:
    - signed PDF
    - video verification
    - thumb verification
    """
    try:
        return verify_agreement_execution(loan_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transaction/{tx_id}")
def audit_transaction(tx_id: str, current_user=Depends(get_current_user)):
    try:
        return verify_transaction(tx_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/repayments/{loan_id}")
def audit_repayments(loan_id: str, current_user=Depends(get_current_user)):
    try:
        return verify_repayments(loan_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
