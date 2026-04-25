import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings

settings = get_settings()


def ensure_storage_dirs() -> None:
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.certificate_path.mkdir(parents=True, exist_ok=True)


def build_upload_path(user_id: int, filename: str) -> Path:
    now = datetime.now(timezone.utc)
    ext = Path(filename).suffix.lower()
    relative = Path(str(now.year), f"{now.month:02d}", f"{now.day:02d}", f"user_{user_id}", f"content_{uuid4().hex}")
    target_dir = settings.upload_path / relative
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"original{ext}"


def save_upload_file(upload_file: UploadFile, target_path: Path) -> None:
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
