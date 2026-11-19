"""Severity assessment (section 10).

Severity = how serious the identified problem is for the crop. It is INDEPENDENT
of confidence (section 9):

    Confidence: 0.94   Severity: High
    -> the AI is confident about its identification, AND the problem is serious.

Do NOT assume high confidence == high severity.

Levels (ordered, lowest to highest): Low, Moderate, High, Critical.
"""

SEVERITY_LEVELS = ["Low", "Moderate", "High", "Critical"]
ESCALATE_SEVERITIES = ["High", "Critical"]  # always escalate to agronomist


def severity_index(level: str) -> int:
    """Position of a severity level in the ordered list (0-based). Unknown → 1."""
    return SEVERITY_LEVELS.index(level) if level in SEVERITY_LEVELS else 1


def calculate_severity(category, problem=None, image_hint=None) -> str:
    """Determine severity for an identified problem.

    Strategy:
        - Unknown category -> "High" (needs human eyes on the field).
        - Use the problem's ``severity_example`` as the data-driven baseline.
        - A vision hint may UPGRADE severity (e.g. widespread damage -> Critical)
          but never downgrade it.
    """
    if category == "Unknown":
        return "High"

    severity = (problem or {}).get("severity_example") or (problem or {}).get("severityExample") or "Moderate"

    if image_hint and image_hint.get("severity"):
        if severity_index(image_hint["severity"]) > severity_index(severity):
            severity = image_hint["severity"]

    return severity
