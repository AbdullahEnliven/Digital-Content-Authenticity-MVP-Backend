from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.verification import Verification

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/verifications/{share_token}")
def public_verification(share_token: str):
    db = SessionLocal()
    try:
        verification = db.scalar(
            select(Verification)
            .where(Verification.share_token == share_token)
            .options(joinedload(Verification.content), joinedload(Verification.ai_analysis_result), joinedload(Verification.certificate))
        )
        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")
        return {
            "verification_id": verification.id,
            "filename": verification.content.original_filename,
            "trust_score": verification.final_trust_score,
            "trust_level": verification.trust_classification,
            "verification_status": verification.verification_status,
            "ai_probability": round((verification.ai_analysis_result.ai_probability if verification.ai_analysis_result else 0) * 100, 2),
            "shareable_link": verification.certificate.shareable_link if verification.certificate else None,
        }
    finally:
        db.close()
