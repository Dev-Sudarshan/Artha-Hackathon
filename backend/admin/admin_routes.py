import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from admin import admin_models as models, admin_schemas as schemas
from admin.admin_auth import create_access_token, require_roles, verify_password
from db.database import get_db, get_all_items, get_item, put_item

router = APIRouter()
logger = logging.getLogger("artha.admin")


# ===========================
# ADAPTER FUNCTIONS
# ===========================

def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        # Heuristic: milliseconds if very large
        seconds = float(value) / 1000.0 if float(value) > 1_000_000_000_000 else float(value)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(tzinfo=None)
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
            return parsed.replace(tzinfo=None)
        except ValueError:
            return None
    return None


def _parse_date(value: Any) -> Optional[date]:
    dt = _parse_datetime(value)
    return dt.date() if dt else None

def get_user_type(user_phone: str, all_loans: dict = None) -> str:
    """Determine if user is borrower or lender based on loan history"""
    if all_loans is None:
        all_loans = get_all_items("loans")
    
    is_borrower = False
    is_lender = False
    
    for loan_id, loan in all_loans.items():
        if loan.get("user_id") == user_phone:
            is_borrower = True
        if loan.get("lender_id") == user_phone:
            is_lender = True
    
    if is_borrower and is_lender:
        return "both"
    elif is_borrower:
        return "borrower"
    elif is_lender:
        return "lender"
    return "unknown"


def transform_to_borrower(user_phone: str, user_data: dict, index: int, all_loans: dict = None, all_kyc: dict = None, all_scores: dict = None) -> schemas.BorrowerOut:
    """Transform JSONB user data to BorrowerOut schema"""
    if all_kyc is not None:
        kyc_data = all_kyc.get(user_phone) or {}
    else:
        kyc_data = get_item("kyc", user_phone) or {}
    if all_scores is not None:
        credit_score = all_scores.get(user_phone) or 600
    else:
        credit_score = get_item("credit_scores", user_phone) or 600
    
    # Get basic info from KYC if available
    basic_info = kyc_data.get("basic_info", {})
    full_name = f"{basic_info.get('first_name', '')} {basic_info.get('last_name', '')}".strip() or user_phone
    
    # Calculate risk score (inverse of credit score, normalized to 0-100)
    risk_score = max(0, min(100, (850 - credit_score) / 8.5))
    
    # Determine status based on loans
    if all_loans is None:
        all_loans = get_all_items("loans")
    status = "INACTIVE"
    for loan in all_loans.values():
        if loan.get("user_id") == user_phone:
            loan_status = loan.get("status", "")
            if loan_status in ["ACTIVE", "LISTED", "AWAITING_SIGNATURE"]:
                status = "ACTIVE"
                break
    
    return schemas.BorrowerOut(
        id=index,
        full_name=full_name,
        email=basic_info.get("email"),
        risk_score=round(risk_score, 2),
        status=status,
        is_blocked=credit_score < 550,
        kyc_status=kyc_data.get("status", "PENDING"),
        created_at=_parse_datetime(kyc_data.get("created_at")) or datetime.now()
    )


def transform_to_lender(user_phone: str, user_data: dict, index: int, all_loans: dict = None, all_kyc: dict = None) -> schemas.LenderOut:
    """Transform JSONB user data to LenderOut schema"""
    if all_kyc is not None:
        kyc_data = all_kyc.get(user_phone) or {}
    else:
        kyc_data = get_item("kyc", user_phone) or {}
    
    # Get basic info from KYC if available
    basic_info = kyc_data.get("basic_info", {})
    full_name = f"{basic_info.get('first_name', '')} {basic_info.get('last_name', '')}".strip() or user_phone
    
    # Calculate portfolio value from active loans
    if all_loans is None:
        all_loans = get_all_items("loans")
    portfolio_value = 0.0
    for loan in all_loans.values():
        if loan.get("lender_id") == user_phone and loan.get("status") == "ACTIVE":
            portfolio_value += loan.get("amount", 0)
    
    return schemas.LenderOut(
        id=index,
        full_name=full_name,
        email=basic_info.get("email"),
        kyc_status=kyc_data.get("status", "PENDING"),
        portfolio_value=portfolio_value,
        is_blocked=False,  # No blocking logic for lenders in current system
        created_at=_parse_datetime(kyc_data.get("created_at")) or datetime.now()
    )


