from pydantic import BaseModel, Field


class CreditScoreInputSchema(BaseModel):
    """
    Input schema for credit score calculation
    """

    monthly_income: float = Field(..., gt=0)
    monthly_expense: float = Field(..., ge=0)

    total_transactions: int = Field(..., ge=0)
    failed_transactions: int = Field(..., ge=0)

    avg_transaction_amount: float = Field(..., ge=0)

    missed_payments: int = Field(..., ge=0)

    loan_outstanding: float = Field(..., ge=0)

    account_age_months: int = Field(..., ge=0)


class CreditScoreResponseSchema(BaseModel):
    """
    Output schema for credit score result
    """

    credit_score: int
    risk_band: str
    borrow_limit_category: str

    features: dict
