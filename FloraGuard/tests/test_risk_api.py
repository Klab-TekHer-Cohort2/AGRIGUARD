import pytest
"""API tests for risk assessment endpoint."""

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


def _seed_reports(n=10):
    db = _SessionLocal()
    for i in range(n):
        db.add(Report(input_channel="smartphone", problem_type="mildew", severity="severe", area="A",
                      created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc)))
    db.commit()
    db.close()


def test_risk_with_reports():
    _seed_reports(10)
    resp = client.get("/api/risk", params={"area": "A", "problem_type": "mildew"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert "reasons" in body


def test_risk_weather_unavailable():
    resp = client.get("/api/risk", params={"area": "A", "problem_type": "mildew"})
    assert resp.status_code == 200
    assert resp.json()["weather_available"] is False


def test_risk_invalid_window():
    resp = client.get("/api/risk", params={"window_hours": "abc"})
    assert resp.status_code == 422

@pytest.fixture(autouse=True)
def _override_db_fixture():
    app.dependency_overrides[get_db] = _override_db
    yield
    app.dependency_overrides.pop(get_db, None)
