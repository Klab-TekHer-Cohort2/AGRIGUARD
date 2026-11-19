"""Tests: language detection, RAG retrieval, AI assistant, USSD formatting.

Mirrors ``tests/language.assistant.test.js``.
"""

import re

from app.services.language_service import language_service
from app.services.rag_service import rag_service
from app.services.ai_assistant_service import ai_assistant_service
from app.services.ussd_response_formatter import ussd_response_formatter
from app.services.crop_analysis_service import crop_analysis_service


# ── Language detection ─────────────────────────────────────────────────────────
def test_english_question_detected_as_english():
    assert language_service.detect_language("My maize leaves are turning yellow.") == "en"


def test_kinyarwanda_question_detected_as_rw():
    assert language_service.detect_language("Ibibabi by'ibigori byanjye birahinduka umuhondo.") == "rw"


def test_empty_string_defaults_to_en():
    assert language_service.detect_language("") == "en"


def test_none_defaults_to_en():
    assert language_service.detect_language(None) == "en"


# ── Language-aware crop analysis ───────────────────────────────────────────────
async def test_english_description_yields_english_response_language():
    result = await crop_analysis_service.analyse_crop_report(
        {
            "crop": "Maize",
            "description": "Small insects eating the leaves of my maize.",
            "language": "en",
        }
    )
    assert result["language"] == "en"


async def test_kinyarwanda_description_auto_detected():
    result = await crop_analysis_service.analyse_crop_report(
        {
            "crop": "Maize",
            "description": "Hari udokoko duto kurya amababi y'ibigori byanjye.",
            # no explicit language → auto-detected
        }
    )
    assert result["language"] == "rw"


# ── RAG retrieval ─────────────────────────────────────────────────────────────
def test_rag_retrieves_relevant_articles_for_maize_pest():
    chunks = rag_service.retrieve("armyworm eating maize leaves", {"topK": 3})
    assert len(chunks) > 0
    assert re.search(r"armyworm|maize", chunks[0]["title"], re.IGNORECASE)


def test_rag_returns_empty_for_gibberish():
    chunks = rag_service.retrieve("xyzqwerty nonsense", {"topK": 3})
    assert chunks == []


def test_rag_build_context_produces_non_empty_string():
    chunks = rag_service.retrieve("fall armyworm maize", {"topK": 2})
    ctx = rag_service.build_context(chunks, "en")
    assert len(ctx) > 0
    assert "source:" in ctx


# ── Ask AgriGuard assistant ────────────────────────────────────────────────────
async def test_english_question_yields_english_answer_with_sources():
    result = await ai_assistant_service.answer_agricultural_question(
        "How can I prevent Fall Armyworm in my maize?"
    )
    assert result["language"] == "en"
    assert len(result["answer"]) > 0
    assert isinstance(result["sources"], list)


async def test_kinyarwanda_question_yields_kinyarwanda_answer():
    result = await ai_assistant_service.answer_agricultural_question(
        "Nigute nshobora kurinda ibigori byanjye kw'inzito y'ibigori?"
    )
    assert result["language"] == "rw"
    assert len(result["answer"]) > 0


async def test_no_retrieval_question_escalates_honestly():
    result = await ai_assistant_service.answer_agricultural_question(
        "What is the price of tea in China?"
    )
    assert result["confidence"] < 0.5
    assert result["needsAgronomist"] is True


async def test_empty_question_returns_validation_message():
    result = await ai_assistant_service.answer_agricultural_question("")
    assert re.search(r"provide a question|Tondeka", result["answer"])


# ── USSD formatter ─────────────────────────────────────────────────────────────
async def test_ussd_formats_known_problem_as_short_plain_text():
    result = await crop_analysis_service.analyse_crop_report(
        {
            "crop": "Maize",
            "description": "Small insects eating maize leaves, holes in the whorl.",
            "image": "maize-armyworm.jpg",
            "language": "en",
        }
    )
    text = ussd_response_formatter.format_crop_analysis(result)
    assert "Possible problem" in text
    assert "Confidence" in text
    assert "Severity" in text
    assert "Status" in text
    # No markdown
    assert "**" not in text
    assert "##" not in text


async def test_ussd_formats_unknown_problem_with_escalation_message():
    result = await crop_analysis_service.analyse_crop_report(
        {
            "crop": "Tomato",
            "description": "Something strange, not sure what this is about.",
            "language": "en",
        }
    )
    text = ussd_response_formatter.format_crop_analysis(result)
    assert "agronomist" in text.lower()