def transform_to_loan(loan_id: str, loan_data: dict, index: int) -> schemas.LoanOut:
    """Transform JSONB loan data to LoanOut schema"""
    return schemas.LoanOut(
        id=index,
        loan_id=loan_id,
        borrower_phone=str(loan_data.get("user_id") or ""),
        lender_phone=str(loan_data.get("lender_id")) if loan_data.get("lender_id") else None,
        amount=float(loan_data.get("amount", 0)),
        interest_rate=float(loan_data.get("interest_rate", 0)),
        status=loan_data.get("status", "UNKNOWN"),
        created_at=_parse_datetime(loan_data.get("created_at")),
    )


def transform_to_kyc(user_id: str, kyc_data: dict, index: int, all_loans: dict = None, all_users: dict = None) -> schemas.KycRecordOut:
    """Transform JSONB KYC data to KycRecordOut schema"""
    user_type = get_user_type(user_id, all_loans=all_loans)

    basic_info = (kyc_data.get("basic_info") or {})
    full_name = " ".join(
        [
            str(basic_info.get("first_name") or "").strip(),
            str(basic_info.get("middle_name") or "").strip(),
            str(basic_info.get("last_name") or "").strip(),
        ]
    ).strip()
    if not full_name:
        if all_users is not None:
            user = all_users.get(user_id) or {}
        else:
            user = get_item("users", user_id) or {}
        full_name = " ".join(
            [
                str(user.get("first_name") or user.get("firstName") or "").strip(),
                str(user.get("last_name") or user.get("lastName") or "").strip(),
            ]
        ).strip() or user_id

    # Age (best-effort)
    age = None
    dob_value = basic_info.get("date_of_birth") or basic_info.get("dob")
    if dob_value:
        try:
            dob = datetime.fromisoformat(str(dob_value)).date()
            today = datetime.now().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except ValueError:
            age = None

    # Location summary from permanent address
    perm = kyc_data.get("permanent_address") or {}
    location = ", ".join(
        [
            str(perm.get("municipality") or "").strip(),
            str(perm.get("district") or "").strip(),
            str(perm.get("province") or "").strip(),
        ]
    ).strip(" ,") or None

    # Document + selfie refs (stored as /static/...)
    id_docs = kyc_data.get("id_documents") or {}
    id_imgs = (id_docs.get("id_images") or {}) if isinstance(id_docs, dict) else {}
    doc_front_url = id_imgs.get("front_image_ref")
    doc_back_url = id_imgs.get("back_image_ref")

    declaration = kyc_data.get("declaration") or {}
    decl_video = (declaration.get("declaration_video") or {}) if isinstance(declaration, dict) else {}
    selfie_url = decl_video.get("selfie_image_ref")

    ai_suggested = None
    final_result = kyc_data.get("final_result") or {}
    if isinstance(final_result, dict):
        ai_suggested = final_result.get("ai_suggested_status")

    return schemas.KycRecordOut(
        id=index,
        user_type=user_type,
        user_phone=user_id,
        full_name=full_name,
        status=kyc_data.get("status", "PENDING"),
        ai_suggested_status=ai_suggested,
        age=age,
        location=location,
        doc_front_url=doc_front_url,
        doc_back_url=doc_back_url,
        selfie_url=selfie_url,
        created_at=_parse_datetime(kyc_data.get("created_at")) or datetime.now(),
    )


def log_action(admin_id: int, action: str, target: str):
    logger.info("admin=%s action=%s target=%s", admin_id, action, target)


