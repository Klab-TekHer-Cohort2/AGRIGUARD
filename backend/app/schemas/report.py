import json
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.report import ReportChannel, ReportSeverity, ReportStatus


class ReportImageResponse(BaseModel):
    id: int
    report_id: int
    image_url: str
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: str
    upload_channel: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportHistoryResponse(BaseModel):
    id: int
    previous_status: Optional[str] = None
    new_status: str
    action_type: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIResultSummary(BaseModel):
    id: int
    model_name: str
    predicted_pest_en: str
    predicted_pest_rw: Optional[str] = None
    confidence_score: float
    detected_severity: str
    recommendations: Optional[Union[List[str], str]] = None
    is_mock: bool = False
    is_verified_correct: Optional[bool] = None

    @field_validator("recommendations", mode="before")
    def parse_recommendations(cls, val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return [val]
        return val

    model_config = ConfigDict(from_attributes=True)


class CropReportCreate(BaseModel):
    crop_id: int = Field(..., description="ID of the crop from /crops catalogue")
    channel: ReportChannel = Field(ReportChannel.APP, description="USSD, IVR, APP, WEB, SMS")
    description: Optional[str] = Field(None, description="Detailed problem description")
    symptoms: List[str] = Field(default_factory=list, description="Observed symptom flags")
    district: Optional[str] = Field(None, description="Defaults to farmer's primary district if omitted")
    sector: Optional[str] = Field(None, description="Defaults to farmer's primary sector if omitted")
    cell: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: ReportSeverity = Field(ReportSeverity.LOW, description="Farmer's perceived severity")


class CropReportResponse(BaseModel):
    id: int
    report_code: str
    farmer_id: int
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    crop_id: int
    crop_name_en: Optional[str] = None
    crop_name_rw: Optional[str] = None
    channel: ReportChannel
    description: Optional[str] = None
    symptoms: List[str] = []
    district: str
    sector: str
    cell: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: ReportSeverity
    status: ReportStatus
    agronomist_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    images: List[ReportImageResponse] = []
    ai_result: Optional[AIResultSummary] = None
    history: List[ReportHistoryResponse] = []
    created_at: datetime
    updated_at: datetime

    @field_validator("symptoms", mode="before")
    def parse_symptoms(cls, val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return [val]
        return val

    model_config = ConfigDict(from_attributes=True)
