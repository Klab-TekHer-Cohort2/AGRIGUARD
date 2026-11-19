"""Crop report analysis — the orchestrator (section 5).

Ties together the pieces of the AI pipeline into one structured result:

    crop (+ description + image)
        -> vision hint (simulated or real CNN abstraction)
        -> problem classification (scikit-learn ML or keyword fallback)
        -> confidence tier (configurable thresholds)
        -> severity (independent of confidence)
        -> localised recommendation
        -> agronomist escalation decision
        -> CropAnalysisResult

The SAME function powers the smartphone flow and (via Person 3's USSD handler)
the USSD flow — there is no separate USSD AI. USSD only formats the output
differently (see ``ussd_format``).

The ``source`` field on the result records whether the ML classifier or the
keyword fallback was used; ``vision_source`` records whether the vision hint
came from a real model, the simulated demo, or no image at all (section 6:
distinguish real vs simulated).
"""

import re
from typing import Any, Dict, Optional

from ai.src import classification, vision, knowledge
from ai.src.confidence import classify_confidence, blend_confidence
from ai.src.severity import calculate_severity
from ai.src.recommendations import generate_recommendation
from ai.src.alert_logic import needs_agronomist
from ai.src.multilingual import resolve_language, localise, get_message
from ai.src.models import CropAnalysisResult


def _resolve_crop(crop_input: str) -> Dict[str, Any]:
    crop = knowledge.get_crop_by_name(crop_input)
    if not crop:
        crop = knowledge.get_crop_by_id(re.sub(r"\s+", "-", (crop_input or "").lower()))
    return crop


def analyze_report(
    crop: str,
    description: Optional[str] = None,
    image: Optional[Any] = None,
    location: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
    farmer_requested_help: bool = False,
    use_ml: bool = True,
    vision_mode: str = "simulated",
) -> CropAnalysisResult:
    """Analyse a single crop report and return a structured CropAnalysisResult.

    Args:
        crop: crop name or id (required).
        description: free-text symptom description.
        image: image filename/URL/bytes (processed by the vision backend).
        location: optional ``{"lat", "lng", "community"}`` (passed through).
        language: explicit language override ("en"/"rw"); auto-detected if None.
        farmer_requested_help: if True, always escalates to an agronomist.
        use_ml: use the trained scikit-learn classifier if available (else keyword).
        vision_mode: "simulated" (default, always works) or "real" (needs weights).

    Returns:
        CropAnalysisResult dataclass (call ``.to_dict()`` for JSON).
    """
    crop_obj = _resolve_crop(crop)
    crop_id = crop_obj["id"] if crop_obj else "unknown"

    lang = resolve_language(explicit=language, text=description)

    # 1. Vision hint (simulated demo by default; real CNN if configured).
    image_hint = None
    vision_source = "none"
    if image:
        try:
            image_hint = vision.analyse_image(image=image, crop_id=crop_id, description=description, mode=vision_mode)
            vision_source = image_hint.get("source", "simulated-demo")
        except Exception:
            image_hint = None
            vision_source = "none"

    # 2. Problem classification (ML or keyword).
    cls = classification.classify_problem(crop_id, description, image_hint=image_hint, use_ml=use_ml)
    problem = cls["problem"]
    base_confidence = cls["confidence"]

    # 3. Confidence tier (configurable thresholds). For the ML path we also add
    #    a small keyword-overlap boost so strongly described cases read higher.
    if cls["source"] == "ml" and problem:
        text = f"{description or ''} {(image_hint or {}).get('text') or ''}".lower()
        kw_hits = sum(1 for kw in problem["keywords"] if kw.lower() in text)
        confidence = blend_confidence(base_confidence, min(kw_hits * 0.02, 0.06))
    else:
        confidence = base_confidence
    conf = classify_confidence(confidence)

    # 4. Severity (independent of confidence; image hint may upgrade).
    severity = calculate_severity(cls["category"], problem, image_hint)

    # 5. Recommendation (localised).
    recommendation = generate_recommendation(crop_id, problem, lang, severity)

    # 6. Agronomist escalation.
    escalation = needs_agronomist(confidence, severity, cls["category"], farmer_requested_help)

    return CropAnalysisResult(
        crop=localise({"en": crop_obj["name_en"], "rw": crop_obj["name_rw"]}, lang) if crop_obj else (crop or ""),
        crop_id=crop_id,
        category=cls["category"],
        possible_problem=(
            localise({"en": problem["name_en"], "rw": problem["name_rw"]}, lang)
            if problem else None
        ),
        problem_id=cls["problem_id"],
        confidence=round(confidence, 2),
        confidence_level=conf.level,
        severity=severity,
        recommendation=recommendation,
        recommendation_text=" ".join(recommendation),
        needs_agronomist=escalation.needs_agronomist,
        escalation_reason=escalation.reason,
        language=lang,
        image_analysed=bool(image_hint),
        source=cls["source"],
        vision_source=vision_source,
        disclaimer=get_message("disclaimer", lang),
    )


def ussd_format(result: CropAnalysisResult) -> str:
    """Format a CropAnalysisResult as a short USSD-friendly plain-text string.

    USSD uses the SAME AI logic (analyze_report); only the formatting differs.
    """
    lang = result.language or "en"

    def L(key):
        return get_message(key, lang)

    lines = []
    if result.category == "Unknown" or not result.possible_problem:
        lines.append(f"{L('possible_problem')}: {L('unknown_problem')}")
        lines.append(f"{L('confidence')}: {int(round(result.confidence * 100))}%")
        lines.append(L("report_sent_for_review"))
        return "\n".join(lines)

    lines.append(f"{L('possible_problem')}: {result.possible_problem}")
    lines.append(f"{L('confidence')}: {int(round(result.confidence * 100))}%")
    lines.append(f"{L('severity')}: {result.severity}")
    advice = result.recommendation[0] if result.recommendation else None
    if advice:
        lines.append(f"{L('advice')}: {advice}")
    lines.append(
        f"{L('status')}: "
        f"{L('needs_agronomist') if result.needs_agronomist else L('agronomist_not_required')}"
    )
    return "\n".join(lines)


def process_ussd_report(farmer_id, crop, problem_description, location, language="en"):
    """Process a USSD report (section 17) — same AI, short response.

    Returns ``{"farmer_id", "ussd_response", "analysis"}``.
    """
    loc = {"community": location} if isinstance(location, str) and location else location
    result = analyze_report(
        crop=crop,
        description=problem_description,
        location=loc,
        language=language,
    )
    return {
        "farmer_id": farmer_id,
        "ussd_response": ussd_format(result),
        "analysis": result.to_dict(),
    }
