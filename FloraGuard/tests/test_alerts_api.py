import pytest
"""API tests for alerts endpoint."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Alert
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


def _seed_alerts():
    db = _SessionLocal()
    for i in range(3):
        db.add(Alert(problem_type="mildew", area="A", risk_level="HIGH", risk_score=70.0, delivery_status="skipped"))
    db.add(Alert(problem_type="rust", area="B", risk_level="HIGH", risk_score=65.0, delivery_status="skipped"))
    db.commit()
    db.close()


def test_list_alerts():
    _seed_alerts()
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    assert resp.json()["total"] == 4


def test_filter_alerts():
    resp = client.get("/api/alerts", params={"area": "A"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


def test_paginate_alerts():
    resp = client.get("/api/alerts", params={"skip": 0, "limit": 2})
    assert resp.status_code == 200
    assert len(resp.json()["alerts"]) == 2

@pytest.fixture(autouse=True)
def _override_db_fixture():
    app.dependency_overrides[get_db] = _override_db
    yield
    app.dependency_overrides.pop(get_db, None)
