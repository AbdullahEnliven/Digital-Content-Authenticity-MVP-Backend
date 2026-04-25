from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal

router = APIRouter(tags=["system"])


@router.get("/health")
def health_check():
    db: Session = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        database = "reachable"
    finally:
        db.close()
    return {"status": "ok", "database": database}
