"""Tests: outbreak detection (section 26)."""

from ai.src.outbreak_detection import detect_outbreak
from ai.src import knowledge


def test_many_nearby_recent_reports_elevated_risk():
    reports = knowledge.reports_as_dicts()
    result = detect_outbreak(reports)
    # The Kabarore Fall Armyworm cluster (12 reports) should NOT be LOW.
    assert result.risk_level in ("MEDIUM", "HIGH", "CRITICAL")
    assert result.report_count >= 3
    assert result.is_prototype is True
    assert "prototype" in result.disclaimer.lower()


def test_isolated_reports_low_risk():
    # Only the non-clustered reports -> each group has 1 report -> below threshold.
    isolated = [r for r in knowledge.reports_as_dicts() if r.get("community") != "Kabarore"]
    result = detect_outbreak(isolated)
    assert result.risk_level == "LOW"
    assert result.alert_recommended is False


def test_empty_reports_low_risk():
    result = detect_outbreak([])
    assert result.risk_level == "LOW"
    assert result.reason == "no_recent_reports"
    assert result.alert_recommended is False


def test_outbreak_identifies_fall_armyworm_maize():
    reports = knowledge.reports_as_dicts()
    result = detect_outbreak(reports)
    assert result.crop_id == "maize"
    assert (result.problem or "").lower().startswith("fall armyworm")
    assert "Kabarore" in (result.affected_area or "")
