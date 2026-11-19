import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.report import ReportSeverity, ReportStatus


class AgronomistProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    qualification: Optional[str] = None
    assigned_districts: Optional[List[str]] = None
    assigned_sectors: Optional[List[str]] = None


class AgronomistProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone_number: str
    email: Optional[str] = None
    license_number: Optional[str] = None
    qualification: Optional[str] = None
    assigned_districts: List[str] = []
    assigned_sectors: List[str] = []
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    @field_validator("assigned_districts", mode="before")
    def parse_districts(cls, val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return [d.strip() for d in val.split(",") if d.strip()]
        return val or []

    @field_validator("assigned_sectors", mode="before")
    def parse_sectors(cls, val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return [s.strip() for s in val.split(",") if s.strip()]
        return val or []

    model_config = ConfigDict(from_attributes=True)


class ReportVerificationRequest(BaseModel):
    is_ai_correct: bool = Field(True, description="Whether the AI prediction was confirmed accurate")
    verified_pest_name: Optional[str] = Field(None, description="Ground truth pest/disease name if corrected")
    verified_severity: Optional[ReportSeverity] = Field(None, description="Agronomist confirmed severity level")
    verification_notes: str = Field(..., min_length=3, description="Agronomist field observations and diagnosis")
    agronomist_recommendations: List[str] = Field(default_factory=list, description="Prescribed chemical or cultural actions")
    status: ReportStatus = Field(ReportStatus.VERIFIED, description="VERIFIED or REJECTED")


class ReportAssignmentRequest(BaseModel):
    agronomist_id: int = Field(..., description="ID of the agronomist to assign the report to")
