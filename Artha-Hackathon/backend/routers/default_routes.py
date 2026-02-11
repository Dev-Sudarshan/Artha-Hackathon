from fastapi import APIRouter, HTTPException
from services.default_service import check_and_mark_defaults

router = APIRouter(prefix="/defaults", tags=["defaults"])


@router.post("/check")
def run_default_check():
    """
    Manually trigger loan default check (admin / cron simulation)
    """
    try:
        return check_and_mark_defaults()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
