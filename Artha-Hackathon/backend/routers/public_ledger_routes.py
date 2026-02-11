from fastapi import APIRouter, HTTPException

from services.public_ledger_service import (
    get_public_transactions,
    get_public_loans,
    get_public_repayments,
    get_public_kyc,
    get_public_identity_proofs,
)

router = APIRouter(prefix="/public/ledger", tags=["public-ledger"])


@router.get("/transactions")
def public_transactions():
    """
    Public read-only view of transaction hashes
    """
    try:
        return get_public_transactions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/loans")
def public_loans():
    """
    Public read-only view of loan request & agreement hashes
    """
    try:
        return get_public_loans()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repayments")
def public_repayments():
    """
    Public read-only view of repayment hashes
    """
    try:
        return get_public_repayments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kyc")
def public_kyc():
    """
    Public read-only view of KYC verification hashes
    """
    try:
        return get_public_kyc()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/identity")
def public_identity():
    """
    Public read-only view of identity proof hashes
    """
    try:
        return get_public_identity_proofs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
