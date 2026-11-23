"""Risk assessment API endpoints (Phase 2)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.risk import RiskAssessmentResponse
from app.services.report_service import ReportService
from app.services.risk_engine import risk_engine
from app.services.weather_service import weather_service

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("", response_model=RiskAssessmentResponse)
def assess_risk(
    area: Optional[str] = Query(None),
    problem_type: Optional[str] = Query(None),
    window_hours: Optional[int] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    svc = ReportService(db)
    reports, _ = svc.list_reports(area=area, problem_type=problem_type, limit=10000)

    weather = None
    if latitude is not None and longitude is not None:
        weather = weather_service.fetch_weather(latitude, longitude)

    result = risk_engine.assess(
        reports=reports,
        area=area,
        problem_type=problem_type,
        window_hours=window_hours,
        weather=weather,
    )
    return result
