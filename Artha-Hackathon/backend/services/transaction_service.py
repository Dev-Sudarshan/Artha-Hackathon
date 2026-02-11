from schemas.transaction_schemas import TransactionReceiptSchema
from blockchain.transactions import (
    record_transaction_receipt,
    record_fee_allocation,
)
from blockchain.loan_status import record_loan_status

from db.database import get_item, put_item, get_all_items

# ---- STORES REPLACED BY DB ----

PLATFORM_FEE_PERCENT = 3.0


def process_fund_transfer(payload: TransactionReceiptSchema, lender_id: str):
    """
    Process fund transfer receipt. Enables LISTED -> ACTIVE transition (Auto-Accept).
    """

    loan_id = payload.loan_id

    # 1️⃣ Loan must exist
    loan = get_item("loans", loan_id)
    if not loan:
        raise Exception("Loan not found")

    borrower_id = loan["user_id"]
    
    # 0️⃣ Self-Lending Check
    if borrower_id == lender_id:
        raise Exception("Cannot lend to your own loan")

    # 2️⃣ Borrower/Lender exclusivity check
    all_loans = get_all_items("loans")
    for _, scan_loan in all_loans.items():
        if scan_loan.get("user_id") == lender_id and scan_loan.get("status") in ["LISTED", "ACTIVE", "AWAITING_SIGNATURE"]:
            raise Exception("Borrowers cannot lend money")

    # 3️⃣ Handle Status (Auto-Accept if LISTED)
    current_status = loan.get("status")
    
    if current_status == "LISTED":
        # Check if already funded (race condition check)
        if loan.get("lender_id"):
             raise Exception("Loan already assigned to a lender")
             
        # Transition to ACTIVE
        loan["status"] = "ACTIVE"
        loan["lender_id"] = lender_id
        # Use payload timestamp for consistency
        import datetime
        # If payload.timestamp is int (unix), convert? Schema says int.
        # But usually we store ISO strings in DB for readability? 
        # Existing code used payload.timestamp directly in record_loan_status.
        # Let's verify schema. Schema says int. 
        # Let's save it as handled below.
        
        # Save updated loan status immediately
        put_item("loans", loan_id, loan)
        
    elif current_status != "ACTIVE":
        raise Exception(f"Loan status is {current_status}, cannot fund.")

    # 4️⃣ Prevent duplicate funding (Check transactions table)
    existing_txn = get_item("transactions", loan_id)
    if existing_txn:
        raise Exception("Loan already funded")

    # 5️⃣ Initialize financial data if missing
    stats = get_item("financial_data", borrower_id)
    if not stats:
        stats = {
            "monthly_income": 0,
            "monthly_expense": 0,
            "total_transactions": 0,
            "failed_transactions": 0,
            "avg_transaction_amount": 0.0,
            "missed_payments": 0,
            "loan_outstanding": 0.0,
            "account_age_months": 0,
        }

    # 6️⃣ Update transaction counters
    stats["total_transactions"] += 1

    if not payload.success:
        stats["failed_transactions"] += 1
        put_item("financial_data", borrower_id, stats)
        raise Exception("Transaction failed")

    # 7️⃣ Store transaction receipt off-chain
    receipt_data = payload.dict()
    # Normalize timestamp to ISO string for storage
    ts_value = receipt_data.get("timestamp")
    if isinstance(ts_value, int):
        import datetime
        receipt_data["timestamp"] = datetime.datetime.fromtimestamp(ts_value).isoformat()
    elif hasattr(ts_value, "isoformat"):
        receipt_data["timestamp"] = ts_value.isoformat()
    
    put_item("transactions", loan_id, receipt_data)

    # 8️⃣ Update average transaction amount
    prev_total = stats["total_transactions"] - 1
    stats["avg_transaction_amount"] = (
        (stats["avg_transaction_amount"] * prev_total + payload.amount)
        / stats["total_transactions"]
    )

    # 9️⃣ Platform fee calculation
    fee_amount = payload.amount * (PLATFORM_FEE_PERCENT / 100)
    net_to_borrower = payload.amount - fee_amount

    # 10️⃣ Update outstanding loan amount
    stats["loan_outstanding"] += payload.amount
    
    # Save stats
    put_item("financial_data", borrower_id, stats)

    # 🔒 Blockchain: transaction receipt
    record_transaction_receipt(
        txn_payload=receipt_data,
        tx_id=payload.transaction_id,
    )

    # 🔒 Blockchain: fee allocation
    record_fee_allocation(
        fee_payload={
            "loan_id": loan_id,
            "gross_amount": payload.amount,
            "platform_fee_percent": PLATFORM_FEE_PERCENT,
            "platform_fee_amount": fee_amount,
            "net_to_borrower": net_to_borrower,
        },
        loan_id=loan_id,
    )

    # 🔒 Confirm ACTIVE status
    record_loan_status(
        {
            "status": "ACTIVE",
            "timestamp": payload.timestamp,
        },
        loan_id,
    )

    return {
        "message": "Fund transfer recorded successfully",
        "platform_fee": fee_amount,
        "net_to_borrower": net_to_borrower,
    }
