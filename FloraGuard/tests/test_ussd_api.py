"""USSD API tests."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
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

@pytest.fixture(autouse=True)
def _ov():
    app.dependency_overrides[get_db] = _override_db
    yield
    app.dependency_overrides.pop(get_db, None)


def test_ussd_flow():
    r = client.post("/api/ussd", json={"session_id": "s1", "phone_number": "0780000000", "text": "1", "action": "menu"})
    assert r.status_code == 200
    r = client.post("/api/ussd", json={"session_id": "s1", "phone_number": "0780000000", "text": "1*1*1*1", "action": "submit"})
    assert r.status_code == 200
    body = r.json()
    assert body["is_end"] is True
    assert body.get("report_id") is not None


def test_ussd_invalid():
    r = client.post("/api/ussd", json={"session_id": "s2", "phone_number": "0780000000", "text": "9*9*9*1", "action": "submit"})
    assert r.status_code == 200
    assert r.json()["is_end"] is True
