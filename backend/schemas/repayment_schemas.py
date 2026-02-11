from pydantic import BaseModel


class RepaymentSchema(BaseModel):
    loan_id: str

    repayment_id: str
    amount: float

    repayment_type: str    # "PARTIAL" or "FULL"

    paid_by: str           # borrower user_id
    timestamp: int
