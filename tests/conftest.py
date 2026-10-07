import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

@pytest.fixture()
def client():
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_file.close()

    test_engine = create_engine(
        f"sqlite:///{db_file.name}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        bind=test_engine, autocommit=False, autoflush=False
    )
    import app.services.job_processor as job_processor
    original_session_local = job_processor.SessionLocal
    job_processor.SessionLocal = TestingSessionLocal
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    job_processor.SessionLocal = original_session_local
    test_engine.dispose()
    os.unlink(db_file.name)
