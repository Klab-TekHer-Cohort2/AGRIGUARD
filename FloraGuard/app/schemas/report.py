"""Report-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class InputChannel(str, Enum):
    """Where the report originated from."""

    SMARTPHONE = "smartphone"
    USSD = "ussd"
    IVR = "ivr"


class Severity(str, Enum):
    """Reported severity level."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class ReportCreate(BaseModel):
    """Base schema for creating a report (shared fields)."""

    input_channel: InputChannel
    problem_type: str = Field(..., min_length=1, max_length=100)
    severity: Severity
    area: str = Field(..., min_length=1, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("problem_type")
    @classmethod
    def problem_type_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("problem_type must not be empty")
        return v.strip()


class SmartphoneReportCreate(ReportCreate):
    """Schema for smartphone reports with optional image."""

    input_channel: InputChannel = InputChannel.SMARTPHONE
    image_path: Optional[str] = None
    ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class USSDReportCreate(ReportCreate):
    """Schema for USSD reports. No image, no AI confidence."""

    input_channel: InputChannel = InputChannel.USSD


class IVRReportCreate(ReportCreate):
    """Schema for IVR reports. No image, no AI confidence."""

    input_channel: InputChannel = InputChannel.IVR


class ReportResponse(BaseModel):
    """Schema for report responses."""

    id: int
    input_channel: str
    problem_type: str
    severity: str
    confidence: Optional[float] = None
    area: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_path: Optional[str] = None
    description: Optional[str] = None
    weather_temperature: Optional[float] = None
    weather_humidity: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """Paginated list of reports."""

    total: int
    reports: list[ReportResponse]