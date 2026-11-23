"""IVR reporting endpoint (provider-independent)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.schemas.ivr import IVRRequest, IVRResponse, IVRCallStatus
from app.services.report_service import ReportService
from app.services.risk_engine import risk_engine
from app.services.weather_service import weather_service
from app.services.alert_service import AlertService

router = APIRouter(prefix="/api/ivr", tags=["ivr"])


@router.post("", response_model=IVRResponse)
def ivr_handler(req: IVRRequest, db: Session = Depends(get_db)):
    if req.status in (IVRCallStatus.STARTED, IVRCallStatus.COLLECTING):
        return IVRResponse(message="Collecting report information. Please provide problem, severity, and area.", status=req.status, is_end=False)

    if req.status == IVRCallStatus.CANCELLED:
        return IVRResponse(message="Call cancelled. No report saved.", status=req.status, is_end=True)

    if req.status in (IVRCallStatus.CONFIRMED, IVRCallStatus.COMPLETED):
        if not (req.problem_type and req.severity and req.area):
            raise HTTPException(status_code=422, detail="Missing report fields")
        if not req.confirmed:
            return IVRResponse(message="Please confirm the report.", status=IVRCallStatus.COLLECTING, is_end=False)

        svc = ReportService(db)
        report = svc.create_ivr_report(
            problem_type=req.problem_type,
            severity=req.severity.value,
            area=req.area,
        )
        all_reports, _ = svc.list_reports(area=req.area, problem_type=req.problem_type, limit=10000)
        assessment = risk_engine.assess(reports=all_reports, area=req.area, problem_type=req.problem_type)
        alerts = []
        if assessment.risk_level.value == "HIGH":
            a = AlertService(db).create_alert(
                problem_type=req.problem_type,
                area=req.area,
                risk_level=assessment.risk_level.value,
                risk_score=assessment.risk_score,
                reasons=assessment.reasons,
            )
            if a is not None:
                alerts.append(AlertService.alert_to_response(a))
        return IVRResponse(message="Report saved successfully.", status=IVRCallStatus.COMPLETED, is_end=True, report_id=report.id, alerts=alerts)

    raise HTTPException(status_code=400, detail="Unsupported IVR status")
