from functools import lru_cache
from pathlib import Path
from typing import List
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def load_env_file() -> None:
    """Load backend/.env for local runs without overriding real environment variables."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

class Settings:
    app_name: str = "TrustVerify Backend API"
    api_v1_str: str = "/api/v1"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-this-in-production"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./trustverify.db"
    upload_dir: str = "./storage/uploads"
    certificate_dir: str = "./storage/certificates"
    max_upload_size_mb: int = 15
    ml_service_url: str = "http://localhost:9000"
    mock_external_services: bool = False
    default_certificate_validity_days: int = 730

    def __init__(self):
        load_env_file()

        # Load from environment variables
        self.app_name = os.getenv("APP_NAME", self.app_name)
        self.api_v1_str = os.getenv("API_V1_STR", self.api_v1_str)
        self.environment = os.getenv("ENVIRONMENT", self.environment)
        self.debug = os.getenv("DEBUG", str(self.debug)).lower() == "true"
        self.secret_key = os.getenv("SECRET_KEY", self.secret_key)
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", self.access_token_expire_minutes))
        self.database_url = os.getenv("DATABASE_URL", self.database_url)
        self.upload_dir = os.getenv("UPLOAD_DIR", self.upload_dir)
        self.certificate_dir = os.getenv("CERTIFICATE_DIR", self.certificate_dir)
        self.max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", self.max_upload_size_mb))
        self.ml_service_url = os.getenv("ML_SERVICE_URL", self.ml_service_url)
        self.mock_external_services = os.getenv("MOCK_EXTERNAL_SERVICES", str(self.mock_external_services)).lower() == "true"
        self.default_certificate_validity_days = int(os.getenv("DEFAULT_CERTIFICATE_VALIDITY_DAYS", self.default_certificate_validity_days))

        # Resolve relative SQLite paths against the backend project root so the app
        # uses one stable database file no matter which folder uvicorn starts from.
        if self.database_url.startswith("sqlite:///./"):
            backend_root = Path(__file__).resolve().parents[2]
            relative_path = self.database_url.removeprefix("sqlite:///./")
            self.database_url = f"sqlite:///{(backend_root / relative_path).as_posix()}"
        elif self.database_url.startswith(("postgres://", "postgresql://")):
            self.database_url = self._normalize_postgres_url(self.database_url)

    def _normalize_postgres_url(self, value: str) -> str:
        """Normalize Railway/Postgres URLs for SQLAlchemy with psycopg."""
        if value.startswith("postgres://"):
            value = "postgresql://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            value = "postgresql+psycopg://" + value.removeprefix("postgresql://")

        parsed = urlsplit(value)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if parsed.hostname and parsed.hostname.endswith(".up.railway.app"):
            query.setdefault("sslmode", "require")
        return urlunsplit(parsed._replace(query=urlencode(query)))

    @property
    def allowed_file_types_list(self) -> List[str]:
        value = os.getenv(
            "ALLOWED_FILE_TYPES_STR",
            "image/jpeg,image/png,image/webp,application/pdf,"
            "text/plain,"
            "audio/mpeg,audio/mp3,audio/wav,audio/x-wav,audio/flac,audio/x-flac,"
            "audio/mp4,audio/x-m4a,audio/ogg,application/ogg,"
            "video/mp4,video/webm,video/quicktime",
        )
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def backend_cors_origins_list(self) -> List[str]:
        value = os.getenv(
            "BACKEND_CORS_ORIGINS_STR",
            "http://localhost:5173,http://localhost:3000,"
            "https://digital-content-authenticity-mvp-frontend-production.up.railway.app",
        )
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def certificate_path(self) -> Path:
        return Path(self.certificate_dir)


def get_settings() -> Settings:
    return Settings()
