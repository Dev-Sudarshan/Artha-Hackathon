from pydantic import BaseModel
from typing import Optional


# -------- GUARANTOR INFO --------

class GuarantorCardImages(BaseModel):
    front_image_ref: str
    back_image_ref: str


class GuarantorInfo(BaseModel):
    full_name: str
    relation: str
    citizenship_no: str
    card_images: GuarantorCardImages


# -------- BORROW REQUEST --------

class BorrowRequestSchema(BaseModel):
    user_id: str
    loan_id: Optional[str] = None # For updating draft in Step 2

    amount: int                  # requested amount
    interest_rate: float = 13.0   # fixed at 13
    tenure_months: int
    purpose: str

    emi_amount: float            # calculated on frontend (shown to user)

    guarantor: Optional[GuarantorInfo] = None

    agreement_pdf_signed: Optional[str] = None # uploaded signed PDF
    video_verification_ref: Optional[str] = None # uploaded video statement

    agreed_to_rules: bool         # must be True

    platform_fee_percent: float = 3.0
    net_amount_received: float   # amount - 3%

    submitted_at: int
