"""Map-related Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AreaRiskSummary(BaseModel):
    """Privacy-safe area-level risk summary."""

    area: str
    total_reports: int
    high_risk_count: int
    moderate_risk_count: int
    mild_risk_count: int
    dominant_problem: Optional[str] = None
    latest_risk_level: Optional[RiskLevel] = None
    latest_risk_score: Optional[float] = None


class MapReportsResponse(BaseModel):
    """Response for the map endpoint."""

    areas: list[AreaRiskSummary]
    generated_at: datetime