"""Alert API endpoints (Phase 2)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.alert import AlertResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    area: Optional[str] = Query(None),
    problem_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    svc = AlertService(db)
    alerts, total = svc.list_alerts(skip=skip, limit=limit, area=area, problem_type=problem_type)
    return {"total": total, "alerts": [AlertService.alert_to_response(a).model_dump() for a in alerts]}
