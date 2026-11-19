"""Outbreak alert management and risk scoring endpoints."""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.ai import AIResult
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.report import CropReport
from app.models.user import User, UserRole
from app.schemas.outbreak import (
    AlertDetailResponse,
    AlertResponse,
    OutbreakCheckRequest,
    RiskScoreResponse,
)
from app.services.outbreak_service import (
    _compute_risk_score,
    check_and_raise_outbreak,
)

logger = logging.getLogger("agriguard.outbreak_api")
router = APIRouter(prefix="/outbreak", tags=["Outbreak & Alerts"])

_STAFF_ROLES = {UserRole.AGRONOMIST, UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN}
_RESOLVER_ROLES = {UserRole.AGRONOMIST, UserRole.SYSTEM_ADMIN}


def _require_staff(current_user: User) -> None:
    if current_user.role not in _STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required.",
        )


def _require_resolver(current_user: User) -> None:
    if current_user.role not in _RESOLVER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agronomist or system administrator access required.",
        )


@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(
    district: Optional[str] = Query(None, max_length=64),
    pest_name: Optional[str] = Query(None, max_length=128),
    severity: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_staff(current_user)
    query = db.query(Alert)
    if district:
        query = query.filter(Alert.target_district.ilike(f"%{district}%"))
    if pest_name:
        query = query.filter(Alert.pest_name.ilike(f"%{pest_name}%"))
    if severity:
        try:
            query = query.filter(Alert.severity == AlertSeverity(severity))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid severity: {severity}",
            ) from exc
    if status_filter:
        try:
            query = query.filter(Alert.status == AlertStatus(status_filter))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {status_filter}",
            ) from exc

    alerts = (
        query.order_by(Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [AlertResponse.model_validate(alert) for alert in alerts]


@router.get("/alerts/{alert_id}", response_model=AlertDetailResponse)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_staff(current_user)
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found.",
        )
    return AlertDetailResponse.model_validate(alert)


@router.post("/alerts/{alert_id}/resolve", response_model=AlertDetailResponse)
def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_resolver(current_user)
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found.",
        )
    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is already resolved.",
        )

    alert.status = AlertStatus.RESOLVED
    alert.resolved_by_user_id = current_user.id
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return AlertDetailResponse.model_validate(alert)


@router.get("/risk-score", response_model=RiskScoreResponse)
def get_risk_score(
    district: str = Query(..., max_length=64),
    pest_name: Optional[str] = Query(None, max_length=128),
    crop_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_staff(current_user)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    query = db.query(CropReport).filter(
        CropReport.district == district,
        CropReport.created_at >= cutoff,
    )
    if crop_id is not None:
        query = query.filter(CropReport.crop_id == crop_id)
    if pest_name:
        query = query.join(
            AIResult,
            AIResult.report_id == CropReport.id,
        ).filter(AIResult.predicted_pest_en == pest_name)

    reports = query.all()
    score = _compute_risk_score(reports)
    return RiskScoreResponse(
        district=district,
        pest_name=pest_name,
        crop_id=crop_id,
        risk_score=round(score, 4),
        contributing_report_count=len(reports),
        threshold=0.4,
        above_threshold=score >= 0.4,
    )


@router.post("/check")
def trigger_outbreak_check(
    body: OutbreakCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_resolver(current_user)
    report = db.query(CropReport).filter(CropReport.id == body.report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {body.report_id} not found.",
        )
    try:
        alert = check_and_raise_outbreak(report, db)
    except Exception as exc:
        logger.exception("Manual outbreak check failed for report_id=%s", body.report_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Outbreak check failed.",
        ) from exc
    return {
        "report_id": report.id,
        "alert_created": alert is not None,
        "alert_id": alert.id if alert else None,
        "message": "Outbreak check completed.",
    }
