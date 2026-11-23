"""Report API endpoints (Phase 1)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Report, RiskAssessment, WeatherObservation
from app.schemas.report import ReportResponse
from app.services.alert_service import AlertService
from app.services.report_service import ReportService
from app.services.risk_engine import risk_engine
from app.services.weather_service import weather_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _service(db: Session) -> ReportService:
    return ReportService(db)


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    input_channel: str = Form(...),
    problem_type: str = Form(...),
    severity: str = Form(...),
    area: str = Form(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    ai_confidence: Optional[float] = Form(None),
    weather_temperature: Optional[float] = Form(None),
    weather_humidity: Optional[float] = Form(None),
    upload_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    svc = _service(db)
    try:
        if input_channel == "smartphone":
            report = svc.create_smartphone_report(
                problem_type=problem_type,
                severity=severity,
                area=area,
                upload_file=upload_file,
                latitude=latitude,
                longitude=longitude,
                description=description,
                ai_confidence=ai_confidence,
                weather_temperature=weather_temperature,
                weather_humidity=weather_humidity,
            )
        elif input_channel == "ussd":
            report = svc.create_ussd_report(
                problem_type=problem_type,
                severity=severity,
                area=area,
                description=description,
                latitude=latitude,
                longitude=longitude,
                weather_temperature=weather_temperature,
                weather_humidity=weather_humidity,
            )
        elif input_channel == "ivr":
            report = svc.create_ivr_report(
                problem_type=problem_type,
                severity=severity,
                area=area,
                description=description,
                latitude=latitude,
                longitude=longitude,
                weather_temperature=weather_temperature,
                weather_humidity=weather_humidity,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown input_channel: {input_channel}")
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Post-save risk assessment and alert generation
    all_reports, _ = svc.list_reports(area=area, problem_type=problem_type, limit=10000)
    weather = None
    if latitude is not None and longitude is not None:
        weather = weather_service.fetch_weather(latitude, longitude)
    assessment = risk_engine.assess(
        reports=all_reports,
        area=area,
        problem_type=problem_type,
        weather=weather,
    )
    if assessment.risk_level.value == "HIGH":
        AlertService(db).create_alert(
            problem_type=problem_type,
            area=area,
            risk_level=assessment.risk_level.value,
            risk_score=assessment.risk_score,
            reasons=assessment.reasons,
        )

    # Persist risk assessment
    ra = RiskAssessment(
        area=area,
        problem_type=problem_type,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level.value,
        contributing_report_count=assessment.contributing_report_count,
        reasons="\n".join(assessment.reasons),
        weather_temperature=assessment.weather_temperature,
        weather_humidity=assessment.weather_humidity,
        weather_available=assessment.weather_available,
    )
    db.add(ra)
    db.commit()

    # Persist weather observation if available
    if weather is not None and weather.available and weather.is_valid and latitude is not None and longitude is not None:
        wo = WeatherObservation(
            latitude=latitude,
            longitude=longitude,
            temperature=weather.temperature,
            humidity=weather.humidity,
            source=weather.source,
        )
        db.add(wo)
        db.commit()

    return ReportService.report_to_response(report)


@router.get("", response_model=dict)
def list_reports(
    skip: int = 0,
    limit: int = 100,
    input_channel: Optional[str] = None,
    area: Optional[str] = None,
    problem_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    svc = _service(db)
    reports, total = svc.list_reports(
        skip=skip, limit=limit, input_channel=input_channel, area=area, problem_type=problem_type
    )
    return {"total": total, "reports": [ReportService.report_to_response(r).model_dump() for r in reports]}


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    svc = _service(db)
    report = svc.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportService.report_to_response(report)
