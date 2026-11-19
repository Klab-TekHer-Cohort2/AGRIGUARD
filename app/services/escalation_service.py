"""Agronomist Escalation Service.

Responsible-AI logic: decides when a human agronomist must review a report
instead of relying solely on the AI assessment.

Escalate when:
    - confidence is low (< medium threshold)
    - severity is High or Critical
    - category is Unknown
    - the farmer explicitly requests human assistance
    - the AI cannot provide reliable guidance

Severity and confidence are evaluated INDEPENDENTLY. A high-confidence
high-severity result still escalates, because the AI is confident the problem
is serious.

Mirrors ``src/services/escalationService.js``.
"""

from app.config import settings


class EscalationService:
    """Decide whether a crop analysis should be escalated to an agronomist."""

    def should_escalate(self, analysis, opts=None):
        """Evaluate escalation for an analysis result.

        Args:
            analysis: dict with ``confidence``, ``severity``, ``category``.
            opts: dict with optional ``farmerRequestedHelp``.

        Returns:
            ``{"needsAgronomist": bool, "reason": str}`` where ``reason`` is a
            comma-separated list of triggered reasons, or ``"none"``.
        """
        opts = opts or {}
        reasons = []

        # Farmer explicitly asked for help → always escalate.
        if opts.get("farmerRequestedHelp"):
            reasons.append("farmer_requested_help")

        # Low confidence.
        confidence = analysis.get("confidence")
        if confidence is None or confidence < settings.escalation_low_confidence_threshold:
            reasons.append("low_confidence")

        # High / critical severity.
        severity = analysis.get("severity")
        if severity in settings.escalation_escalate_severities:
            reasons.append(f"severity_{(severity or '').lower()}")

        # Unknown category.
        category = analysis.get("category")
        if category and category in settings.escalation_escalate_categories:
            reasons.append("unknown_category")

        return {
            "needsAgronomist": len(reasons) > 0,
            "reason": ",".join(reasons) or "none",
        }


# Module-level singleton.
escalation_service = EscalationService()
