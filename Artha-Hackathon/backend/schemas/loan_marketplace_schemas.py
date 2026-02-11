from pydantic import BaseModel


class MarketplaceLoanSchema(BaseModel):
    loan_id: str

    borrower_name: str      # display name (first name / masked)
    amount: int
    purpose: str
    interest_rate: float
    tenure_months: int
    credit_score: int | None = None

    status: str             # LISTED only
