def calculate_trust_score(ai_probability: float, metadata_score: float, identity_verified: bool, file_integrity_valid: bool) -> dict:
    ai_component = max(0.0, (1.0 - ai_probability) * 55)
    metadata_component = max(0.0, min(metadata_score, 1.0)) * 20
    identity_component = 15 if identity_verified else 7
    integrity_component = 10 if file_integrity_valid else 0
    score = round(ai_component + metadata_component + identity_component + integrity_component, 2)

    if score >= 80:
        trust_level = "Verified"
        verification_status = "verified"
    elif score >= 50:
        trust_level = "Suspicious"
        verification_status = "review"
    else:
        trust_level = "Low Trust"
        verification_status = "low_trust"

    reasons = [
        f"AI-generation probability: {round(ai_probability * 100, 2)}%.",
        f"Metadata consistency score: {round(metadata_score * 100, 2)}%.",
        f"Identity verification: {'passed' if identity_verified else 'not provided'}.",
        f"File integrity: {'valid' if file_integrity_valid else 'invalid'}.",
    ]
    return {
        "score": score,
        "trust_level": trust_level,
        "verification_status": verification_status,
        "reasoning": " ".join(reasons),
        "rule_version": "1.0.0",
    }
