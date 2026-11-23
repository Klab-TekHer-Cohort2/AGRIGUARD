"""Risk-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Calculated risk level."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskAssessmentRequest(BaseModel):
    """Request to trigger a risk assessment."""

    area: Optional[str] = None
    problem_type: Optional[str] = None
    window_hours: Optional[int] = None


class RiskAssessmentResponse(BaseModel):
    """Response from the risk engine."""

    risk_score: float
    risk_level: RiskLevel
    problem_type: Optional[str] = None
    area: Optional[str] = None
    reasons: list[str]
    contributing_report_count: int
    assessment_timestamp: datetime
    weather_temperature: Optional[float] = None
    weather_humidity: Optional[float] = None
    weather_available: bool = False