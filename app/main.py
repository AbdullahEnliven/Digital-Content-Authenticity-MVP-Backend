from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, certificates, history, public, system, uploads, verifications
from app.core.config import get_settings
from app.core.database import Base, engine
from app.services.file_storage import ensure_storage_dirs

settings = get_settings()
Base.metadata.create_all(bind=engine)
ensure_storage_dirs()
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


app.include_router(system.router)
app.include_router(auth.router, prefix=settings.api_v1_str)
app.include_router(uploads.router, prefix=settings.api_v1_str)
app.include_router(verifications.router, prefix=settings.api_v1_str)
app.include_router(history.router, prefix=settings.api_v1_str)
app.include_router(certificates.router, prefix=settings.api_v1_str)
app.include_router(public.router, prefix=settings.api_v1_str)
