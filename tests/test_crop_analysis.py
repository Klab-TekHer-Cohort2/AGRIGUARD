"""Tests: crop report analysis end-to-end (deterministic mock).

Mirrors ``tests/cropAnalysis.test.js``.

These tests call the async ``analyse_crop_report`` coroutine; pytest-asyncio
runs them automatically (asyncio_mode=auto, configured in pyproject.toml).
"""

import re

from app.services.crop_analysis_service import crop_analysis_service
from app.data.prototype_dataset import prototype_dataset as dataset


# ── analyse_crop_report — Fall Armyworm demo ───────────────────────────────
async def test_fall_armyworm_identifies_crop_as_maize():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["smartphoneReport"])
    assert result["cropId"] == "maize"


async def test_fall_armyworm_classifies_as_pest():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["smartphoneReport"])
    assert result["category"] == "Pest"


async def test_fall_armyworm_identifies_problem():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["smartphoneReport"])
    assert re.search(r"Fall Armyworm", result["possibleProblem"], re.IGNORECASE)
    assert result["problemId"] == "fall-armyworm"


async def test_fall_armyworm_confidence_is_high():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["smartphoneReport"])
    assert result["confidence"] >= 0.80
    assert result["confidenceTier"] == "high"


async def test_fall_armyworm_severity_is_supported_level():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["smartphoneReport"])
    assert result["severity"] in ["Low", "Moderate", "High", "Critical"]


async def test_fall_armyworm_has_recommendation_list():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["smartphoneReport"])
    assert isinstance(result["recommendation"], list)
    assert len(result["recommendation"]) > 0


async def test_fall_armyworm_moderate_severity_no_agronomist():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["smartphoneReport"])
    # Fall Armyworm default severityExample is Moderate; high confidence → no escalation
    if result["severity"] == "Moderate":
        assert result["needsAgronomist"] is False


async def test_fall_armyworm_image_was_analysed():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["smartphoneReport"])
    assert result["imageAnalysed"] is True


# ── analyse_crop_report — Unknown problem (low confidence) ─────────────────
async def test_unknown_classifies_as_unknown():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["unknownReport"])
    assert result["category"] == "Unknown"


async def test_unknown_confidence_is_low():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["unknownReport"])
    assert result["confidence"] < 0.50


async def test_unknown_escalates_to_agronomist():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["unknownReport"])
    assert result["needsAgronomist"] is True
    assert "low_confidence" in result["escalationReason"]


# ── analyse_crop_report — Farmer requests help ─────────────────────────────
async def test_farmer_requests_help_escalates():
    result = await crop_analysis_service.analyse_crop_report(dataset["demoScenarios"]["farmerRequestsHelp"])
    assert result["needsAgronomist"] is True
    assert "farmer_requested_help" in result["escalationReason"]


# ── Data quality — recommendations consistent with crop ─────────────────────
async def test_maize_armyworm_recommendation_is_maize_relevant():
    result = await crop_analysis_service.analyse_crop_report(
        {
            "crop": "Maize",
            "description": "holes in leaves, small insects, whorl damage",
            "image": "maize-armyworm.jpg",
        }
    )
    rec_text = result["recommendationText"].lower()
    # Should reference maize or armyworm-related actions, not unrelated crops.
    assert re.search(r"maize|armyworm|whorl|field|inspect", rec_text)
