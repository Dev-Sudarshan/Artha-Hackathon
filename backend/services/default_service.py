import time
from blockchain.loan_status import record_loan_status

from db.database import get_all_items, put_item, get_repayments


def check_and_mark_defaults():
    """
    Check ACTIVE loans and mark them DEFAULTED if overdue and unpaid
    """
    current_time = int(time.time())
    defaulted_loans = []

    all_loans = get_all_items("loans")
    for loan_id, loan in all_loans.items():
        # 1️⃣ Only ACTIVE loans can default
        if loan.get("status") != "ACTIVE":
            continue

        start_time = loan.get("start_timestamp")
        tenure_months = loan.get("tenure_months")
        total_due = loan.get("amount")

        if not start_time or not tenure_months:
            continue

        # 2️⃣ Calculate loan end time (simple month = 30 days)
        loan_end_time = start_time + (tenure_months * 30 * 24 * 60 * 60)

        # 3️⃣ Check repayment status
        repayments = get_repayments(loan_id)
        total_repaid = sum(r["amount"] for r in repayments)

        if current_time > loan_end_time and total_repaid < total_due:
            # 4️⃣ Mark DEFAULTED
            loan["status"] = "DEFAULTED"

            put_item("loans", loan_id, loan)

            record_loan_status(
                {
                    "status": "DEFAULTED",
                    "timestamp": current_time,
                    "reason": "Loan overdue and unpaid",
                },
                loan_id,
            )

            defaulted_loans.append(loan_id)

    return {
        "message": "Default check completed",
        "defaulted_loans": defaulted_loans,
    }
