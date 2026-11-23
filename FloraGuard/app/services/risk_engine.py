"""Deterministic, rule-based risk prediction engine for FloraGuard.

NOTE: These are prototype heuristic rules. They are NOT scientifically
validated and must not be treated as a validated agronomic model.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, Sequence

from app.core.config import settings
from app.db.models import Report
from app.schemas.risk import RiskAssessmentResponse, RiskLevel
from typing import Any

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {"mild": 5.0, "moderate": 10.0, "severe": 20.0}
RECENCY_BONUS_HOURS = 24
RECENCY_BONUS_POINTS = 5.0
WEATHER_HUMIDITY_THRESHOLD = 70.0
WEATHER_TEMP_MIN = 20.0
WEATHER_TEMP_MAX = 30.0
WEATHER_POINTS = 10.0
REPORT_BASE_POINTS = 8.0


class RiskEngine:
    """Rule-based risk engine."""

    def __init__(
        self,
        window_hours: Optional[int] = None,
        low_max: Optional[float] = None,
        medium_max: Optional[float] = None,
    ) -> None:
        self.window_hours = window_hours if window_hours is not None else settings.RISK_WINDOW_HOURS
        self.low_max = low_max if low_max is not None else settings.RISK_SCORE_LOW_MAX
        self.medium_max = medium_max if medium_max is not None else settings.RISK_SCORE_MEDIUM_MAX

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def assess(
        self,
        reports: Sequence[Report],
        area: Optional[str] = None,
        problem_type: Optional[str] = None,
        window_hours: Optional[int] = None,
        weather: Optional[Any] = None,
    ) -> RiskAssessmentResponse:
        window = window_hours if window_hours is not None else self.window_hours
        now = self._now()
        cutoff = now - timedelta(hours=window)

        contributing = []
        for r in reports:
            if area and r.area != area:
                continue
            if problem_type and r.problem_type != problem_type:
                continue
            created = r.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created < cutoff:
                continue
            contributing.append(r)

        score = 0.0
        reasons: list[str] = []

        count = len(contributing)
        if count > 0:
            score += count * REPORT_BASE_POINTS
            reasons.append(f"{count} report(s) in the last {window} hours.")

        # Severity contribution
        severity_points = 0.0
        for r in contributing:
            w = SEVERITY_WEIGHTS.get((r.severity or "").lower(), 0.0)
            severity_points += w
        if severity_points > 0:
            score += severity_points
            reasons.append(f"Severity contribution: {severity_points:.0f} points.")

        # Recency bonus
        recent_cutoff = now - timedelta(hours=RECENCY_BONUS_HOURS)
        recent_count = 0
        for r in contributing:
            created = r.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created >= recent_cutoff:
                recent_count += 1
        if recent_count > 0:
            bonus = recent_count * RECENCY_BONUS_POINTS
            score += bonus
            reasons.append(f"{recent_count} report(s) within last {RECENCY_BONUS_HOURS}h (+{bonus:.0f}).")

        # Weather
        weather_temp = None
        weather_humidity = None
        weather_available = False
        if weather is not None and weather.available and weather.is_valid:
            weather_temp = weather.temperature
            weather_humidity = weather.humidity
            weather_available = True
            if (
                weather.humidity is not None
                and weather.humidity >= WEATHER_HUMIDITY_THRESHOLD
                and weather.temperature is not None
                and WEATHER_TEMP_MIN <= weather.temperature <= WEATHER_TEMP_MAX
            ):
                score += WEATHER_POINTS
                reasons.append(
                    f"Favorable disease conditions (temp {weather.temperature:.1f}C, "
                    f"humidity {weather.humidity:.1f}%) +{WEATHER_POINTS:.0f}."
                )
            else:
                reasons.append("Weather not in high-risk range.")
        else:
            reasons.append("Weather data unavailable; skipped weather contribution.")

        # Classify
        if score <= self.low_max:
            level = RiskLevel.LOW
        elif score <= self.medium_max:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.HIGH

        if count == 0:
            reasons.append("No contributing reports; baseline LOW risk.")

        return RiskAssessmentResponse(
            risk_score=round(score, 2),
            risk_level=level,
            problem_type=problem_type,
            area=area,
            reasons=reasons,
            contributing_report_count=count,
            assessment_timestamp=now,
            weather_temperature=weather_temp,
            weather_humidity=weather_humidity,
            weather_available=weather_available,
        )


risk_engine = RiskEngine()
"""Module-level singleton."""
