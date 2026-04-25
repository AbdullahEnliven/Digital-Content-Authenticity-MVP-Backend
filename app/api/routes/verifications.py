from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.uploaded_content import UploadedContent
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import VerificationOut, VerificationStartRequest
from app.services.credit_service import charge_verification_credits
from app.services.verification_service import run_verification

router = APIRouter(prefix="/verifications", tags=["verifications"])


def serialize_verification(verification: Verification) -> VerificationOut:
    return VerificationOut(
        id=verification.id,
        status=verification.status,
        final_trust_score=verification.final_trust_score,
        trust_classification=verification.trust_classification,
        verification_status=verification.verification_status,
        reasoning_summary=verification.reasoning_summary,
        share_token=verification.share_token,
        created_at=verification.created_at,
        updated_at=verification.updated_at,
        content={
            "id": verification.content.id,
            "filename": verification.content.original_filename,
            "mime_type": verification.content.mime_type,
            "sha256_hash": verification.content.sha256_hash,
            "file_size": verification.content.file_size,
        },
        metadata=verification.content.metadata_result,
        ai_analysis=verification.ai_analysis_result,
        trust_score=verification.trust_score_result,
        certificate=verification.certificate,
    )


@router.post("/{upload_id}/start", response_model=VerificationOut)
async def start_verification(
    upload_id: int,
    payload: VerificationStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.scalar(select(UploadedContent).where(UploadedContent.id == upload_id, UploadedContent.user_id == current_user.id))
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    charge_verification_credits(current_user, db, upload.mime_type)
    try:
        verification = await run_verification(db, upload, payload.include_identity, payload.auto_issue_certificate)
    except httpx.HTTPStatusError as exc:
        detail = "ML service failed during verification"
        try:
            ml_detail = exc.response.json().get("detail")
            if ml_detail:
                detail = f"{detail}: {ml_detail}"
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
    verification = db.scalar(
        select(Verification)
        .where(Verification.id == verification.id)
        .options(
            joinedload(Verification.content).joinedload(UploadedContent.metadata_result),
            joinedload(Verification.ai_analysis_result),
            joinedload(Verification.trust_score_result),
            joinedload(Verification.certificate),
        )
    )
    return serialize_verification(verification)


@router.get("/{verification_id}", response_model=VerificationOut)
def get_verification(verification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    verification = db.scalar(
        select(Verification)
        .where(Verification.id == verification_id, Verification.user_id == current_user.id)
        .options(
            joinedload(Verification.content).joinedload(UploadedContent.metadata_result),
            joinedload(Verification.ai_analysis_result),
            joinedload(Verification.trust_score_result),
            joinedload(Verification.certificate),
        )
    )
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    return serialize_verification(verification)


@router.get("/{verification_id}/status")
def get_verification_status(verification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get the current progress status of a verification"""
    verification = db.scalar(
        select(Verification).where(
            Verification.id == verification_id, 
            Verification.user_id == current_user.id
        ).options(
            joinedload(Verification.content).joinedload(UploadedContent.metadata_result),
            joinedload(Verification.ai_analysis_result),
            joinedload(Verification.trust_score_result),
            joinedload(Verification.certificate),
        )
    )
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    
    # Get metadata from content relationship
    has_metadata = verification.content.metadata_result is not None if verification.content else False
    
    # Calculate progress
    if verification.status == 'completed':
        progress = 100
    elif verification.status == 'processing':
        # Show 42% during processing to indicate we're running AI detection
        progress = 42
    else:
        # Default for 'pending' state
        progress = 18
    
    return {
        "status": verification.status,
        "progress": progress,
        "has_metadata": has_metadata,
        "has_ai_analysis": bool(verification.ai_analysis_result),
        "has_trust_score": bool(verification.trust_score_result),
        "has_certificate": bool(verification.certificate),
    }
