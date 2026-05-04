from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification
from app.services.certificate_service import generate_certificate_pdf

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("/{verification_id}/metadata")
def get_certificate_metadata(verification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = db.scalar(
        select(Verification)
        .where(Verification.id == verification_id, Verification.user_id == current_user.id)
        .options(joinedload(Verification.certificate), joinedload(Verification.content), joinedload(Verification.ai_analysis_result))
    )
    if not verification or not verification.certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {
        "verification_id": verification.id,
        "file_path": verification.certificate.file_path,
        "created_at": verification.certificate.created_at,
        "filename": verification.content.original_filename,
        "trust_score": verification.final_trust_score,
        "trust_level": verification.trust_classification,
        "ai_probability": round((verification.ai_analysis_result.ai_probability if verification.ai_analysis_result else 0) * 100, 2),
    }


@router.get("/{verification_id}/download")
def download_certificate(verification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = db.scalar(
        select(Verification)
        .where(Verification.id == verification_id, Verification.user_id == current_user.id)
        .options(joinedload(Verification.certificate), joinedload(Verification.content), joinedload(Verification.ai_analysis_result))
    )
    if not verification or not verification.certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    path = Path(verification.certificate.file_path)
    generate_certificate_pdf(
        path,
        {
            "verification_id": verification.id,
            "filename": verification.content.original_filename if verification.content else "-",
            "trust_score": verification.final_trust_score or 0,
            "trust_level": verification.trust_classification or "-",
            "ai_probability": round((verification.ai_analysis_result.ai_probability if verification.ai_analysis_result else 0) * 100, 2),
            "issued_at": verification.certificate.created_at.isoformat(),
            "reasoning": verification.reasoning_summary or "Verification completed successfully.",
        },
    )
    if not path.exists():
        raise HTTPException(status_code=404, detail="Certificate file missing")
    return FileResponse(path=path, media_type="application/pdf", filename=path.name)
