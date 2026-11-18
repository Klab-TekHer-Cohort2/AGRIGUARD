"""AgriGuard AI configuration.

All AI thresholds and runtime settings live here. Values can be overridden via
environment variables (loaded from .env by python-dotenv). This mirrors the
previous ``src/config/aiConfig.js`` so behaviour and the mock/openai modes stay
identical.
"""

import os

from dotenv import load_dotenv

# Load variables from .env if present. Does not override already-set env vars.
load_dotenv()


def _get_float(key: str, default: float) -> float:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Settings:
    """Runtime configuration for the AgriGuard AI layer.

    Attributes mirror the nested object in aiConfig.js:
      confidence.high / confidence.medium
      severity.levels / severity.escalateLevels
      escalation.lowConfidenceThreshold / escalateSeverities / escalateCategories
      outbreak.minReportsForRisk / highRiskReportCount / criticalRiskReportCount /
             timeWindowDays / alertRadiusKm
      mode, supportedLanguages, defaultLanguage
      image.maxSizeBytes / supportedMimeTypes
    """

    # ── Confidence thresholds ──────────────────────────────────────────────
    confidence_high: float = _get_float("AI_CONFIDENCE_HIGH", 0.80)
    confidence_medium: float = _get_float("AI_CONFIDENCE_MEDIUM", 0.50)
    # below medium == low confidence

    # ── Severity levels ──────────────────────────────────────────────────────
    severity_levels = ["Low", "Moderate", "High", "Critical"]
    escalate_severities = ["High", "Critical"]  # always escalate to agronomist

    # ── Agronomist escalation ────────────────────────────────────────────────
    escalation_low_confidence_threshold: float = _get_float("AI_CONFIDENCE_MEDIUM", 0.50)
    escalation_escalate_severities = ["High", "Critical"]
    escalation_escalate_categories = ["Unknown"]

    # ── Outbreak detection ───────────────────────────────────────────────────
    outbreak_min_reports_for_risk: int = _get_int("OUTBREAK_MIN_REPORTS", 3)
    outbreak_high_risk_report_count: int = _get_int("OUTBREAK_HIGH_RISK_REPORTS", 7)
    outbreak_critical_risk_report_count: int = _get_int("OUTBREAK_CRITICAL_RISK_REPORTS", 12)
    outbreak_time_window_days: int = _get_int("OUTBREAK_TIME_WINDOW_DAYS", 7)
    outbreak_alert_radius_km: float = _get_float("ALERT_RADIUS_KM", 5.0)

    # ── AI mode ──────────────────────────────────────────────────────────────
    # 'mock'   = deterministic prototype (always works, no API key needed)
    # 'openai' = OpenAI GPT-4o vision (requires OPENAI_API_KEY)
    mode: str = os.getenv("AI_MODE", "mock")

    # ── Language support ─────────────────────────────────────────────────────
    supported_languages = ["en", "rw"]
    default_language: str = "en"

    # ── Image analysis ───────────────────────────────────────────────────────
    image_max_size_bytes: int = 5 * 1024 * 1024  # 5 MB
    image_supported_mime_types = ["image/jpeg", "image/png", "image/webp"]

    # ── Server ───────────────────────────────────────────────────────────────
    port: int = _get_int("PORT", 5000)
    cors_origin: str = os.getenv("CORS_ORIGIN", "*")


# Singleton instance imported throughout the app.
settings = Settings()
