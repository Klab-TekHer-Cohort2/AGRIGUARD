"""Confidence calculation (section 9).

Confidence = how sure the AI is about its identification. It is a SEPARATE
concept from severity (section 10): a high-confidence result can still be a
high-severity problem, and a low-confidence result is not automatically mild.

Thresholds are configurable via the ``ConfidenceConfig`` dataclass so the
team's backend can tune them without touching this module.
"""

from dataclasses import dataclass

from ai.src.models import ConfidenceResult


@dataclass
class ConfidenceConfig:
    """Configurable confidence thresholds (0.0–1.0)."""
    high: float = 0.80
    medium: float = 0.50

    def validate(self):
        if not (0.0 < self.medium <= self.high <= 1.0):
            raise ValueError(
                f"Confidence thresholds invalid: need 0 < medium({self.medium}) "
                f"<= high({self.high}) <= 1"
            )


# Default config (matches the AgriGuard contract used by the FastAPI service).
DEFAULT_CONFIG = ConfidenceConfig()


def classify_confidence(score: float, config: ConfidenceConfig = None) -> ConfidenceResult:
    """Classify a numeric confidence score into a tier.

    Returns a ``ConfidenceResult`` with both ``level`` (display) and ``tier``
    (machine-readable), plus the original ``score``.

    Examples (default thresholds):
        0.92 -> High
        0.65 -> Medium
        0.38 -> Low
    """
    config = config or DEFAULT_CONFIG
    config.validate()

    if score is None:
        return ConfidenceResult(score=0.0, level="Low", tier="low")

    if score >= config.high:
        level, tier = "High", "high"
    elif score >= config.medium:
        level, tier = "Medium", "medium"
    else:
        level, tier = "Low", "low"
    return ConfidenceResult(score=float(score), level=level, tier=tier)


def blend_confidence(base: float, keyword_boost: float, cap: float = 0.98) -> float:
    """Combine a model-derived base confidence with a keyword-overlap boost.

    Used by the crop-analysis orchestrator: the trained classifier provides a
    probability (base), and matching known symptom keywords adds a small boost,
    capped so the pipeline never reports unrealistic 1.0 certainty.
    """
    return float(min(base + keyword_boost, cap))
