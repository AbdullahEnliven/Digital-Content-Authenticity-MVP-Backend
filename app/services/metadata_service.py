from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader


def extract_metadata(file_path: str, mime_type: str) -> dict:
    path = Path(file_path)
    result = {
        "file_format": path.suffix.lower().replace('.', ''),
        "creation_timestamp": None,
        "device_info": None,
        "compression_indicators": "normal",
        "consistency_score": 0.7,
        "raw_metadata_json": {},
    }

    if mime_type.startswith("image/"):
        try:
            with Image.open(path) as img:
                exif = img.getexif() or {}
                result["raw_metadata_json"] = {
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format,
                    "exif_keys": [str(k) for k in exif.keys()],
                }
                result["device_info"] = str(exif.get(272) or exif.get(271) or "Unknown device")
                result["creation_timestamp"] = str(exif.get(306) or exif.get(36867) or "Unavailable")
                result["consistency_score"] = 0.85 if exif else 0.65
                result["compression_indicators"] = "normal" if img.format in {"JPEG", "PNG", "WEBP"} else "review"
        except UnidentifiedImageError:
            result["consistency_score"] = 0.4
            result["compression_indicators"] = "unsupported-image"
    elif mime_type == "application/pdf":
        reader = PdfReader(path)
        meta = reader.metadata or {}
        result["raw_metadata_json"] = {
            "pages": len(reader.pages),
            "title": str(meta.get('/Title', '')),
            "producer": str(meta.get('/Producer', '')),
            "creator": str(meta.get('/Creator', '')),
        }
        result["device_info"] = str(meta.get('/Producer', 'PDF document'))
        result["creation_timestamp"] = str(meta.get('/CreationDate', 'Unavailable'))
        result["consistency_score"] = 0.78 if meta else 0.6
        result["compression_indicators"] = "pdf-standard"
    elif mime_type.startswith("audio/") or mime_type.startswith("video/") or mime_type in {"application/ogg"}:
        media_kind = "Video" if mime_type.startswith("video/") else "Audio"
        result["raw_metadata_json"] = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
        result["device_info"] = f"{media_kind} file"
        result["creation_timestamp"] = "Unavailable"
        result["consistency_score"] = 0.72
        result["compression_indicators"] = f"{media_kind.lower()}-standard"
    elif mime_type == "text/plain":
        text = path.read_text(encoding="utf-8", errors="replace")
        result["raw_metadata_json"] = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "characters": len(text),
            "lines": len(text.splitlines()) or 1,
        }
        result["device_info"] = "Plain text file"
        result["creation_timestamp"] = "Unavailable"
        result["consistency_score"] = 0.76 if text.strip() else 0.2
        result["compression_indicators"] = "text-standard"
    return result
