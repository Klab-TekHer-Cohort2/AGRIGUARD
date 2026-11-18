"""Crop Analysis Service — the deterministic prototype crop-problem analyser.

Responsibilities:
    classify_crop_problem(crop_id, description, image_hint) → category + problem
    calculate_confidence(confidence)                       → tier (high/med/low)
    calculate_severity(category, problem, image_hint)       → Low|Moderate|High|Critical
    generate_recommendation(crop_id, problem, lang, sev)   → localised advice list
    analyse_crop_report(input)                             → full CropAnalysisResult

MOCK MODE (default):
    Deterministic keyword + scenario mapping. The same input always produces
    the same output, so demos are reproducible and tests are stable.

REAL MODE:
    If AI_MODE=openai and OPENAI_API_KEY is set, analyse_crop_report delegates
    image analysis to imageAnalysisService (which calls the OpenAI vision API).
    A clean swap point — see image_analysis_service.py.

Architecture note: this module NEVER calls an external API directly. The image
analysis adapter is injected, so swapping mock↔real does not require touching
this file.

Mirrors ``src/services/cropAnalysisService.js``.
"""

import logging
import math
import re
from datetime import datetime, timezone

from app.config import settings
from app.data import knowledge_base as kb
from app.services.language_service import language_service
from app.services.escalation_service import escalation_service
from app.services.image_analysis_service import image_analysis_service

logger = logging.getLogger("agriguard.crop_analysis")


def _round2(value):
    """Round to 2 decimals, rounding half up (matches JS ``Math.round(x*100)/100``)."""
    return math.floor(value * 100 + 0.5) / 100