# ===========================
# ADMIN ENDPOINTS
# ===========================


@router.get("/admin/dashboard", response_model=schemas.DashboardOut)
def get_dashboard(
    admin=Depends(require_roles(["super_admin", "finance_admin", "support_admin"])),
):
    """
    Dashboard with real-time KPIs from Artha JSONB database
    """
    all_loans = get_all_items("loans")
    all_kyc = get_all_items("kyc")
    
    # Calculate KPIs
    active_loans = sum(1 for loan in all_loans.values() if loan.get("status") == "ACTIVE")
    total_funded = sum(loan.get("amount", 0) for loan in all_loans.values() if loan.get("status") in ["ACTIVE", "REPAID"])
    
    # Calculate default rate (loans overdue / total active)
    overdue_count = 0
    for loan in all_loans.values():
        if loan.get("status") == "ACTIVE" and loan.get("due_date"):
            due = _parse_date(loan.get("due_date"))
            if due and due < datetime.now().date():
                overdue_count += 1
    
    default_rate = (overdue_count / active_loans * 100) if active_loans > 0 else 0.0
    
    # Count pending KYC (any PENDING*)
    pending_kyc = sum(
        1
        for kyc in all_kyc.values()
        if str(kyc.get("status") or "").upper().startswith("PENDING")
    )
    
    # Count flagged accounts (borrowers with low credit score)
    borrower_phones = {loan.get("user_id") for loan in all_loans.values() if loan.get("user_id")}
    flagged_accounts = sum(1 for phone in borrower_phones if (get_item("credit_scores", phone) or 600) < 550)
    
    kpis = schemas.DashboardKpiOut(
        active_loans=active_loans,
        total_funded=float(total_funded),
        default_rate=round(default_rate, 2),
        pending_kyc=pending_kyc,
        flagged_accounts=flagged_accounts
    )

    # Build watchlist (high-risk loans)
    watchlist = []
    for loan_id, loan in list(all_loans.items())[:5]:  # Top 5 for watchlist
        if loan.get("status") == "ACTIVE":
            borrower_id = loan.get("user_id", "unknown")
            credit_score = get_item("credit_scores", borrower_id) or 600
            if credit_score < 650:
                watchlist.append(schemas.WatchlistItemOut(
                    label=f"Loan {loan_id[:8]}...",
                    value=loan.get("amount", 0),
                    risk_level="HIGH" if credit_score < 550 else "MEDIUM"
                ))
    
    # System alerts
    alerts = [
        schemas.AlertItemOut(
            label="System Active",
            value=len(all_loans),
            status="ACTIVE"
        ),
        schemas.AlertItemOut(
            label="Pending KYC",
            value=pending_kyc,
            status="WARNING" if pending_kyc > 5 else "OK"
        ),
    ]

    return schemas.DashboardOut(
        kpis=kpis,
        watchlist=watchlist,
        alerts=alerts,
    )


@router.post("/admin/auth/login", response_model=schemas.TokenOut)
def admin_login(payload: schemas.AdminLoginRequest, db: Session = Depends(get_db)):
    try:
        admin = db.query(models.AdminUser).filter(models.AdminUser.email == payload.email).first()
    except SQLAlchemyError as exc:
        logger.exception("Database error during login")
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

    if not admin or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": admin.email, "role": admin.role, "admin_id": admin.id})
    return schemas.TokenOut(access_token=token, role=admin.role)



