from pydantic import BaseModel


class TransactionReceiptSchema(BaseModel):
    loan_id: str

    transaction_id: str
    amount: float

    sender_account: str
    receiver_account: str

    timestamp: int
    success: bool
