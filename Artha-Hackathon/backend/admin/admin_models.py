from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db.database import Base


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="support_admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Borrower(Base):
    __tablename__ = "borrowers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    risk_score = Column(Float, default=0.5)
    status = Column(String, default="PENDING")
    is_blocked = Column(Boolean, default=False)
    kyc_status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)


class Lender(Base):
    __tablename__ = "lenders"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    kyc_status = Column(String, default="PENDING")
    portfolio_value = Column(Float, default=0)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    borrower_id = Column(Integer, ForeignKey("borrowers.id"), nullable=False)
    lender_id = Column(Integer, ForeignKey("lenders.id"), nullable=True)
    amount = Column(Float, nullable=False)
    interest_rate = Column(Float, default=0)
    status = Column(String, default="PENDING")
    issued_at = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    repaid_amount = Column(Float, default=0)

    borrower = relationship("Borrower")
    lender = relationship("Lender")


class KycRecord(Base):
    __tablename__ = "kyc_records"

    id = Column(Integer, primary_key=True, index=True)
    user_type = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    status = Column(String, default="PENDING")
    confidence_score = Column(Float, default=0)
    document_type = Column(String, default="citizenship")
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=True)
    tx_hash = Column(String, nullable=False)
    chain_status = Column(String, default="PENDING")
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    loan = relationship("Loan")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_type = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    status = Column(String, default="OPEN")
    priority = Column(String, default="MEDIUM")
    created_at = Column(DateTime, default=datetime.utcnow)
