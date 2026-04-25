from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.uploaded_content import UploadedContent
from app.models.user import User
from app.schemas.upload import UploadResponse
from app.services.file_storage import build_upload_path, save_upload_file
from app.utils.hash import sha256_file

settings = get_settings()
router = APIRouter(prefix="/uploads", tags=["uploads"])

MIME_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
}


def _normalized_content_type(filename: str, content_type: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    inferred = MIME_BY_EXTENSION.get(suffix)
    if inferred and (not content_type or content_type == "application/octet-stream"):
        return inferred
    return content_type or inferred or "application/octet-stream"


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_content(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filename = file.filename or "upload.bin"
    content_type = _normalized_content_type(filename, file.content_type)
    if content_type not in settings.allowed_file_types_list:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    target_path = build_upload_path(current_user.id, filename)
    save_upload_file(file, target_path)
    size = Path(target_path).stat().st_size
    if size > max_bytes:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.max_upload_size_mb} MB")

    upload = UploadedContent(
        user_id=current_user.id,
        original_filename=filename,
        stored_filename=target_path.name,
        stored_path=str(target_path),
        mime_type=content_type,
        file_size=size,
        sha256_hash=sha256_file(target_path),
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return UploadResponse(id=upload.id, original_filename=upload.original_filename, mime_type=upload.mime_type, file_size=upload.file_size, sha256_hash=upload.sha256_hash, created_at=upload.created_at)
