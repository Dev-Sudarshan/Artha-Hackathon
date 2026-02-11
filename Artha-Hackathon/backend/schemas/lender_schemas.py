from pydantic import BaseModel


class LenderAcceptanceSchema(BaseModel):
    loan_id: str
    lender_id: str
    accepted_at: int
