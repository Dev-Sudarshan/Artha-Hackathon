import os

from schemas.loan_schemas import BorrowRequestSchema
from schemas.loan_marketplace_schemas import MarketplaceLoanSchema
from schemas.lender_schemas import LenderAcceptanceSchema

from blockchain.loans import record_loan_acceptance
from blockchain.loan_status import record_loan_status

from utils.emi_calculator import calculate_emi
from services.pdf_service import generate_loan_agreement_pdf
from models.video_verification import verify_video_identity

from db.database import get_item, put_item, get_all_items
import uuid


# ---- CONSTANTS ----
GUARANTOR_REQUIRED_AMOUNT = 30000
PLATFORM_FEE_PERCENT = 3.0

BORROW_LIMITS = {
    "HIGH": 100000,
    "MEDIUM": 50000,
    "LOW": 10000,
    "BLOCKED": 0,
}


# =========================
# CREDIT SCORE ENFORCEMENT
# =========================

def get_credit_limit(user_id: str) -> int:
    """
    Enforce borrowing limit using EXISTING credit score
    """
    score = get_item("credit_scores", user_id)

    if score is None:
        raise Exception("Credit score not initialized")

    if score >= 750:
        return BORROW_LIMITS["HIGH"]
    if score >= 650:
        return BORROW_LIMITS["MEDIUM"]
    if score >= 550:
        return BORROW_LIMITS["LOW"]
    return BORROW_LIMITS["BLOCKED"]


# =========================
# BORROWER FLOW
# =========================

