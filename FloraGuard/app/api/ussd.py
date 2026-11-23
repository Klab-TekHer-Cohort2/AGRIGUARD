"""USSD reporting endpoint (provider-independent)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.schemas.ussd import USSDRequest, USSDResponse, USSDAction
from app.services.report_service import ReportService
from app.services.risk_engine import risk_engine
from app.services.weather_service import weather_service
from app.services.alert_service import AlertService

router = APIRouter(prefix="/api/ussd", tags=["ussd"])

PROBLEMS = ["powdery_mildew", "rust", "blight"]
SEVERITIES = ["mild", "moderate", "severe"]


def _menu(step: int, areas) -> str:
    if step == 0:
        return "Welcome to FloraGuard\n1. Report a problem\n0. Exit"
    if step == 1:
        opts = "\n".join(f"{i+1}. {p}" for i, p in enumerate(PROBLEMS))
        return f"Select problem type:\n{opts}\n0. Back"
    if step == 2:
        opts = "\n".join(f"{i+1}. {s}" for i, s in enumerate(SEVERITIES))
        return f"Select severity:\n{opts}\n0. Back"
    if step == 3:
        opts = "\n".join(f"{i+1}. {a}" for i, a in enumerate(areas))
        return f"Select area:\n{opts}\n0. Back"
    if step == 4:
        return "Confirm report?\n1. Yes\n2. No (cancel)\n0. Back"
    return "Invalid step"


@router.post("", response_model=USSDResponse)
def ussd_handler(req: USSDRequest, db: Session = Depends(get_db)):
    try:
        data = req
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    areas = settings.supported_areas_list or ["Unknown"]
    text = (req.text or "").strip()
    parts = [p for p in text.split("*") if p != ""]
    # Determine current step
    step = len(parts)
    # Exit
    if text == "0" or (parts and parts[-1] == "0" and step == 1):
        return USSDResponse(message="Thank you. Goodbye.", is_end=True)

    # Back navigation: if last part is 0 and step>1, drop last
    if parts and parts[-1] == "0" and step > 1:
        parts = parts[:-1]
        step = len(parts)
        return USSDResponse(message=_menu(step, areas), is_end=False)

    # If too many steps, treat as submit confirmation
    if step >= 4:
        # parts: problem, severity, area, confirm
        try:
            pi = int(parts[0]) - 1
            si = int(parts[1]) - 1
            ai = int(parts[2]) - 1
            confirm = parts[3]
        except (ValueError, IndexError):
            return USSDResponse(message="Invalid input. " + _menu(0, areas), is_end=True)
        if not (0 <= pi < len(PROBLEMS) and 0 <= si < len(SEVERITIES) and 0 <= ai < len(areas)):
            return USSDResponse(message="Invalid selection. " + _menu(0, areas), is_end=True)
        if confirm != "1":
            return USSDResponse(message="Report cancelled.", is_end=True)

        svc = ReportService(db)
        report = svc.create_ussd_report(
            problem_type=PROBLEMS[pi],
            severity=SEVERITIES[si],
            area=areas[ai],
        )
        # risk + alert
        all_reports, _ = svc.list_reports(area=areas[ai], problem_type=PROBLEMS[pi], limit=10000)
        assessment = risk_engine.assess(reports=all_reports, area=areas[ai], problem_type=PROBLEMS[pi])
        alerts = []
        if assessment.risk_level.value == "HIGH":
            a = AlertService(db).create_alert(
                problem_type=PROBLEMS[pi],
                area=areas[ai],
                risk_level=assessment.risk_level.value,
                risk_score=assessment.risk_score,
                reasons=assessment.reasons,
            )
            if a is not None:
                alerts.append(AlertService.alert_to_response(a))
        return USSDResponse(message="Report submitted successfully.", is_end=True, report_id=report.id, alerts=alerts)

    # Otherwise show next menu
    # validate current last input if any
    if step > 0:
        last = parts[-1]
        idx = step - 1
        if idx == 0:
            if not (last.isdigit() and 1 <= int(last) <= len(PROBLEMS)):
                return USSDResponse(message="Invalid problem selection.\n" + _menu(0, areas), is_end=True)
        elif idx == 1:
            if not (last.isdigit() and 1 <= int(last) <= len(SEVERITIES)):
                return USSDResponse(message="Invalid severity.\n" + _menu(1, areas), is_end=True)
        elif idx == 2:
            if not (last.isdigit() and 1 <= int(last) <= len(areas)):
                return USSDResponse(message="Invalid area.\n" + _menu(2, areas), is_end=True)

    return USSDResponse(message=_menu(step, areas), is_end=False)
