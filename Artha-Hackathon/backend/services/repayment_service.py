from schemas.repayment_schemas import RepaymentSchema
from blockchain.transactions import record_repayment
from blockchain.loan_status import record_loan_status

import uuid
from db.database import get_item, put_item, add_repayment, get_repayments

# ---- STORES REPLACED BY DB ----


# ---- CREDIT SCORE RULES ----
INITIAL_SCORE = 600
REWARD_ON_FULL_REPAY = 20
MAX_SCORE = 850


def _increase_credit_score(user_id: str):
    """
    Increase credit score after successful full repayment
    """
    current = get_item("credit_scores", user_id) or INITIAL_SCORE
    new_score = min(current + REWARD_ON_FULL_REPAY, MAX_SCORE)
    put_item("credit_scores", user_id, new_score)


def process_repayment(payload: RepaymentSchema):
    """
    Process partial or full loan repayment
    Credit score increases ONLY on full repayment
    """

    loan_id = payload.loan_id

    # 1️⃣ Loan must exist
    loan = get_item("loans", loan_id)
    if not loan:
        raise Exception("Loan not found")

    # 2️⃣ Loan must be ACTIVE
    if loan.get("status") != "ACTIVE":
        raise Exception("Loan is not active")

    # 3️⃣ Borrower check
    borrower_id = loan.get("user_id")
    if borrower_id != payload.paid_by:
        raise Exception("Only borrower can repay this loan")

    # 4️⃣ Track repayment amount
    # Use helper to get list, sum them
    existing_repayments = get_repayments(loan_id)
    total_repaid = sum(r["amount"] for r in existing_repayments)
    
    total_repaid += payload.amount
    
    # Store this new repayment record
    repayment_id = f"RP-{uuid.uuid4().hex[:8]}"
    rp_data = payload.dict()
    rp_data["repayment_id"] = repayment_id
    
    # Fix timestamp
    import datetime
    dt_object = datetime.datetime.fromtimestamp(rp_data["timestamp"])
    rp_data["timestamp"] = dt_object.isoformat()
    
    add_repayment(repayment_id, loan_id, rp_data)

    # 5️⃣ Blockchain write: repayment proof
    record_repayment(
        repayment_payload=payload.dict(),
        loan_id=loan_id,
    )

    # 6️⃣ FULL repayment → close loan + increase credit score
    # Auto-detect full repayment if amount covers total payable
    is_fully_repaid = payload.repayment_type == "FULL"
    
    if loan.get("total_payable") and total_repaid >= loan.get("total_payable"):
        is_fully_repaid = True

    if is_fully_repaid:
        loan["status"] = "REPAID"
        put_item("loans", loan_id, loan)

        # ✅ Increase fake credit score
        _increase_credit_score(borrower_id)

        record_loan_status(
            {
                "status": "REPAID",
                "timestamp": payload.timestamp,
            },
            loan_id,
        )

        return {
            "message": "Loan fully repaid",
            "new_credit_score": get_item("credit_scores", borrower_id),
        }

    # 7️⃣ Partial repayment (no credit score change)
    current_score = get_item("credit_scores", borrower_id) or INITIAL_SCORE
    return {
        "message": "Partial repayment recorded",
        "total_repaid": total_repaid,
        "credit_score": current_score,
    }
