"""Alert-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AlertStatus(str, Enum):
    """Delivery status of an alert."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class AlertCreate(BaseModel):
    """Request to create an alert manually."""

    problem_type: str
    area: str
    risk_level: str
    risk_score: float
    reasons: list[str]
    preventive_guidance: str
    delivery_status: AlertStatus = AlertStatus.PENDING


class AlertResponse(BaseModel):
    """Schema for alert responses."""

    id: int
    problem_type: str
    area: str
    risk_level: str
    risk_score: float
    reasons: list[str]
    preventive_guidance: str
    delivery_status: str
    created_at: datetime

    model_config = {"from_attributes": True}