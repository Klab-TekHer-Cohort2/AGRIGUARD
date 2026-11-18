"""USSD Response Formatter.

Converts a CropAnalysisResult into a short, plain-text response suitable for a
USSD session (limited characters, no rich media).

Uses the SAME AI/data layer as the smartphone flow — USSD does NOT have a
separate AI system. It just formats the shared CropAnalysisResult differently.

USSD-friendly rules:
    - Short lines (USSD gateways may truncate around 140–180 chars per screen).
    - Plain ASCII (no emoji, no markdown).
    - One fact per line.
    - Always end with a clear status line.

Mirrors ``src/services/ussdResponseFormatter.js``.
"""

from app.services.language_service import language_service


def _round_pct(value):
    """Round a 0–1 confidence to a whole-number percentage string (matches JS Math.round)."""
    import math
    return str(math.floor((value or 0) * 100 + 0.5))


class UssdResponseFormatter:
    """Format analysis/risk results for USSD channels."""

    def format_crop_analysis(self, result):
        """Format a CropAnalysisResult into a USSD-friendly string.

        Args:
            result: a CropAnalysisResult dict.

        Returns:
            newline-joined plain-text string.
        """
        lang = result.get("language") or "en"

        def L(key):
            return language_service.get_message(key, lang)

        lines = []

        if result.get("category") == "Unknown" or not result.get("possibleProblem"):
            # Unknown / low-confidence path
            lines.append(L("possibleProblem") + ": " + L("unknownProblem"))
            lines.append(L("confidence") + ": " + _round_pct(result.get("confidence")) + "%")
            lines.append(L("reportSentForReview"))
            return "\n".join(lines)

        # Known problem path
        lines.append(f"{L('possibleProblem')}: {result['possibleProblem']}")
        lines.append(f"{L('confidence')}: {_round_pct(result.get('confidence'))}%")
        lines.append(f"{L('severity')}: {result['severity']}")

        # Short single-line advice (first recommendation only, for USSD length).
        advice = result.get("recommendation") and result["recommendation"][0]
        if advice:
            lines.append(f"{L('advice')}: {advice}")

        # Status line
        lines.append(
            f"{L('status')}: "
            f"{L('needsAgronomist') if result.get('needsAgronomist') else L('agronomistNotRequired')}"
        )

        return "\n".join(lines)

    def format_community_risk(self, risk_result):
        """Format a community risk result for USSD (very short summary)."""
        lines = []
        lines.append(f"Risk: {risk_result.get('riskLevel')}")
        if risk_result.get("problem"):
            lines.append(f"Problem: {risk_result['problem']}")
        if risk_result.get("crop"):
            lines.append(f"Crop: {risk_result['crop']}")
        lines.append(f"Reports: {risk_result.get('reportCount')}")
        if risk_result.get("affectedArea"):
            lines.append(f"Area: {risk_result['affectedArea']}")
        lines.append(
            f"Alert: {'Recommended' if risk_result.get('alertRecommended') else 'Not required'}"
        )
        return "\n".join(lines)


# Module-level singleton.
ussd_response_formatter = UssdResponseFormatter()
