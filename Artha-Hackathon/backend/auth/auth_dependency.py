from fastapi import Header, HTTPException
from db.database import get_item


def get_current_user(authorization: str = Header(...)):
    """
    Minimal auth dependency.
    Expects header: Authorization: Bearer <token>
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.split(" ")[1]

    session = get_item("sessions", token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return session["phone"]  # or user_id if you map it
