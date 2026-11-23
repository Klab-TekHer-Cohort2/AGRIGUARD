"""Focused tests for synchronous report service."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Report
from app.services.report_service import ReportService


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_create_report():
    db = _session()
    svc = ReportService(db)
    r = svc.create_report("smartphone", "mildew", "moderate", "A", latitude=1.0, longitude=2.0)
    assert r.id is not None
    assert r.input_channel == "smartphone"
    assert r.area == "A"


def test_smartphone_report():
    db = _session()
    svc = ReportService(db)
    r = svc.create_smartphone_report("mildew", "mild", "A", ai_confidence=0.9)
    assert r.input_channel == "smartphone"
    assert r.confidence == 0.9


def test_ussd_report():
    db = _session()
    svc = ReportService(db)
    r = svc.create_ussd_report("rust", "severe", "B", description="leaves")
    assert r.input_channel == "ussd"
    assert r.description == "leaves"


def test_ivr_report():
    db = _session()
    svc = ReportService(db)
    r = svc.create_ivr_report("blight", "moderate", "C")
    assert r.input_channel == "ivr"


def test_get_report():
    db = _session()
    svc = ReportService(db)
    r = svc.create_report("smartphone", "mildew", "moderate", "A")
    fetched = svc.get_report(r.id)
    assert fetched is not None
    assert fetched.id == r.id


def test_get_missing_report():
    db = _session()
    svc = ReportService(db)
    assert svc.get_report(9999) is None


def test_list_reports_filters_pagination():
    db = _session()
    svc = ReportService(db)
    for i in range(5):
        svc.create_report("smartphone", "mildew", "moderate", "A")
    svc.create_report("ussd", "rust", "mild", "B")
    reports, total = svc.list_reports(input_channel="smartphone", area="A", skip=0, limit=2)
    assert total == 5
    assert len(reports) == 2
    # pagination
    reports2, _ = svc.list_reports(skip=2, limit=2)
    assert len(reports2) == 2


def test_delete_report():
    db = _session()
    svc = ReportService(db)
    r = svc.create_report("smartphone", "mildew", "moderate", "A")
    assert svc.delete_report(r.id) is True
    assert svc.get_report(r.id) is None
    assert svc.delete_report(9999) is False


def test_report_to_response():
    db = _session()
    svc = ReportService(db)
    r = svc.create_report("smartphone", "mildew", "moderate", "A")
    resp = svc.report_to_response(r)
    assert resp.id == r.id
    assert resp.area == "A"
