import hashlib
from pathlib import Path

import httpx

from app.core.config import get_settings

settings = get_settings()


def _is_audio_mime(mime_type: str) -> bool:
    return mime_type.startswith("audio/") or mime_type in {"application/ogg"}


def _is_text_mime(mime_type: str) -> bool:
    return mime_type == "text/plain"


def _mock_response(file_path: str, mime_type: str) -> dict:
    digest = hashlib.sha256(Path(file_path).read_bytes()).hexdigest()
    sample = int(digest[:8], 16) / 0xFFFFFFFF
    ai_probability = round(min(max(sample, 0.02), 0.98), 4)
    if _is_text_mime(mime_type):
        model_name = "mock-text-auth-detector"
    elif _is_audio_mime(mime_type):
        model_name = "mock-voice-auth-detector"
    else:
        model_name = "mock-image-detector"
    return {
        "ai_probability": ai_probability,
        "confidence_score": round(0.70 + abs(0.5 - ai_probability) * 0.6, 4),
        "model_name": model_name,
        "model_version": "local-dev",
    }


def _normalize_voice_auth_response(payload: dict) -> dict:
    probabilities = payload.get("class_probabilities") or {}
    ai_probability = float(probabilities.get("ai", 1.0 if payload.get("predicted_label") == "ai" else 0.0))
    return {
        "ai_probability": round(ai_probability, 6),
        "confidence_score": round(float(payload.get("confidence", max(probabilities.values(), default=ai_probability))), 6),
        "model_name": "speechbrain-ecapa-voice-auth",
        "model_version": "1.0.0",
    }


def _normalize_text_auth_response(payload: dict) -> dict:
    probabilities = payload.get("class_probabilities") or {}
    ai_probability = float(probabilities.get("ai", 1.0 if payload.get("predicted_label") == "ai" else 0.0))
    return {
        "ai_probability": round(ai_probability, 6),
        "confidence_score": round(float(payload.get("confidence", max(probabilities.values(), default=ai_probability))), 6),
        "model_name": "minilm-text-auth",
        "model_version": "1.0.0",
    }


async def analyze_file(file_path: str, mime_type: str) -> dict:
    if settings.mock_external_services or mime_type == "application/pdf":
        return _mock_response(file_path, mime_type)

    async with httpx.AsyncClient(timeout=120) as client:
        if _is_text_mime(mime_type):
            text = Path(file_path).read_text(encoding="utf-8", errors="replace")
            response = await client.post(
                f"{settings.ml_service_url}/predict/text-auth",
                json={"text": text},
            )
            response.raise_for_status()
            return _normalize_text_auth_response(response.json())

        with open(file_path, "rb") as handle:
            files = {"file": (Path(file_path).name, handle, mime_type)}
            endpoint = "/predict/voice-auth" if _is_audio_mime(mime_type) else "/predict"
            response = await client.post(f"{settings.ml_service_url}{endpoint}", files=files)
            response.raise_for_status()
            payload = response.json()
            return _normalize_voice_auth_response(payload) if _is_audio_mime(mime_type) else payload
