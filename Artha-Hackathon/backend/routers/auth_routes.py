from fastapi import APIRouter, HTTPException, Depends
import traceback
from auth.auth_service import (
    register_user,
    verify_registration_otp,
    login_user,
    logout_user,
    send_login_otp,
)

from auth.auth_dependency import get_current_user
from db.database import get_item, get_all_items, get_user_loan_summary, get_user_profile_data
from services.loan_service import get_credit_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: dict):
    """
    Register user and send OTP
    """
    try:
        register_user(
            phone=payload.get("phone"),
            password=payload.get("password"),
            first_name=payload.get("first_name") or payload.get("firstName"),
            middle_name=payload.get("middle_name") or payload.get("middleName"),
            last_name=payload.get("last_name") or payload.get("lastName"),
            dob=payload.get("dob"),
        )
        return {"message": "OTP sent to phone"}
    except ValueError as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-otp")
def verify_otp(payload: dict):
    """
    Verify OTP and log user in
    """
    try:
        token = verify_registration_otp(
            phone=payload.get("phone"),
            otp_code=payload.get("otp") or payload.get("otp_code"),
        )
        return {"token": token}
    except ValueError as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-login-otp")
def send_login_otp_route(payload: dict):
    """
    Send OTP for login
    """
    try:
        send_login_otp(payload["phone"])
        return {"message": "OTP sent"}
    except ValueError as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(payload: dict):
    """
    Login existing user
    """
    try:
        result = login_user(
            phone=payload.get("phone"),
            password=payload.get("password"),
            otp=payload.get("otp"),
        )
        return result
    except ValueError as e:
        traceback.print_exc()
        # If OTP required, we return 400 so frontend knows to show OTP field
        # But if invalid credentials, we usually return 401
        # The service raises 'Invalid credentials' or 'OTP verification required'
        # We can distinguish messages or just return 400 for everything except auth failure?
        # Standard: 401 for auth failure.
        if str(e) == "Invalid credentials":
            raise HTTPException(status_code=401, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout")
def logout(payload: dict):
    """
    Logout user
    """
    logout_user(payload["token"])
    return {"message": "Logged out successfully"}


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    """Return live user profile info based on session token — single DB connection."""
    phone = current_user

    # Single connection fetches user + kyc + credit_score + loan summary
    profile = get_user_profile_data(phone)
    user = profile["user"]
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    kyc_data = profile["kyc"] or {}
    kyc_status = kyc_data.get("status") or "INCOMPLETE"
    kyc_verified = kyc_status == "APPROVED"

    # Calculate borrowing limit based on credit score
    borrowing_limit = 0
    if profile["credit_score"] is not None:
        try:
            borrowing_limit = get_credit_limit(phone)
        except:
            borrowing_limit = 50000  # Default fallback

    return {
        "firstName": user.get("first_name") or user.get("firstName") or "",
        "middleName": user.get("middle_name") or user.get("middleName"),
        "lastName": user.get("last_name") or user.get("lastName") or "",
        "phone": user.get("phone") or phone,
        "dob": user.get("dob"),
        "createdAt": user.get("created_at"),
        "kycVerified": kyc_verified,
        "kycStatus": kyc_status,
        "creditScore": profile["credit_score"],
        "activeRole": profile["active_role"],
        "totalLended": profile["total_lended"],
        "totalBorrowed": profile["total_borrowed"],
        "borrowingLimit": borrowing_limit,
    }
