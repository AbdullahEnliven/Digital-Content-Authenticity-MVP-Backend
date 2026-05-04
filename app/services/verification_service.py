from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.uploaded_content import UploadedContent
from app.models.verification import AIAnalysisResult, Certificate, MetadataResult, TrustScore, Verification, VerificationLog
from app.services.certificate_service import build_certificate_path, generate_certificate_pdf, new_verification_code
from app.services.metadata_service import extract_metadata
from app.services.ml_client import analyze_file
from app.services.trust_score_service import calculate_trust_score


async def run_verification(db: Session, upload: UploadedContent, include_identity: bool, auto_issue_certificate: bool) -> Verification:
    verification = Verification(
        user_id=upload.user_id,
        content_id=upload.id,
        status="processing",
        share_token=uuid4().hex,
        file_integrity_valid=True,
    )
    db.add(verification)
    db.flush()

    db.add(VerificationLog(verification_id=verification.id, event="verification_started", details="Verification initiated"))

    meta_payload = extract_metadata(upload.stored_path, upload.mime_type)
    metadata_result = MetadataResult(content_id=upload.id, **meta_payload)
    db.add(metadata_result)
    db.flush()

    # Call the actual ML service for AI analysis
    ai_payload = await analyze_file(upload.stored_path, upload.mime_type)
    # Filter ai_payload to only include fields expected by AIAnalysisResult
    ai_result_fields = {"ai_probability", "confidence_score", "model_name", "model_version"}
    filtered_ai_payload = {k: v for k, v in ai_payload.items() if k in ai_result_fields}
    ai_result = AIAnalysisResult(verification_id=verification.id, **filtered_ai_payload)
    db.add(ai_result)

    trust_payload = calculate_trust_score(
        ai_probability=ai_payload["ai_probability"],
        metadata_score=meta_payload["consistency_score"],
        identity_verified=include_identity,
        file_integrity_valid=True,
    )
    trust_result = TrustScore(verification_id=verification.id, **{k: trust_payload[k] for k in ["score", "trust_level", "reasoning", "rule_version"]})
    db.add(trust_result)

    verification.status = "completed"
    verification.final_trust_score = trust_payload["score"]
    verification.trust_classification = trust_payload["trust_level"]
    verification.verification_status = trust_payload["verification_status"]
    verification.reasoning_summary = trust_payload["reasoning"]
    verification.updated_at = datetime.now(timezone.utc)
    db.add(VerificationLog(verification_id=verification.id, event="verification_completed", details=trust_payload["reasoning"]))

    if auto_issue_certificate or trust_payload["score"] >= 50:
        verification_code = new_verification_code()
        pdf_path = build_certificate_path(verification.id)
        generate_certificate_pdf(
            pdf_path,
            {
                "verification_id": verification.id,
                "filename": upload.original_filename,
                "trust_score": trust_payload["score"],
                "trust_level": trust_payload["trust_level"],
                "ai_probability": round(ai_payload["ai_probability"] * 100, 2),
                "issued_at": datetime.now(timezone.utc).isoformat(),
                "reasoning": trust_payload["reasoning"],
            },
        )
        cert = Certificate(
            verification_id=verification.id,
            verification_code=verification_code,
            file_path=str(pdf_path),
            shareable_link=f"/api/v1/public/verifications/{verification.share_token}",
        )
        db.add(cert)

    db.commit()
    db.refresh(verification)
    return verification
