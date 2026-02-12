from fastapi import APIRouter, HTTPException, Depends
from auth.auth_dependency import get_current_user
from schemas.loan_schemas import BorrowRequestSchema
from schemas.lender_schemas import LenderAcceptanceSchema
from services.loan_service import (
    create_borrow_request,
    get_marketplace_listings,
    accept_loan,
    get_user_portfolio,
)

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("/my-portfolio")
def get_my_portfolio(current_user=Depends(get_current_user)):
    """
    Get current user's active loan and investments
    """
    return get_user_portfolio(current_user)


import traceback

@router.post("/borrow")
def create_borrow_listing(
    payload: BorrowRequestSchema,
    current_user=Depends(get_current_user),
):
    try:
        # Enforce auth user as the borrower
        payload.user_id = current_user
        return create_borrow_request(payload)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/marketplace")
def marketplace_listings():
    # PUBLIC
    return get_marketplace_listings()


@router.post("/{loan_id}/accept")
def accept_loan_route(
    loan_id: str,
    payload: LenderAcceptanceSchema,
    current_user=Depends(get_current_user),
):
    try:
        payload.lender_id = current_user
        if loan_id != payload.loan_id:
            raise Exception("Loan ID mismatch")
        return accept_loan(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{loan_id}")
def delete_loan_route(
    loan_id: str,
    current_user=Depends(get_current_user),
):
    """
    Delete/Cancel a loan request by the borrower.
    Can be deleted if: DRAFT, PENDING_VERIFICATION, PENDING_ADMIN_APPROVAL, or LISTED (not yet accepted by lender)
    """
    from db.database import get_item, delete_item
    
    loan = get_item("loans", loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    # Verify ownership
    if loan.get("user_id") != current_user:
        raise HTTPException(status_code=403, detail="You can only delete your own loans")
    
    # Check if loan can be deleted
    status = loan.get("status", "").upper()
    deletable_statuses = ["DRAFT", "PENDING_VERIFICATION", "PENDING_ADMIN_APPROVAL", "LISTED"]
    
    if status not in deletable_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete loan with status '{status}'. Only drafts, pending, or listed (unfunded) loans can be deleted."
        )
    
    # Delete the loan
    delete_item("loans", loan_id)
    
    return {
        "message": "Loan deleted successfully",
        "loan_id": loan_id,
        "status": "DELETED"
    }