@router.get("/admin/borrowers", response_model=schemas.Page[schemas.BorrowerOut])
def list_borrowers(
    status: Optional[str] = None,
    risk_score_min: Optional[float] = Query(default=None),
    risk_score_max: Optional[float] = Query(default=None),
    skip: int = 0,
    limit: int = 25,
    admin=Depends(require_roles(["super_admin", "finance_admin", "support_admin"])),
):
    """
    List all borrowers from Artha JSONB database
    """
    all_users = get_all_items("users")
    all_loans = get_all_items("loans")
    all_kyc = get_all_items("kyc")
    all_scores = get_all_items("credit_scores")
    
    # Find all users who have borrowed
    borrower_phones = set()
    for loan in all_loans.values():
        if loan.get("user_id"):
            borrower_phones.add(loan["user_id"])
    
    # Transform to BorrowerOut schema
    borrowers = []
    for idx, phone in enumerate(borrower_phones):
        user_data = all_users.get(phone, {})
        borrower = transform_to_borrower(phone, user_data, idx + 1, all_loans=all_loans, all_kyc=all_kyc, all_scores=all_scores)
        
        # Apply filters
        if status and borrower.status != status:
            continue
        if risk_score_min is not None and borrower.risk_score < risk_score_min:
            continue
        if risk_score_max is not None and borrower.risk_score > risk_score_max:
            continue
        
        borrowers.append(borrower)
    
    # Sort by ID and paginate
    borrowers.sort(key=lambda x: x.id)
    total = len(borrowers)
    items = borrowers[skip:skip + limit]
    
    return schemas.Page(items=items, total=total, skip=skip, limit=limit)


@router.patch("/admin/borrowers/{borrower_id}")
def update_borrower(
    borrower_id: int,
    payload: schemas.BorrowerStatusUpdate,
    admin=Depends(require_roles(["super_admin", "finance_admin"])),
):
    """TODO: Integrate with Artha JSONB storage"""
    raise HTTPException(status_code=404, detail="Borrower not found")



@router.get("/admin/lenders", response_model=schemas.Page[schemas.LenderOut])
def list_lenders(
    kyc_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 25,
    admin=Depends(require_roles(["super_admin", "finance_admin", "support_admin"])),
):
    """
    List all lenders from Artha JSONB database
    """
    all_users = get_all_items("users")
    all_loans = get_all_items("loans")
    all_kyc = get_all_items("kyc")
    
    # Find all users who have lent
    lender_phones = set()
    for loan in all_loans.values():
        if loan.get("lender_id"):
            lender_phones.add(loan["lender_id"])
    
    # Transform to LenderOut schema
    lenders = []
    for idx, phone in enumerate(lender_phones):
        user_data = all_users.get(phone, {})
        lender = transform_to_lender(phone, user_data, idx + 1, all_loans=all_loans, all_kyc=all_kyc)
        
        # Apply filters
        if kyc_status and lender.kyc_status != kyc_status:
            continue
        
        lenders.append(lender)
    
    # Sort by ID and paginate
    lenders.sort(key=lambda x: x.id)
    total = len(lenders)
    items = lenders[skip:skip + limit]
    
    return schemas.Page(items=items, total=total, skip=skip, limit=limit)


@router.patch("/admin/lenders/{lender_id}", response_model=schemas.LenderOut)
def update_lender(
    lender_id: int,
    payload: schemas.LenderStatusUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(["super_admin", "finance_admin"])),
):
    lender = db.get(models.Lender, lender_id)
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    if payload.kyc_status is not None:
        lender.kyc_status = payload.kyc_status
    if payload.is_blocked is not None:
        lender.is_blocked = payload.is_blocked
    db.commit()
    db.refresh(lender)
    log_action(admin.id, "update_lender", f"lender:{lender_id}")
    return lender



@router.get("/admin/loans", response_model=schemas.Page[schemas.LoanOut])
def list_loans(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 25,
    admin=Depends(require_roles(["super_admin", "finance_admin"])),
):
    """
    List all loans from Artha JSONB database
    """
    all_loans = get_all_items("loans")
    
    # Transform to LoanOut schema
    loans = []
    for idx, (loan_id, loan_data) in enumerate(all_loans.items()):
        loan = transform_to_loan(loan_id, loan_data, idx + 1)
        
        # Apply filters
        if status and loan.status != status:
            continue
        
        loans.append(loan)
    
    # Sort by ID and paginate
    loans.sort(key=lambda x: x.id)
    total = len(loans)
    items = loans[skip:skip + limit]
    
    return schemas.Page(items=items, total=total, skip=skip, limit=limit)

