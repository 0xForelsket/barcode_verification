import pytest
import os
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Set test backup token BEFORE importing main (which reads env vars at import time)
os.environ["BACKUP_TOKEN"] = "test-backup-token-12345"

from main import app
from database import get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # Initialize ShiftStats as lifespan does
        from datetime import datetime
        from models import ShiftStats

        today = datetime.now().date()
        stats = ShiftStats(date=today)
        session.add(stats)
        session.commit()

        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
