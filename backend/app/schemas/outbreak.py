"""Pydantic v2 schemas for the outbreak detection and alert management feature."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    id: int
    title_en: str = Field(max_length=128)
    title_rw: str = Field(max_length=128)
    pest_name: Optional[str] = Field(None, max_length=128)
    target_district: str
    target_sector: Optional[str] = None
    severity: str
    status: str
    affected_report_count: int = 1
    source_report_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertDetailResponse(AlertResponse):
    message_en: str
    message_rw: str
    resolved_by_user_id: Optional[int] = None
    resolved_at: Optional[datetime] = None


class RiskScoreResponse(BaseModel):
    district: str
    pest_name: Optional[str] = None
    crop_id: Optional[int] = None
    risk_score: float = Field(ge=0.0, le=1.0)
    contributing_report_count: int = Field(ge=0)
    threshold: float = Field(ge=0.0, le=1.0)
    above_threshold: bool


class OutbreakCheckRequest(BaseModel):
    report_id: int = Field(ge=1)
