"""Tests: confidence classification (section 26)."""

from ai.src.confidence import classify_confidence


def test_high_confidence():
    assert classify_confidence(0.92).level == "High"
    assert classify_confidence(0.92).tier == "high"


def test_medium_confidence():
    assert classify_confidence(0.65).level == "Medium"


def test_low_confidence():
    assert classify_confidence(0.38).level == "Low"


def test_boundary_exactly_0_80_is_high():
    assert classify_confidence(0.80).level == "High"


def test_boundary_exactly_0_50_is_medium():
    assert classify_confidence(0.50).level == "Medium"


def test_boundary_0_49_is_low():
    assert classify_confidence(0.49).level == "Low"


def test_none_is_low():
    assert classify_confidence(None).level == "Low"
