from pydantic import BaseModel
from datetime import datetime


class SignedAgreementUploadSchema(BaseModel):
    """
    Payload for uploading signed loan agreement PDF
    """
    loan_id: str
    signed_pdf_ref: str   # file path / storage reference
    uploaded_at: datetime
