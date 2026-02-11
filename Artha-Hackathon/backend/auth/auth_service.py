from datetime import datetime, timedelta
from auth.password_utils import hash_password, verify_password
from auth.otp_service import send_otp, verify_otp

from db.database import get_item, put_item, delete_item

def register_user(
    phone: str,
    password: str,
    first_name: str,
    middle_name: str | None,
    last_name: str,
    dob: str
) -> None:
    """
    Create a new user and send OTP
    """
    existing = get_item("users", phone)
    if existing and existing.get("is_verified"):
        raise ValueError("User already exists and is verified. Please login.")

    new_user = {
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "dob": dob,
        "phone": phone,
        "password_hash": hash_password(password),
        "is_verified": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    put_item("users", phone, new_user)

    send_otp(phone)


def verify_registration_otp(phone: str, otp_code: str) -> str:
    """
    Verify OTP and log user in
    """
    user = get_item("users", phone)
    if not user:
        raise ValueError("Verification failed: User record not found")

    if not verify_otp(phone, otp_code):
        raise ValueError("Invalid verification code (OTP) entered")

    user["is_verified"] = True
    put_item("users", phone, user) 
    return create_session(phone)


def send_login_otp(phone: str) -> None:
    """
    Send OTP for login (only if user exists)
    """
    if not get_item("users", phone):
        raise ValueError("User not found")
    send_otp(phone)


def login_user(phone: str, password: str, otp: str = None) -> dict:
    """
    Login existing user with optional OTP
    """
    user = get_item("users", phone)
    if not user:
        raise ValueError("User not found")

    if not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid credentials")

    # If OTP is provided, verify it
    if otp:
        if not verify_otp(phone, otp):
             raise ValueError("Invalid OTP")
        # Mark as verified if not already
        if not user["is_verified"]:
             user["is_verified"] = True
             put_item("users", phone, user)
    else:
        if not user["is_verified"]:
            send_otp(phone)
            raise ValueError("OTP verification required")

    # Check real KYC status
    kyc_data = get_item("kyc", phone)
    kyc_verified = (kyc_data.get("status") == "APPROVED") if kyc_data else False

    token = create_session(phone)
    return {
        "token": token,
        "user": {
             "firstName": user["first_name"],
             "middleName": user["middle_name"],
             "lastName": user["last_name"],
             "phone": user["phone"],
             "dob": user["dob"],
             "kycVerified": kyc_verified
        }
    }


def create_session(phone: str) -> str:
    """
    Create login session / token
    """
    token = f"session-{phone}-{datetime.utcnow().timestamp()}"
    session_data = {
        "phone": phone,
        "expires_at": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
    }
    put_item("sessions", token, session_data)
    return token


def logout_user(token: str) -> None:
    """
    Logout user
    """
    delete_item("sessions", token)
