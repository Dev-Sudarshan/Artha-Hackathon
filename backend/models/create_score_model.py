"""
CREDIT SCORE MODEL
------------------
Deterministic, explainable credit scoring logic.

Score range: 300 – 850
Higher score = lower risk
"""

from dataclasses import dataclass


# =========================
# INPUT DATA STRUCTURE
# =========================

@dataclass
class CreditScoreInput:
    monthly_income: float
    monthly_expense: float
    total_transactions: int
    failed_transactions: int
    avg_transaction_amount: float
    missed_payments: int
    loan_outstanding: float
    account_age_months: int


# =========================
# CORE CREDIT SCORE LOGIC
# =========================

def calculate_credit_score(data: CreditScoreInput) -> dict:
    """
    Calculate credit score based on financial behavior
    """

    # ---- Safety guards ----
    if data.monthly_income <= 0:
        raise ValueError("Monthly income must be greater than zero")

    if data.total_transactions <= 0:
        failure_rate = 0
    else:
        failure_rate = data.failed_transactions / data.total_transactions

    # ---- Feature engineering ----
    expense_ratio = data.monthly_expense / data.monthly_income
    utilization_ratio = data.loan_outstanding / data.monthly_income
    stability_factor = min(data.account_age_months, 60)

    # ---- Base score ----
    score = 850

    # ---- Risk penalties ----
    score -= expense_ratio * 200
    score -= failure_rate * 300
    score -= utilization_ratio * 250
    score -= data.missed_payments * 40

    # ---- Stability reward ----
    score += stability_factor * 2

    # ---- Clamp score ----
    score = max(300, min(int(score), 850))

    # ---- Risk band ----
    if score >= 750:
        risk_band = "HIGH"
        borrow_limit = "HIGH"
    elif score >= 650:
        risk_band = "MEDIUM"
        borrow_limit = "MEDIUM"
    elif score >= 550:
        risk_band = "LOW"
        borrow_limit = "LOW"
    else:
        risk_band = "BLOCKED"
        borrow_limit = "NONE"

    return {
        "credit_score": score,
        "risk_band": risk_band,
        "borrow_limit_category": borrow_limit,
        "features": {
            "expense_ratio": round(expense_ratio, 2),
            "failure_rate": round(failure_rate, 2),
            "utilization_ratio": round(utilization_ratio, 2),
            "account_age_months": data.account_age_months,
        },
    }


# =========================
# LOCAL TEST
# =========================

if __name__ == "__main__":
    sample = CreditScoreInput(
        monthly_income=50000,
        monthly_expense=20000,
        total_transactions=120,
        failed_transactions=3,
        avg_transaction_amount=1500,
        missed_payments=1,
        loan_outstanding=30000,
        account_age_months=24,
    )

    result = calculate_credit_score(sample)
    print(result)
