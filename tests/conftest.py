import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["CERTIFICATE_DIR"] = "./test_certificates"
os.environ["MOCK_EXTERNAL_SERVICES"] = "true"

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_and_teardown():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Path("/tmp/trustverify_storage/uploads").mkdir(parents=True, exist_ok=True)
    Path("/tmp/trustverify_storage/certificates").mkdir(parents=True, exist_ok=True)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    shutil.rmtree("/tmp/trustverify_storage", ignore_errors=True)
    if Path("/tmp/trustverify_test.db").exists():
        Path("/tmp/trustverify_test.db").unlink()


@pytest.fixture
def client():
    return TestClient(app)
