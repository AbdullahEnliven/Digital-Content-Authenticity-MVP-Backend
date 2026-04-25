from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UploadedContent(Base):
    __tablename__ = "uploaded_contents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    upload_status: Mapped[str] = mapped_column(String(50), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploaded_contents")
    metadata_result = relationship("MetadataResult", back_populates="content", uselist=False, cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="content", cascade="all, delete-orphan")
