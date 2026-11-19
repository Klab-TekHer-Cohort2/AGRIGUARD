"""Tests: confidence thresholds, severity, escalation.

Mirrors ``tests/confidence.severity.test.js``.
"""

from app.services.crop_analysis_service import crop_analysis_service
from app.services.escalation_service import escalation_service


# ── Confidence logic ──────────────────────────────────────────────────────────
def test_confidence_high_tier():
    t = crop_analysis_service.calculate_confidence(0.92)
    assert t["tier"] == "high"
    assert t["label"] == "High"


def test_confidence_medium_tier():
    t = crop_analysis_service.calculate_confidence(0.65)
    assert t["tier"] == "medium"


def test_confidence_low_tier():
    t = crop_analysis_service.calculate_confidence(0.38)
    assert t["tier"] == "low"


def test_boundary_exactly_0_80_is_high():
    assert crop_analysis_service.calculate_confidence(0.80)["tier"] == "high"


def test_boundary_exactly_0_50_is_medium():
    assert crop_analysis_service.calculate_confidence(0.50)["tier"] == "medium"


def test_boundary_0_49_is_low():
    assert crop_analysis_service.calculate_confidence(0.49)["tier"] == "low"


# ── Severity logic (independent of confidence) ───────────────────────────────
def test_high_severity_with_high_confidence_is_possible():
    sev = crop_analysis_service.calculate_severity(
        category="Disease",
        problem={"severityExample": "High"},
    )
    assert sev == "High"


def test_unknown_category_is_high_severity():
    sev = crop_analysis_service.calculate_severity(category="Unknown", problem=None)
    assert sev == "High"


def test_image_hint_can_upgrade_severity():
    sev = crop_analysis_service.calculate_severity(
        category="Disease",
        problem={"severityExample": "Moderate"},
        image_hint={"severity": "Critical"},
    )
    assert sev == "Critical"


def test_image_hint_does_not_downgrade_severity():
    sev = crop_analysis_service.calculate_severity(
        category="Disease",
        problem={"severityExample": "High"},
        image_hint={"severity": "Low"},
    )
    assert sev == "High"


# ── Agronomist escalation ─────────────────────────────────────────────────────
def test_low_confidence_escalates():
    r = escalation_service.should_escalate({"confidence": 0.38, "severity": "Moderate", "category": "Pest"})
    assert r["needsAgronomist"] is True
    assert "low_confidence" in r["reason"]


def test_high_severity_escalates_even_with_high_confidence():
    r = escalation_service.should_escalate({"confidence": 0.92, "severity": "High", "category": "Pest"})
    assert r["needsAgronomist"] is True
    assert "severity_high" in r["reason"]


def test_critical_severity_escalates():
    r = escalation_service.should_escalate({"confidence": 0.95, "severity": "Critical", "category": "Disease"})
    assert r["needsAgronomist"] is True
    assert "severity_critical" in r["reason"]


def test_unknown_category_escalates():
    r = escalation_service.should_escalate({"confidence": 0.45, "severity": "High", "category": "Unknown"})
    assert r["needsAgronomist"] is True
    assert "unknown_category" in r["reason"]


def test_farmer_requests_help_always_escalates():
    r = escalation_service.should_escalate(
        {"confidence": 0.92, "severity": "Low", "category": "Pest"},
        {"farmerRequestedHelp": True},
    )
    assert r["needsAgronomist"] is True
    assert "farmer_requested_help" in r["reason"]


def test_high_confidence_low_severity_known_category_no_escalation():
    r = escalation_service.should_escalate({"confidence": 0.92, "severity": "Moderate", "category": "Pest"})
    assert r["needsAgronomist"] is False