@router.post("/admin/loans/{loan_id}/approve")
def approve_loan(
    loan_id: str,
    payload: schemas.AdminDecisionIn,
    admin=Depends(require_roles(["super_admin", "finance_admin"])),
):
    loan = get_item("loans", loan_id) or {}
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if loan.get("status") != "PENDING_ADMIN_APPROVAL":
        raise HTTPException(status_code=400, detail=f"Loan is not pending admin approval (status={loan.get('status')})")

    loan["status"] = "LISTED"
    loan["admin_review"] = {
        "reviewed_by": admin.email,
        "reviewed_at": datetime.utcnow().isoformat(),
        "decision": "APPROVED",
        "reason": payload.reason,
    }
    put_item("loans", loan_id, loan)
    return {"message": "Loan approved and listed", "loan_id": loan_id, "status": "LISTED"}


@router.post("/admin/loans/{loan_id}/reject")
def reject_loan(
    loan_id: str,
    payload: schemas.AdminDecisionIn,
    admin=Depends(require_roles(["super_admin", "finance_admin"])),
):
    loan = get_item("loans", loan_id) or {}
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if loan.get("status") != "PENDING_ADMIN_APPROVAL":
        raise HTTPException(status_code=400, detail=f"Loan is not pending admin approval (status={loan.get('status')})")

    loan["status"] = "REJECTED_BY_ADMIN"
    loan["admin_review"] = {
        "reviewed_by": admin.email,
        "reviewed_at": datetime.utcnow().isoformat(),
        "decision": "REJECTED",
        "reason": payload.reason,
    }
    put_item("loans", loan_id, loan)
    return {"message": "Loan rejected", "loan_id": loan_id, "status": "REJECTED_BY_ADMIN"}


@router.get("/admin/kyc", response_model=schemas.Page[schemas.KycRecordOut])
def list_kyc(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 25,
    admin=Depends(require_roles(["super_admin", "support_admin"])),
):
    """
    List all KYC records from Artha JSONB database
    """
    all_kyc = get_all_items("kyc")
    all_loans = get_all_items("loans")
    all_users = get_all_items("users")
    
    # Transform to KycRecordOut schema
    kyc_records = []
    for idx, (user_id, kyc_data) in enumerate(all_kyc.items()):
        record = transform_to_kyc(user_id, kyc_data, idx + 1, all_loans=all_loans, all_users=all_users)
        
        # Apply filters
        if status and record.status != status:
            continue
        
        kyc_records.append(record)
    
    # Sort by ID and paginate
    kyc_records.sort(key=lambda x: x.id)
    total = len(kyc_records)
    items = kyc_records[skip:skip + limit]
    
    return schemas.Page(items=items, total=total, skip=skip, limit=limit)


@router.get("/admin/kyc/{user_phone}", response_model=schemas.KycDetailsOut)
def get_kyc_details(
    user_phone: str,
    admin=Depends(require_roles(["super_admin", "support_admin"])),
):
    kyc_data = get_item("kyc", user_phone) or {}
    if not kyc_data:
        raise HTTPException(status_code=404, detail="KYC record not found")

    record = transform_to_kyc(user_phone, kyc_data, 1)
    return schemas.KycDetailsOut(
        user_phone=user_phone,
        full_name=record.full_name,
        status=record.status,
        age=record.age,
        location=record.location,
        doc_front_url=record.doc_front_url,
        doc_back_url=record.doc_back_url,
        selfie_url=record.selfie_url,
        kyc=kyc_data,
    )


