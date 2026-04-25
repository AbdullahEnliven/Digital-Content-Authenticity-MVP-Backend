from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.uploaded_content import UploadedContent
from app.models.user import User
from app.models.verification import Verification
from app.schemas.verification import HistoryItemOut

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryItemOut])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Verification)
        .where(Verification.user_id == current_user.id)
        .options(joinedload(Verification.content), joinedload(Verification.certificate))
        .order_by(Verification.created_at.desc())
    ).all()
    return [
        HistoryItemOut(
            verification_id=item.id,
            upload_id=item.content.id,
            filename=item.content.original_filename,
            mime_type=item.content.mime_type,
            created_at=item.created_at,
            final_trust_score=item.final_trust_score,
            trust_classification=item.trust_classification,
            verification_status=item.verification_status,
            has_certificate=bool(item.certificate),
        )
        for item in rows
    ]
