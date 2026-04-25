from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    organization: Mapped[str] = mapped_column(String(255), nullable=True)
    job_role: Mapped[str] = mapped_column(String(255), nullable=True)
    bio: Mapped[str] = mapped_column(String(1000), nullable=True)
    daily_credit_limit: Mapped[int] = mapped_column(Integer, default=250)
    credits_remaining: Mapped[int] = mapped_column(Integer, default=250)
    credits_reset_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    uploaded_contents = relationship("UploadedContent", back_populates="user", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="user", cascade="all, delete-orphan")
