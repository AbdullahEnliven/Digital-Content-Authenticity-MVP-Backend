from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.models.verification import Verification
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserOut, UserUpdate, UserStats
from app.services.credit_service import DAILY_CREDIT_LIMIT, ensure_daily_credits

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return user


def _build_token_response(user: User) -> TokenResponse:
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=user)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        daily_credit_limit=DAILY_CREDIT_LIMIT,
        credits_remaining=DAILY_CREDIT_LIMIT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login_swagger(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = _authenticate_user(db, username, password)
    ensure_daily_credits(user, db, commit=True)
    return _build_token_response(user)


@router.post("/login-json", response_model=TokenResponse)
def login_json(payload: UserLogin, db: Session = Depends(get_db)):
    user = _authenticate_user(db, payload.email, payload.password)
    ensure_daily_credits(user, db, commit=True)
    return _build_token_response(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_daily_credits(current_user, db, commit=True)
    return current_user


@router.put("/me", response_model=UserOut)
def update_profile(payload: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.full_name = payload.full_name
    current_user.organization = payload.organization
    current_user.job_role = payload.job_role
    current_user.bio = payload.bio
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/stats", response_model=UserStats)
def get_user_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import func
    from app.models.verification import Verification, Certificate

    # Get all user's verifications
    verifications = db.query(Verification).filter(Verification.user_id == current_user.id).all()
    
    # Calculate statistics
    total_verifications = len(verifications)
    verified_authentic = sum(1 for v in verifications if v.trust_classification == 'Verified')
    suspicious = sum(1 for v in verifications if v.trust_classification == 'Suspicious')
    certificates_issued = sum(1 for v in verifications if v.certificate is not None)
    
    # For AI Detected, count items with high AI probability (trust_classification = 'Suspicious' or related)
    ai_detected = suspicious

    return UserStats(
        total_verifications=total_verifications,
        verified_authentic=verified_authentic,
        ai_detected=ai_detected,
        certificates_issued=certificates_issued
    )