@router.post("/admin/kyc/{user_phone}/approve")
def approve_kyc(
    user_phone: str,
    payload: schemas.AdminDecisionIn,
    admin=Depends(require_roles(["super_admin", "support_admin"])),
):
    kyc_data = get_item("kyc", user_phone) or {}
    if not kyc_data:
        raise HTTPException(status_code=404, detail="KYC record not found")

    kyc_data["status"] = "APPROVED"
    kyc_data["review"] = {
        "reviewed_by": admin.email,
        "reviewed_at": datetime.utcnow().isoformat(),
        "decision": "APPROVED",
        "reason": payload.reason,
    }
    put_item("kyc", user_phone, kyc_data)
    return {"message": "KYC approved", "user_phone": user_phone, "status": "APPROVED"}


@router.post("/admin/kyc/{user_phone}/reject")
def reject_kyc(
    user_phone: str,
    payload: schemas.AdminDecisionIn,
    admin=Depends(require_roles(["super_admin", "support_admin"])),
):
    kyc_data = get_item("kyc", user_phone) or {}
    if not kyc_data:
        raise HTTPException(status_code=404, detail="KYC record not found")

    kyc_data["status"] = "REJECTED"
    kyc_data["review"] = {
        "reviewed_by": admin.email,
        "reviewed_at": datetime.utcnow().isoformat(),
        "decision": "REJECTED",
        "reason": payload.reason,
    }
    put_item("kyc", user_phone, kyc_data)
    return {"message": "KYC rejected", "user_phone": user_phone, "status": "REJECTED"}


@router.patch("/admin/kyc/{record_id}")
def update_kyc(record_id: int, admin=Depends(require_roles(["super_admin", "support_admin"]))):
    raise HTTPException(status_code=400, detail="Use /admin/kyc/{user_phone}/approve or /reject")


@router.get("/admin/transactions", response_model=schemas.Page[schemas.TransactionOut])
def list_transactions(
    chain_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 25,
    admin=Depends(require_roles(["super_admin", "finance_admin"])),
):
    """
    List all blockchain transactions from Artha (note: transactions table stores by loan_id)
    Currently returns sample data as transaction structure needs clarification
    """
    # Note: transactions table in Artha uses loan_id as primary key
    # and stores receipt data, not individual transactions
    # For a proper transaction history, would need to modify the schema
    
    return schemas.Page(items=[], total=0, skip=skip, limit=limit)


@router.get("/admin/support-tickets", response_model=schemas.Page[schemas.SupportTicketOut])
def list_support_tickets(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(["super_admin", "support_admin"])),
):
    query = db.query(models.SupportTicket)
    if status:
        query = query.filter(models.SupportTicket.status == status)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return schemas.Page(items=items, total=total, skip=skip, limit=limit)


@router.patch("/admin/support-tickets/{ticket_id}", response_model=schemas.SupportTicketOut)
def update_support_ticket(
    ticket_id: int,
    payload: schemas.SupportTicketUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(["super_admin", "support_admin"])),
):
    ticket = db.get(models.SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if payload.status is not None:
        ticket.status = payload.status
    if payload.priority is not None:
        ticket.priority = payload.priority
    db.commit()
    db.refresh(ticket)
    log_action(admin.id, "update_ticket", f"ticket:{ticket_id}")
    return ticket


@router.get("/admin/users", response_model=schemas.Page[schemas.AdminUserOut])
def list_admin_users(
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 25,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(["super_admin"])),
):
    query = db.query(models.AdminUser)
    if role:
        query = query.filter(models.AdminUser.role == role)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return schemas.Page(items=items, total=total, skip=skip, limit=limit)


@router.patch("/admin/users/{admin_id}", response_model=schemas.AdminUserOut)
def update_admin_user(
    admin_id: int,
    payload: schemas.AdminUserUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles(["super_admin"])),
):
    target = db.get(models.AdminUser, admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin user not found")
    if payload.role is not None:
        target.role = payload.role
    if payload.is_active is not None:
        target.is_active = payload.is_active
    db.commit()
    db.refresh(target)
    log_action(admin.id, "update_admin", f"admin:{admin_id}")
    return target
