import random
from datetime import datetime, timedelta

from db.database import get_item, put_item, delete_item

OTP_EXPIRY_MINUTES = 5


def generate_otp() -> str:
    """
    Generate a 6-digit OTP (Static for Dev)
    """
    return "123456"


def send_otp(phone: str) -> None:
    """
    Generate and send OTP to user's phone
    """
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    data = {
        "otp": otp,
        "expires_at": expires_at.isoformat(),
        "verified": False,
    }
    put_item("otps", phone, data)

    # SMS gateway integration goes here (mocked)
    print(f"[OTP SERVICE] OTP for {phone}: {otp}")


def verify_otp(phone: str, otp_code: str) -> bool:
    """
    Verify OTP for a phone number
    """
    record = get_item("otps", phone)
    print(f"[OTP DEBUG] Verifying for {phone}. Record: {record}, Input: {otp_code}")
    
    if not record:
        print("[OTP DEBUG] No record found")
        return False

    # Comparison
    if record["otp"] == otp_code:
        record["verified"] = True
        put_item("otps", phone, record)
        return True
    
    print(f"[OTP DEBUG] Mismatch: {record['otp']} vs {otp_code}")
    return False
