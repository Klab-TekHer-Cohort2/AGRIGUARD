"""Tests: crop problem classification (sections 5, 7, 8).

Covers both backends:
  - keyword fallback (deterministic, no sklearn needed) for the Fall Armyworm
    scenario and the unknown scenario.
  - the scikit-learn ML classifier (when sklearn is installed): trains on the
    knowledge base and checks that a real maize-pest description is classified
    as a maize problem, plus that evaluation metrics are produced.
"""

import pytest

from ai.src import classification
from ai.src.crop_analysis import analyze_report


# ── Keyword fallback (deterministic, always available) ───────────────────────
def test_keyword_classifies_fall_armyworm():
    cls = classification.classify_problem(
        crop_id="maize",
        description="the leaves of my maize have holes and i can see small insects near the whorl",
        use_ml=False,
    )
    assert cls["category"] == "Pest"
    assert cls["problem_id"] == "fall-armyworm"
    assert cls["confidence"] >= 0.80
    assert cls["source"] == "keyword"


def test_keyword_unknown_for_gibberish():
    cls = classification.classify_problem(crop_id="tomato", description="something strange zzzqwerty", use_ml=False)
    assert cls["category"] == "Unknown"
    assert cls["confidence"] < 0.50


def test_analyze_report_keyword_fall_armyworm():
    result = analyze_report(
        crop="Maize",
        description="Holes in leaves, small insects near the whorl.",
        image="maize-armyworm.jpg",
        use_ml=False,
    )
    d = result.to_dict()
    assert d["crop_id"] == "maize"
    assert d["category"] == "Pest"
    assert d["problem_id"] == "fall-armyworm"
    assert d["confidence_level"] == "High"
    assert d["vision_source"] == "simulated-demo"


def test_analyze_report_unknown_escalates():
    result = analyze_report(
        crop="Tomato",
        description="Something strange is happening, I am not sure what it is.",
        use_ml=False,
    )
    d = result.to_dict()
    assert d["category"] == "Unknown"
    assert d["confidence"] < 0.50
    assert d["needs_agronomist"] is True
    assert "low_confidence" in d["escalation_reason"]


# ── scikit-learn ML classifier (only when sklearn is installed) ───────────────
@pytest.mark.skipif(not classification.SKLEARN_AVAILABLE, reason="scikit-learn not installed")
def test_ml_classifier_trains_and_evaluates():
    eval_result = classification.train_classifier(test_size=0.25, random_state=42)
    assert eval_result["n_train"] > 0
    assert eval_result["n_test"] > 0
    assert eval_result["n_classes"] == 21
    # Accuracy must be above random chance (1/21 ≈ 0.05).  This is a 21-class
    # prototype knowledge base with very few samples, so we only verify the
    # pipeline ran, produced real numeric metrics, and beats pure guessing.
    assert eval_result["accuracy"] > 1 / eval_result["n_classes"]
    assert 0.0 <= eval_result["f1_macro"] <= 1.0
    assert "report" in eval_result
    assert isinstance(eval_result["confusion_matrix"], list)


@pytest.mark.skipif(not classification.SKLEARN_AVAILABLE, reason="scikit-learn not installed")
def test_ml_classifier_predicts_maize_pest_for_armyworm_text():
    classification.train_classifier(random_state=42)
    cls = classification.classify_problem(
        crop_id="maize",
        description="irregular holes in leaves, larvae hiding in the whorl, sawdust frass",
        use_ml=True,
    )
    maize_problems = {p["id"] for p in __import__("ai.src.knowledge", fromlist=["get_problems_by_crop"]).get_problems_by_crop("maize")}
    assert cls["problem_id"] in maize_problems
    assert cls["source"] == "ml"