def create_borrow_request(payload: BorrowRequestSchema):
    """
    STEP 1:
    - Check KYC
    - Enforce credit score limit
    - Calculate EMI & total payable
    - Generate UNSIGNED agreement PDF
    - Store loan as AWAITING_SIGNATURE
    """

    user_id = payload.user_id

    # 0️⃣ Mutual Exclusion: borrower vs lender
    all_loans = get_all_items("loans")
    for scan_loan_id, scan_loan in all_loans.items():
        if scan_loan.get("lender_id") == user_id and scan_loan.get("status") != "REPAID":
            raise Exception("Active lenders cannot borrow")
        if scan_loan["user_id"] == user_id:
            if scan_loan["status"] in ["PENDING_ADMIN_APPROVAL", "LISTED", "ACTIVE", "AWAITING_SIGNATURE"]:
                if not payload.loan_id or scan_loan_id != payload.loan_id:
                    raise Exception("You already have an active loan or request")

    # 1️⃣ KYC check
    kyc_data = get_item("kyc", user_id) or {}
    if not kyc_data or kyc_data.get("status") != "APPROVED":
        print(f"WARNING: KYC not approved for {user_id}, but bypassing for DEMO")
        # raise Exception("KYC not approved")

    # 2️⃣ Agreement acceptance
    if not payload.agreed_to_rules:
        raise Exception("Rules must be accepted")

    # 3️⃣ Credit score enforcement
    credit_score = get_item("credit_scores", user_id)
    if credit_score is None:
        print(f"WARNING: Credit score missing for {user_id}, mocking to 750 for DEMO")
        credit_score = 750 # DEMO HACK: Default high score
        # raise Exception("Credit score not available")

    # DEMO HACK: Bypass actual limit check
    # max_allowed = get_credit_limit(user_id)
    # if max_allowed == 0:
    #     raise Exception("Borrowing blocked due to low credit score")
    # if payload.amount > max_allowed:
    #     raise Exception("Requested amount exceeds credit limit")

    # 4️⃣ Guarantor rule - REQUIRED for amounts > 30k
    if payload.amount > GUARANTOR_REQUIRED_AMOUNT:
        if not payload.guarantor:
            raise Exception(f"Guarantor required for loan amounts exceeding NPR {GUARANTOR_REQUIRED_AMOUNT}")
        # Validate guarantor fields
        if not payload.guarantor.full_name or not payload.guarantor.full_name.strip():
            raise Exception("Guarantor full name is required")
        if not payload.guarantor.citizenship_no or not payload.guarantor.citizenship_no.strip():
            raise Exception("Guarantor citizenship number is required")
        if not payload.guarantor.relation or not payload.guarantor.relation.strip():
            raise Exception("Guarantor relationship is required")
        if not payload.guarantor.card_images or not payload.guarantor.card_images.front_image_ref or not payload.guarantor.card_images.back_image_ref:
            raise Exception("Guarantor citizenship card images (front and back) are required")

    # 5️⃣ Platform fee
    platform_fee = payload.amount * (PLATFORM_FEE_PERCENT / 100)
    net_amount_received = payload.amount - platform_fee

    # 6️⃣ EMI calculation (backend truth)
    emi_data = calculate_emi(
        principal=payload.amount,
        annual_interest_rate=payload.interest_rate,
        tenure_months=payload.tenure_months,
    )

    emi = emi_data["emi"]
    total_payable = emi_data["total_payable"]

    # 7️⃣ Loan ID
    loan_id = payload.loan_id or f"LN-{uuid.uuid4().hex[:8].upper()}"

    # 8️⃣ Get Borrower Details from KYC for PDF
    basic_info = kyc_data.get("basic_info", {})
    borrower_name = " ".join(filter(None, [basic_info.get("first_name"), basic_info.get("middle_name"), basic_info.get("last_name")]))
    borrower_cit_no = kyc_data.get("id_documents", {}).get("id_details", {}).get("id_number", "N/A")

    # 9️⃣ Generate unsigned agreement PDF
    pdf_ref = generate_loan_agreement_pdf(
        borrower_full_name=borrower_name,
        borrower_citizenship_no=borrower_cit_no,
        guarantor_full_name=payload.guarantor.full_name if payload.guarantor else "N/A",
        guarantor_citizenship_no=payload.guarantor.citizenship_no if payload.guarantor else "N/A",
        amount=payload.amount,
        interest_rate=payload.interest_rate,
        tenure_months=payload.tenure_months,
        net_amount_received=net_amount_received,
        net_amount_returned=total_payable,
    )

    # 9️⃣ Video Verification Enrollment
    if payload.video_verification_ref:
        # Get card from KYC
        front_image_ref = kyc_data["id_documents"]["id_images"]["front_image_ref"]
        video_result = verify_video_identity(
            video_path=payload.video_verification_ref,
            citizenship_image_path=front_image_ref
        )
        if video_result["final_status"] != "APPROVED":
            raise Exception(f"Video verification failed: {video_result.get('reason')}")

    # 🔟 Store loan draft (DB)
    loan_data = {
        "loan_id": loan_id,
        "user_id": user_id,
        "amount": payload.amount,
        "interest_rate": payload.interest_rate,
        "tenure_months": payload.tenure_months,
        "purpose": payload.purpose,
        "emi": emi,
        "total_payable": total_payable,
        "platform_fee": platform_fee,
        "net_amount_received": net_amount_received,
        "guarantor": payload.guarantor.dict() if payload.guarantor else None,
        "agreement_pdf_unsigned": pdf_ref,
        "agreement_pdf_signed": payload.agreement_pdf_signed,
        "video_verification_ref": payload.video_verification_ref,
        "credit_score": credit_score,
        "status": "PENDING_ADMIN_APPROVAL",
        "created_at": payload.submitted_at, # This is int from frontend
    }

    put_item("loans", loan_id, loan_data)
    print(f"Loan {loan_id} created and awaiting admin approval.")

    return {
        "loan_id": loan_id,
        "status": "PENDING_ADMIN_APPROVAL",
        "agreement_pdf": f"/pdfs/{os.path.basename(pdf_ref)}",
        "emi": emi,
        "total_payable": total_payable,
        "credit_score": credit_score,
    }


# =========================
# MARKETPLACE
# =========================

def get_marketplace_listings():
    """
    Public marketplace (LISTED loans only)
    """
    listings = []

    loans_map = get_all_items("loans")

    for loan_id, loan in loans_map.items():
        if loan.get("status") != "LISTED":
            continue

        # Fetch borrower name
        user_id = loan["user_id"]
        user = get_item("users", user_id)
        
        borrower_display_name = "Unknown"
        if user:
            # Format: "Ram K."
            f_name = user.get("first_name", "")
            l_name = user.get("last_name", "")
            if l_name:
                borrower_display_name = f"{f_name} {l_name[0]}."
            else:
                borrower_display_name = f_name

        listings.append(
            MarketplaceLoanSchema(
                loan_id=loan_id,
                borrower_name=borrower_display_name,
                amount=loan["amount"],
                purpose=loan["purpose"],
                interest_rate=loan["interest_rate"],
                tenure_months=loan["tenure_months"],
                status=loan["status"],
                credit_score=loan.get("credit_score")
            )
        )

    return listings


