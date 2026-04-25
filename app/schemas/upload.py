from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    id: int
    original_filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    created_at: datetime


class UploadedContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    stored_path: str
    mime_type: str
    file_size: int
    sha256_hash: str
    upload_status: str
    created_at: datetime
