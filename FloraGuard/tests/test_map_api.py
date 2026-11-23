"""Map API tests."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Report
from main import app
from fastapi.testclient import TestClient

_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(bind=_engine)
_SessionLocal = sessionmaker(bind=_engine)


def _override_db():
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db
client = TestClient(app)

import pytest
from datetime import datetime, timezone

@pytest.fixture(autouse=True)
def _ov():
    app.dependency_overrides[get_db] = _override_db
    yield
    app.dependency_overrides.pop(get_db, None)


def test_map_reports():
    db = _SessionLocal()
    db.add(Report(input_channel="smartphone", problem_type="mildew", severity="mild", area="A", created_at=datetime.now(timezone.utc)))
    db.commit()
    db.close()
    r = client.get("/api/map/reports")
    assert r.status_code == 200
    body = r.json()
    assert "areas" in body
    assert body["areas"][0]["area"] == "A"