# =========================
# LENDER FLOW
# =========================

def accept_loan(payload: LenderAcceptanceSchema):
    """
    Lender accepts a LISTED loan
    """

    loan_id = payload.loan_id
    lender_id = payload.lender_id
    
    # EARLY CHECK: Prevent self-funding
    loan = get_item("loans", loan_id)
    if not loan:
        raise Exception("Loan not found")
    
    if loan["user_id"] == lender_id:
        raise Exception("You cannot fund your own loan")
    
    # 0️⃣ Mutual Exclusion: Borrower cannot Lend
    all_loans = get_all_items("loans")
    total_lended_so_far = 0
    
    for _, scan_loan in all_loans.items():
        # Check if lender is acting as a borrower elsewhere
        if scan_loan["user_id"] == lender_id:
             if scan_loan["status"] in ["LISTED", "ACTIVE", "AWAITING_SIGNATURE"]:
                 raise Exception("Borrowers cannot lend money")
        
        # Calculate total active lending
        if scan_loan.get("lender_id") == lender_id and scan_loan.get("status") != "REPAID":
            total_lended_so_far += scan_loan["amount"]

    # 0️⃣ Lending Limit: Max 500,000
    LENDING_LIMIT = 500000
    loan_to_accept = get_item("loans", loan_id) # Need amount
    if not loan_to_accept:
         raise Exception("Loan not found")
         
    if total_lended_so_far + loan_to_accept["amount"] > LENDING_LIMIT:
        raise Exception("Lending limit (500,000) exceeded")

    if loan["status"] != "LISTED":
        raise Exception("Loan is not available for acceptance")

    lender_kyc = get_item("kyc", lender_id)
    if not lender_kyc or lender_kyc.get("status") != "APPROVED":
        raise Exception("Lender KYC not approved")

    # Update loan
    loan["lender_id"] = lender_id
    loan["status"] = "ACTIVE"
    loan["start_timestamp"] = payload.accepted_at.isoformat()

    put_item("loans", loan_id, loan)

    # Store acceptance for audit
    put_item(
        "loan_acceptances",
        loan_id,
        {
            "loan_id": loan_id,
            "lender_id": lender_id,
            "accepted_at": payload.accepted_at.isoformat(),
        },
    )

    # Blockchain proof
    record_loan_acceptance(
        {
            "loan_id": loan_id,
            "lender_id": lender_id,
            "accepted_at": payload.accepted_at,
        },
        loan_id,
    )

    record_loan_status(
        {
            "status": "ACTIVE",
            "timestamp": payload.accepted_at,
        },
        loan_id,
    )

    return {"message": "Loan accepted and activated"}


# =========================
# PORTFOLIO
# =========================

def get_user_portfolio(user_id: str):
    """
    Get user's financial portfolio:
    - Active Borrowing (if any)
    - Active Investments (if any)
    """
    loans_map = get_all_items("loans")
    
    active_loan_data = None
    investments = []
    total_invested = 0
    interest_earned = 0 # This would be calculated from repayments in a real system
    
    from db.database import get_repayments

    # 1. Borrowing Side
    for loan_id, loan in loans_map.items():
        if loan["user_id"] == user_id:
            if loan["status"] in ["PENDING_ADMIN_APPROVAL", "LISTED", "ACTIVE", "AWAITING_SIGNATURE"]:
                # Count repayments
                repayments = get_repayments(loan_id)
                loan["paid_emis"] = len(repayments)
                # Calculate total repaid amount
                loan["total_repaid_amount"] = sum(r["amount"] for r in repayments)
                active_loan_data = loan
                break
    
    # 2. Lending Side
    for loan_id, loan in loans_map.items():
        if loan.get("lender_id") == user_id:
            investments.append(loan)
            total_invested += loan["amount"]
            # Est interest
            interest = loan["amount"] * (loan["interest_rate"] / 100)
            interest_earned += interest
            
    return {
        "active_loan": active_loan_data,
        "investment_stats": {
            "total_invested": total_invested,
            "interest_earned": interest_earned,
            "active_loans_count": len(investments),
            "loans": investments 
        }
    }
