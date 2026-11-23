"""Focused tests for the risk engine."""

from datetime import datetime, timedelta, timezone

from app.db.models import Report
from app.schemas.risk import RiskLevel
from app.services.risk_engine import RiskEngine
from types import SimpleNamespace


def _report(area="A", problem="powdery_mildew", severity="moderate", hours_ago=1):
    r = Report(
        input_channel="smartphone",
        problem_type=problem,
        severity=severity,
        area=area,
        created_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
    )
    return r


def test_no_reports_low():
    engine = RiskEngine()
    res = engine.assess([], area="A")
    assert res.risk_level == RiskLevel.LOW
    assert res.contributing_report_count == 0
    assert res.risk_score == 0.0


def test_high_frequency_high():
    engine = RiskEngine(window_hours=72, low_max=29, medium_max=59)
    reports = [_report(hours_ago=i) for i in range(10)]
    res = engine.assess(reports, area="A")
    assert res.risk_level == RiskLevel.HIGH
    assert res.contributing_report_count == 10


def test_weather_unavailable_graceful():
    engine = RiskEngine()
    reports = [_report()]
    wdata = SimpleNamespace(temperature=None, humidity=None, available=False, is_valid=False)
    res = engine.assess(reports, area="A", weather=wdata)
    assert res.weather_available is False
    assert res.weather_temperature is None


def test_weather_available_contributes():
    engine = RiskEngine()
    reports = [_report()]
    wdata = SimpleNamespace(temperature=25.0, humidity=80.0, available=True, is_valid=True)
    res = engine.assess(reports, area="A", weather=wdata)
    assert res.weather_available is True
    assert res.weather_temperature == 25.0
    assert any("Favorable disease conditions" in r for r in res.reasons)


def test_filters_area_and_problem():
    engine = RiskEngine()
    r1 = _report(area="A", problem="mildew")
    r2 = _report(area="B", problem="mildew")
    res = engine.assess([r1, r2], area="A", problem_type="mildew")
    assert res.contributing_report_count == 1


def test_thresholds_configurable():
    engine = RiskEngine(low_max=1000, medium_max=2000)
    reports = [_report() for _ in range(2)]
    res = engine.assess(reports, area="A")
    assert res.risk_level == RiskLevel.LOW
