from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.report import CropReportResponse


class DashboardKPIs(BaseModel):
    total_farmers: int
    total_reports: int
    pending_reports: int
    ai_analyzed_reports: int
    verified_reports: int
    high_severity_cases: int
    critical_severity_cases: int
    active_alerts_count: int
    assigned_to_me: int = 0


class PestStatItem(BaseModel):
    pest_name: str
    pest_name_rw: Optional[str] = None
    crop_name: Optional[str] = None
    count: int
    percentage: float
    highest_severity: str


class LocationStatItem(BaseModel):
    district: str
    sector: Optional[str] = None
    report_count: int
    dominant_pest: Optional[str] = None


class MapPointCluster(BaseModel):
    report_id: int
    report_code: str
    crop_name: str
    predicted_pest: Optional[str] = None
    severity: str
    status: str
    latitude: float
    longitude: float
    district: str
    sector: str
    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    kpis: DashboardKPIs
    pest_statistics: List[PestStatItem]
    location_breakdown: List[LocationStatItem]
    recent_reports: List[CropReportResponse]
    active_alerts: List[Dict[str, Any]]
