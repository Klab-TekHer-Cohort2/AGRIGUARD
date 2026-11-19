"""Tests: multilingual detection (section 26)."""

from ai.src.multilingual import detect_language, resolve_language


def test_english_detected_as_english():
    assert detect_language("My maize leaves are turning yellow.") == "en"


def test_kinyarwanda_detected_as_rw():
    assert detect_language("Ibibabi by'ibigori byanjye birahinduka umuhondo.") == "rw"


def test_empty_defaults_to_english():
    assert detect_language("") == "en"


def test_none_defaults_to_english():
    assert detect_language(None) == "en"


def test_explicit_language_overrides_detection():
    assert resolve_language(explicit="rw", text="hello maize") == "rw"


def test_auto_falls_back_to_detection():
    assert resolve_language(explicit=None, text="ibigori byanjye") == "rw"
    assert resolve_language(explicit=None, text="my maize field") == "en"
