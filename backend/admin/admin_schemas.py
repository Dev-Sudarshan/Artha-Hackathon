from datetime import date, datetime
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class Page(GenericModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class AdminUserOut(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime


class BorrowerOut(BaseModel):
    id: int
    full_name: str
    email: Optional[str]
    risk_score: float
    status: str
    is_blocked: bool
    kyc_status: str
    created_at: datetime


class LenderOut(BaseModel):
    id: int
    full_name: str
    email: Optional[str]
    kyc_status: str
    portfolio_value: float
    is_blocked: bool
    created_at: datetime


class LoanOut(BaseModel):
    id: int
    loan_id: str
    borrower_phone: str
    lender_phone: Optional[str]
    amount: float
    interest_rate: float
    status: str
    created_at: Optional[datetime] = None
    agreement_pdf_unsigned: Optional[str] = None
    agreement_pdf_signed: Optional[str] = None
    video_verification_ref: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    blockchain_loan_hash: Optional[str] = None
    blockchain_repayment_tx_hash: Optional[str] = None
    # Video verification fields
    kyc_selfie_ref: Optional[str] = None
    video_frame_ref: Optional[str] = None
    video_verification_result: Optional[dict] = None
    ai_suggestion: Optional[str] = None
    ai_suggestion_reason: Optional[str] = None


class KycRecordOut(BaseModel):
    id: int
    user_type: str
    user_phone: str
    full_name: str
    status: str
    ai_suggested_status: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    doc_front_url: Optional[str] = None
    doc_back_url: Optional[str] = None
    selfie_url: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    blockchain_kyc_hash: Optional[str] = None
    created_at: datetime


class AdminDecisionIn(BaseModel):
    reason: Optional[str] = None


class KycDetailsOut(BaseModel):
    user_phone: str
    full_name: str
    status: str
    age: Optional[int] = None
    location: Optional[str] = None
    doc_front_url: Optional[str] = None
    doc_back_url: Optional[str] = None
    selfie_url: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    blockchain_kyc_hash: Optional[str] = None
    kyc: dict[str, Any]


class TransactionOut(BaseModel):
    id: int
    loan_id: Optional[int]
    tx_hash: str
    chain_status: str
    amount: float
    created_at: datetime


class SupportTicketOut(BaseModel):
    id: int
    user_type: str
    user_id: int
    subject: str
    status: str
    priority: str
    created_at: datetime


class BorrowerStatusUpdate(BaseModel):
    status: Optional[str] = None
    is_blocked: Optional[bool] = None
    kyc_status: Optional[str] = None


class LenderStatusUpdate(BaseModel):
    kyc_status: Optional[str] = None
    is_blocked: Optional[bool] = None


class LoanStatusUpdate(BaseModel):
    status: Optional[str] = None
    repaid_amount: Optional[float] = None


class KycStatusUpdate(BaseModel):
    status: Optional[str] = None
    confidence_score: Optional[float] = None


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None


class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class DashboardKpiOut(BaseModel):
    active_loans: int
    total_funded: float
    default_rate: float
    pending_kyc: int
    flagged_accounts: int


class WatchlistItemOut(BaseModel):
    label: str
    value: float
    risk_level: str


class AlertItemOut(BaseModel):
    label: str
    value: int
    status: str


class DashboardOut(BaseModel):
    kpis: DashboardKpiOut
    watchlist: List[WatchlistItemOut]
    alerts: List[AlertItemOut]
