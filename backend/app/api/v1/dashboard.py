from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db, get_current_user
from app.models.user import User, UserRole, Farmer
from app.models.crop import Crop
from app.models.report import (
    CropReport,
    ReportSeverity,
    ReportStatus,
)
from app.models.ai import AIResult
from app.models.alert import Alert, AlertStatus
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardKPIs,
    PestStatItem,
    LocationStatItem,
    MapPointCluster,
)
from app.api.v1.reports import format_report_response

router = APIRouter(prefix="/dashboard", tags=["Agronomist Dashboard"])


def check_dashboard_access(current_user: User):
    """Restricts dashboard access to authorized agronomists, admins, and org managers."""
    if current_user.role not in [UserRole.AGRONOMIST, UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorized agricultural personnel.",
        )


@router.get("/stats", response_model=DashboardOverviewResponse)
def get_dashboard_statistics(
    district: Optional[str] = Query(None, description="Filter by district"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    crop_id: Optional[int] = Query(None, description="Filter by crop"),
    pest_name: Optional[str] = Query(None, description="Filter by diagnosed pest name"),
    severity: Optional[ReportSeverity] = Query(None, description="Filter by severity"),
    status_filter: Optional[ReportStatus] = Query(None, description="Filter by verification status"),
    from_date: Optional[datetime] = Query(None, description="Filter reports from date"),
    to_date: Optional[datetime] = Query(None, description="Filter reports to date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Main analytics endpoint for the Agronomist Dashboard.
    Returns high-level KPIs, pest breakdown, geographic distribution,
    recent cases, and active community alerts with multi-dimensional filtering.
    """
    check_dashboard_access(current_user)

    # Base query for filtered reports
    query = db.query(CropReport)

    if district:
        query = query.filter(CropReport.district.ilike(f"%{district}%"))
    if sector:
        query = query.filter(CropReport.sector.ilike(f"%{sector}%"))
    if crop_id:
        query = query.filter(CropReport.crop_id == crop_id)
    if severity:
        query = query.filter(CropReport.severity == severity)
    if status_filter:
        query = query.filter(CropReport.status == status_filter)
    if from_date:
        query = query.filter(CropReport.created_at >= from_date)
    if to_date:
        query = query.filter(CropReport.created_at <= to_date)
    if pest_name:
        query = query.join(AIResult).filter(AIResult.predicted_pest_en.ilike(f"%{pest_name}%"))

    total_reports = query.count()

    # 1. Calculate KPIs
    total_farmers = db.query(Farmer).count()
    pending_reports = query.filter(CropReport.status == ReportStatus.PENDING).count()
    ai_analyzed_reports = query.filter(CropReport.status == ReportStatus.AI_ANALYZED).count()
    verified_reports = query.filter(CropReport.status == ReportStatus.VERIFIED).count()
    high_severity_cases = query.filter(CropReport.severity == ReportSeverity.HIGH).count()
    critical_severity_cases = query.filter(CropReport.severity == ReportSeverity.CRITICAL).count()

    # Active alerts
    alert_query = db.query(Alert).filter(Alert.status == AlertStatus.ACTIVE)
    if district:
        alert_query = alert_query.filter(Alert.target_district.ilike(f"%{district}%"))
    active_alerts_count = alert_query.count()

    assigned_to_me = 0
    if current_user.agronomist_profile:
        assigned_to_me = query.filter(
            CropReport.assigned_agronomist_id == current_user.agronomist_profile.id
        ).count()

    kpis = DashboardKPIs(
        total_farmers=total_farmers,
        total_reports=total_reports,
        pending_reports=pending_reports,
        ai_analyzed_reports=ai_analyzed_reports,
        verified_reports=verified_reports,
        high_severity_cases=high_severity_cases,
        critical_severity_cases=critical_severity_cases,
        active_alerts_count=active_alerts_count,
        assigned_to_me=assigned_to_me,
    )

    # 2. Pest and Disease Statistics
    pest_stats_query = (
        db.query(
            AIResult.predicted_pest_en,
            AIResult.predicted_pest_rw,
            func.count(AIResult.id).label("count"),
            func.max(AIResult.detected_severity).label("highest_severity"),
        )
        .join(CropReport, AIResult.report_id == CropReport.id)
    )
    if district:
        pest_stats_query = pest_stats_query.filter(CropReport.district.ilike(f"%{district}%"))
    if crop_id:
        pest_stats_query = pest_stats_query.filter(CropReport.crop_id == crop_id)

    pest_results = (
        pest_stats_query.group_by(AIResult.predicted_pest_en, AIResult.predicted_pest_rw)
        .order_by(func.count(AIResult.id).desc())
        .limit(10)
        .all()
    )

    pest_statistics = []
    for pr in pest_results:
        pct = round((pr.count / max(1, total_reports)) * 100, 1)
        pest_statistics.append(
            PestStatItem(
                pest_name=pr.predicted_pest_en,
                pest_name_rw=pr.predicted_pest_rw,
                count=pr.count,
                percentage=pct,
                highest_severity=pr.highest_severity or "MEDIUM",
            )
        )

    # 3. Location Breakdown (by District & Sector)
    location_results = (
        db.query(
            CropReport.district,
            CropReport.sector,
            func.count(CropReport.id).label("report_count"),
        )
        .group_by(CropReport.district, CropReport.sector)
        .order_by(func.count(CropReport.id).desc())
        .limit(15)
        .all()
    )

    location_breakdown = [
        LocationStatItem(
            district=lr.district,
            sector=lr.sector,
            report_count=lr.report_count,
        )
        for lr in location_results
    ]

    # 4. Recent Reports
    recent = query.order_by(CropReport.created_at.desc()).limit(10).all()
    recent_reports = [format_report_response(r) for r in recent]

    # 5. Active Alerts List
    active_alerts = [
        {
            "id": a.id,
            "title_en": a.title_en,
            "title_rw": a.title_rw,
            "target_district": a.target_district,
            "target_sector": a.target_sector,
            "severity": a.severity.value,
            "created_at": a.created_at,
        }
        for a in alert_query.limit(5).all()
    ]

    return DashboardOverviewResponse(
        kpis=kpis,
        pest_statistics=pest_statistics,
        location_breakdown=location_breakdown,
        recent_reports=recent_reports,
        active_alerts=active_alerts,
    )


@router.get("/pest-trends", response_model=List[PestStatItem])
def get_pest_trends(
    district: Optional[str] = Query(None, description="Filter by district"),
    crop_id: Optional[int] = Query(None, description="Filter by crop"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns ranked breakdown of all detected crop pests and diseases.
    """
    check_dashboard_access(current_user)

    query = (
        db.query(
            AIResult.predicted_pest_en,
            AIResult.predicted_pest_rw,
            func.count(AIResult.id).label("count"),
            func.max(AIResult.detected_severity).label("highest_severity"),
        )
        .join(CropReport, AIResult.report_id == CropReport.id)
    )

    if district:
        query = query.filter(CropReport.district.ilike(f"%{district}%"))
    if crop_id:
        query = query.filter(CropReport.crop_id == crop_id)

    total_count = query.count()
    results = (
        query.group_by(AIResult.predicted_pest_en, AIResult.predicted_pest_rw)
        .order_by(func.count(AIResult.id).desc())
        .all()
    )

    return [
        PestStatItem(
            pest_name=r.predicted_pest_en,
            pest_name_rw=r.predicted_pest_rw,
            count=r.count,
            percentage=round((r.count / max(1, total_count)) * 100, 1),
            highest_severity=r.highest_severity or "MEDIUM",
        )
        for r in results
    ]


@router.get("/map-clusters", response_model=List[MapPointCluster])
def get_map_clusters(
    district: Optional[str] = Query(None, description="Filter by district"),
    crop_id: Optional[int] = Query(None, description="Filter by crop"),
    severity: Optional[ReportSeverity] = Query(None, description="Filter by severity"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns geolocated crop report points for the Interactive Outbreak Map on the frontend.
    """
    check_dashboard_access(current_user)

    query = db.query(CropReport).filter(
        CropReport.latitude.isnot(None),
        CropReport.longitude.isnot(None),
    )

    if district:
        query = query.filter(CropReport.district.ilike(f"%{district}%"))
    if crop_id:
        query = query.filter(CropReport.crop_id == crop_id)
    if severity:
        query = query.filter(CropReport.severity == severity)

    reports = query.order_by(CropReport.created_at.desc()).limit(200).all()

    points = []
    for r in reports:
        pest = r.ai_result.predicted_pest_en if r.ai_result else None
        points.append(
            MapPointCluster(
                report_id=r.id,
                report_code=r.report_code,
                crop_name=r.crop.name_en if r.crop else "Unknown",
                predicted_pest=pest,
                severity=r.severity.value,
                status=r.status.value,
                latitude=r.latitude,
                longitude=r.longitude,
                district=r.district,
                sector=r.sector,
                created_at=r.created_at,
            )
        )
    return points
