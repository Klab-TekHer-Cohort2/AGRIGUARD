"""Focused tests for alert service."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Alert
from app.services.alert_service import AlertService


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_create_alert_high():
    db = _session()
    svc = AlertService(db)
    alert = svc.create_alert("mildew", "A", "HIGH", 75.0, ["reason1"])
    assert alert is not None
    assert alert.delivery_status == "skipped"
    assert alert.preventive_guidance


def test_non_high_returns_none():
    db = _session()
    svc = AlertService(db)
    assert svc.create_alert("mildew", "A", "MEDIUM", 40.0, ["r"]) is None


def test_dedup():
    db = _session()
    svc = AlertService(db)
    a1 = svc.create_alert("mildew", "A", "HIGH", 75.0, ["r"])
    a2 = svc.create_alert("mildew", "A", "HIGH", 80.0, ["r2"])
    assert a1 is not None
    assert a2 is None


def test_alert_to_response():
    db = _session()
    svc = AlertService(db)
    alert = svc.create_alert("mildew", "A", "HIGH", 75.0, ["r1", "r2"])
    resp = svc.alert_to_response(alert)
    assert resp.reasons == ["r1", "r2"]
    assert resp.delivery_status == "skipped"
