import pytest
"""API tests for report endpoints."""

from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Report  # noqa
from main import app


_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


def test_create_report_json_form():
    resp = client.post("/api/reports", data={
        "input_channel": "ussd",
        "problem_type": "rust",
        "severity": "moderate",
        "area": "A",
    })
    assert resp.status_code == 201
    assert resp.json()["input_channel"] == "ussd"


def test_create_smartphone_with_image():
    files = {"upload_file": ("img.jpg", BytesIO(b"\xff\xd8\xff"), "image/jpeg")}
    data = {"input_channel": "smartphone", "problem_type": "mildew", "severity": "mild", "area": "A"}
    resp = client.post("/api/reports", data=data, files=files)
    assert resp.status_code == 201
    assert resp.json()["image_path"] is not None


def test_invalid_image_type():
    files = {"upload_file": ("img.txt", BytesIO(b"hello"), "text/plain")}
    data = {"input_channel": "smartphone", "problem_type": "mildew", "severity": "mild", "area": "A"}
    resp = client.post("/api/reports", data=data, files=files)
    assert resp.status_code == 400


def test_missing_required_field():
    resp = client.post("/api/reports", data={"input_channel": "ussd", "problem_type": "rust", "area": "A"})
    assert resp.status_code == 422


def test_list_reports_and_filters():
    client.post("/api/reports", data={"input_channel": "ussd", "problem_type": "rust", "severity": "mild", "area": "A"})
    resp = client.get("/api/reports", params={"input_channel": "ussd"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1


def test_pagination():
    resp = client.get("/api/reports", params={"skip": 0, "limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()["reports"]) <= 1


def test_get_missing_report():
    resp = client.get("/api/reports/999999")
    assert resp.status_code == 404

@pytest.fixture(autouse=True)
def _override_db_fixture():
    app.dependency_overrides[get_db] = _override_db
    yield
    app.dependency_overrides.pop(get_db, None)