def _now_iso():
    """UTC ISO 8601 timestamp with a trailing ``Z`` (matches JS ``new Date().toISOString()``)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class CropAnalysisService:
    """Main AI entry point producing the structured CropAnalysisResult contract."""

    # ── Classification ───────────────────────────────────────────────────────
    def classify_crop_problem(self, crop_id=None, description=None, image_hint=None):
        """Classify a crop problem based on crop + description (+ image hint).

        Returns:
            ``{"category", "problemId", "problem", "confidence"}`` where
            ``problem`` is the full knowledge-base dict (or None for Unknown).
        """
        text = f"{description or ''} {(image_hint or {}).get('text') or ''}".lower()

        # 1. Filter problems applicable to this crop.
        candidates = kb.get_problems_by_crop(crop_id)
        # If the crop is unknown, search across all problems.
        if not candidates:
            candidates = kb.problems

        # 2. Score each candidate by keyword overlap with the description.
        scored = []
        for p in candidates:
            score = 0
            for kw in p["keywords"]:
                if kw.lower() in text:
                    score += 1
            scored.append((p, score))

        # Sort by score descending (stable for ties, like JS Array.sort).
        scored.sort(key=lambda x: x[1], reverse=True)
        best = scored[0] if scored else None

        # 3. No keyword overlap → Unknown.
        if not best or best[1] == 0:
            return {
                "category": "Unknown",
                "problemId": None,
                "problem": None,
                "confidence": 0.38,  # baseline low confidence for unknown
            }

        # 4. Confidence is derived from the base problem confidence, boosted by
        #    keyword-match strength, capped at 0.98.
        base = best[0].get("confidence") or 0.7
        boost = min(best[1] * 0.04, 0.08)
        confidence = min(_round2(base + boost), 0.98)

        return {
            "category": best[0]["category"],
            "problemId": best[0]["id"],
            "problem": best[0],
            "confidence": confidence,
        }

    # ── Confidence ───────────────────────────────────────────────────────────
    def calculate_confidence(self, confidence):
        """Return a human-readable confidence tier: ``{"tier", "label"}``."""
        if confidence is None:
            return {"tier": "low", "label": "Low"}
        if confidence >= settings.confidence_high:
            return {"tier": "high", "label": "High"}
        if confidence >= settings.confidence_medium:
            return {"tier": "medium", "label": "Medium"}
        return {"tier": "low", "label": "Low"}

    # ── Severity ──────────────────────────────────────────────────────────────
    def calculate_severity(self, category=None, problem=None, image_hint=None):
        """Determine severity. Independent of confidence.

        Strategy:
            - If the problem has a severityExample, use it (data-driven).
            - If category is Unknown, escalate to High so a human reviews it.
            - Image hint may upgrade severity (e.g. widespread damage → Critical).
        """
        if category == "Unknown":
            return "High"  # unknown + reported = needs eyes on the field

        severity = (problem or {}).get("severityExample") or "Moderate"

        # Image-derived severity upgrade (from vision adapter).
        if image_hint and image_hint.get("severity"):
            levels = settings.severity_levels
            if levels.index(image_hint["severity"]) > levels.index(severity):
                severity = image_hint["severity"]

        return severity

    # ── Recommendations ──────────────────────────────────────────────────────
    def generate_recommendation(self, crop_id=None, problem=None, lang=None, severity=None):
        """Generate a localised recommendation based on the identified problem.

        Falls back to crop-specific general advice if the problem is unknown.
        """
        lang = lang or settings.default_language
        crop = kb.get_crop_by_id(crop_id)

        if problem:
            recs = list(language_service.localise_list(problem["recommendations"], lang))
            # Append escalation note for high/critical severity even when known.
            if severity in settings.escalation_escalate_severities:
                recs.append(
                    language_service.get_message("needsAgronomist", lang)
                    + " — "
                    + language_service.get_message("disclaimer", lang)
                )
            return recs

        # Unknown problem → general advice from the crop's prevention tips.
        if crop:
            return language_service.localise_list(crop["preventionTips"], lang)[:3]

        return [
            "Genzura umurima wawe kandi usabe inama z'umuhinzi w'ubuhinza."
            if lang == "rw"
            else "Inspect your field and seek advice from an agricultural extension officer."
        ]

    # ── Full report analysis (the public entry point) ───────────────────────
    async def analyse_crop_report(self, report_input):
        """Analyse a single crop report and return the full CropAnalysisResult.

        Args:
            report_input: dict with ``crop`` (required), optional ``description``,
                ``image``, ``location``, ``language``, ``farmerRequestedHelp``.

        Returns:
            dict matching the CropAnalysisResult contract (see docs).
        """
        crop_input = report_input.get("crop") or ""
        crop = kb.get_crop_by_name(crop_input) or kb.get_crop_by_id(
            re.sub(r"\s+", "-", crop_input.lower())
        )
        crop_id = crop["id"] if crop else "unknown"

        # Language: explicit > detected from description > default.
        lang = (
            report_input.get("language")
            or language_service.detect_language(report_input.get("description"))
            or settings.default_language
        )

        # 1. Image analysis (mock or real — adapter handles both).
        image_hint = None
        if report_input.get("image"):
            try:
                image_hint = await image_analysis_service.analyse_image(
                    image=report_input.get("image"),
                    crop_id=crop_id,
                    description=report_input.get("description"),
                )
            except Exception as err:
                # Never let a vision failure break the whole report — degrade gracefully.
                logger.error("[cropAnalysis] image analysis failed: %s", err)
                image_hint = None

        # 2. Classification.
        classification = self.classify_crop_problem(
            crop_id=crop_id,
            description=report_input.get("description"),
            image_hint=image_hint,
        )

        # 3. Confidence tier.
        conf_tier = self.calculate_confidence(classification["confidence"])

        # 4. Severity.
        severity = self.calculate_severity(
            category=classification["category"],
            problem=classification["problem"],
            image_hint=image_hint,
        )

        # 5. Recommendation.
        recommendation = self.generate_recommendation(
            crop_id=crop_id,
            problem=classification["problem"],
            lang=lang,
            severity=severity,
        )

        # 6. Escalation.
        escalation = escalation_service.should_escalate(
            {
                "confidence": classification["confidence"],
                "severity": severity,
                "category": classification["category"],
            },
            {"farmerRequestedHelp": report_input.get("farmerRequestedHelp")},
        )

        # 7. Build the structured CropAnalysisResult contract.
        result = {
            "category": classification["category"],
            "possibleProblem": (
                language_service.localise(classification["problem"]["name"], lang)
                if classification["problem"]
                else None
            ),
            "problemId": classification["problemId"],
            "confidence": classification["confidence"],
            "confidenceTier": conf_tier["tier"],
            "confidenceLabel": conf_tier["label"],
            "severity": severity,
            "recommendation": recommendation,
            "recommendationText": " ".join(recommendation),
            "needsAgronomist": escalation["needsAgronomist"],
            "escalationReason": escalation["reason"],
            "language": lang,
            "crop": language_service.localise(crop["name"], lang) if crop else crop_input,
            "cropId": crop_id,
            "location": report_input.get("location") or None,
            "imageAnalysed": bool(image_hint),
            "disclaimer": language_service.get_message("disclaimer", lang),
            "timestamp": _now_iso(),
        }

        return result


# Module-level singleton.
crop_analysis_service = CropAnalysisService()
