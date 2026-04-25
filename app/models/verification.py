from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MetadataResult(Base):
    __tablename__ = "metadata_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("uploaded_contents.id"), unique=True, nullable=False)
    file_format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    creation_timestamp: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    compression_indicators: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.5)
    raw_metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    content = relationship("UploadedContent", back_populates="metadata_result")


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("uploaded_contents.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    final_trust_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    trust_classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reasoning_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_integrity_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="verifications")
    content = relationship("UploadedContent", back_populates="verifications")
    ai_analysis_result = relationship("AIAnalysisResult", back_populates="verification", uselist=False, cascade="all, delete-orphan")
    trust_score_result = relationship("TrustScore", back_populates="verification", uselist=False, cascade="all, delete-orphan")
    certificate = relationship("Certificate", back_populates="verification", uselist=False, cascade="all, delete-orphan")
    logs = relationship("VerificationLog", back_populates="verification", cascade="all, delete-orphan")


class AIAnalysisResult(Base):
    __tablename__ = "ai_analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    verification_id: Mapped[int] = mapped_column(ForeignKey("verifications.id"), unique=True, nullable=False)
    ai_probability: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    verification = relationship("Verification", back_populates="ai_analysis_result")


class TrustScore(Base):
    __tablename__ = "trust_scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    verification_id: Mapped[int] = mapped_column(ForeignKey("verifications.id"), unique=True, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    trust_level: Mapped[str] = mapped_column(String(50), nullable=False)
    reasoning: Mapped[str] = mapped_column(String(1000), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    verification = relationship("Verification", back_populates="trust_score_result")


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    verification_id: Mapped[int] = mapped_column(ForeignKey("verifications.id"), unique=True, nullable=False)
    verification_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    shareable_link: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    verification = relationship("Verification", back_populates="certificate")


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    verification_id: Mapped[int] = mapped_column(ForeignKey("verifications.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), default="INFO")
    event: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    verification = relationship("Verification", back_populates="logs")
