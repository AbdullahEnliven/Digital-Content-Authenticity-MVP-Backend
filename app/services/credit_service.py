from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User

DAILY_CREDIT_LIMIT = 250
CREDIT_COSTS = {
    "text": 20,
    "audio": 30,
    "image": 50,
    "video": 70,
}


def credit_type_for_mime(mime_type: str) -> str:
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("audio/") or mime_type in {"application/ogg"}:
        return "audio"
    if mime_type.startswith("video/"):
        return "video"
    return "text"


def credit_cost_for_mime(mime_type: str) -> int:
    return CREDIT_COSTS[credit_type_for_mime(mime_type)]


def ensure_daily_credits(user: User, db: Session, commit: bool = False) -> User:
    today = date.today()
    if user.daily_credit_limit is None:
        user.daily_credit_limit = DAILY_CREDIT_LIMIT
    if user.credits_reset_date != today:
        user.daily_credit_limit = DAILY_CREDIT_LIMIT
        user.credits_remaining = DAILY_CREDIT_LIMIT
        user.credits_reset_date = today
        db.add(user)
        if commit:
            db.commit()
            db.refresh(user)
    return user


def charge_verification_credits(user: User, db: Session, mime_type: str) -> int:
    ensure_daily_credits(user, db)
    cost = credit_cost_for_mime(mime_type)
    if user.credits_remaining < cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Not enough credits. This verification needs {cost} credits, but you have {user.credits_remaining} remaining today.",
        )
    user.credits_remaining -= cost
    db.add(user)
    db.commit()
    db.refresh(user)
    return cost
