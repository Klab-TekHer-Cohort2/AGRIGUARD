"""Tests: agronomist escalation (section 26)."""

from ai.src.alert_logic import needs_agronomist


def test_low_confidence_escalates():
    r = needs_agronomist(confidence=0.38, severity="Moderate", category="Pest")
    assert r.needs_agronomist is True
    assert "low_confidence" in r.reasons


def test_high_severity_escalates_even_with_high_confidence():
    r = needs_agronomist(confidence=0.92, severity="High", category="Pest")
    assert r.needs_agronomist is True
    assert "severity_high" in r.reasons


def test_critical_severity_escalates():
    r = needs_agronomist(confidence=0.95, severity="Critical", category="Disease")
    assert r.needs_agronomist is True


def test_unknown_category_escalates():
    r = needs_agronomist(confidence=0.45, severity="High", category="Unknown")
    assert r.needs_agronomist is True
    assert "unknown_category" in r.reasons


def test_farmer_requested_help_always_escalates():
    r = needs_agronomist(confidence=0.92, severity="Low", category="Pest",
                         farmer_requested_help=True)
    assert r.needs_agronomist is True
    assert "farmer_requested_help" in r.reasons


def test_normal_high_confidence_low_severity_no_escalation():
    r = needs_agronomist(confidence=0.92, severity="Moderate", category="Pest")
    assert r.needs_agronomist is False
