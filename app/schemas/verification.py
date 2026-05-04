from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class VerificationStartRequest(BaseModel):
    include_identity: bool = True
    auto_issue_certificate: bool = False


class MetadataResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_format: str | None = None
    creation_timestamp: str | None = None
    device_info: str | None = None
    compression_indicators: str | None = None
    consistency_score: float | None = None
    raw_metadata_json: dict[str, Any] | None = None


class AIAnalysisResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ai_probability: float
    confidence_score: float
    model_name: str
    model_version: str


class TrustScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: float
    trust_level: str
    reasoning: str
    rule_version: str


class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_path: str
    created_at: datetime


class VerificationOut(BaseModel):
    id: int
    status: str
    final_trust_score: float | None = None
    trust_classification: str | None = None
    verification_status: str | None = None
    reasoning_summary: str | None = None
    share_token: str | None = None
    created_at: datetime
    updated_at: datetime
    content: dict[str, Any]
    metadata: MetadataResultOut | None = None
    ai_analysis: AIAnalysisResultOut | None = None
    trust_score: TrustScoreOut | None = None
    certificate: CertificateOut | None = None


class HistoryItemOut(BaseModel):
    verification_id: int
    upload_id: int
    filename: str
    mime_type: str
    created_at: datetime
    final_trust_score: float | None = None
    trust_classification: str | None = None
    verification_status: str | None = None
    has_certificate: bool
