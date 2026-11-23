"""Map reports aggregation endpoint."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.schemas.map import AreaRiskSummary, MapReportsResponse, RiskLevel
from app.services.report_service import ReportService
from app.services.risk_engine import risk_engine

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get("/reports", response_model=MapReportsResponse)
def map_reports(db: Session = Depends(get_db)):
    svc = ReportService(db)
    reports, _ = svc.list_reports(limit=100000)
    by_area = {}
    for r in reports:
        by_area.setdefault(r.area, []).append(r)

    summaries = []
    for area, reps in by_area.items():
        sev = Counter((r.severity or "").lower() for r in reps)
        problems = Counter(r.problem_type for r in reps)
        dominant = problems.most_common(1)[0][0] if problems else None
        assessment = risk_engine.assess(reports=reps, area=area)
        summaries.append(AreaRiskSummary(
            area=area,
            total_reports=len(reps),
            high_risk_count=sev.get("severe", 0),
            moderate_risk_count=sev.get("moderate", 0),
            mild_risk_count=sev.get("mild", 0),
            dominant_problem=dominant,
            latest_risk_level=RiskLevel(assessment.risk_level.value) if assessment.risk_level.value in ("LOW", "MEDIUM", "HIGH") else None,
            latest_risk_score=assessment.risk_score,
        ))
    return MapReportsResponse(areas=summaries, generated_at=datetime.now(timezone.utc))
