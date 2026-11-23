"""Alert generation service for FloraGuard.

Generates and persists alerts for HIGH-risk conditions. No SMS provider is
assumed to be configured, so delivery status is recorded as SKIPPED rather
than claiming a message was sent.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Alert
from app.schemas.alert import AlertResponse, AlertStatus

logger = logging.getLogger(__name__)

DEDUP_WINDOW_HOURS = 24


def _preventive_guidance(problem_type: Optional[str]) -> str:
    base = (
        "Inspect affected plants regularly, remove visibly infected material, "
        "improve airflow and spacing, and avoid working in fields when wet. "
        "Consult a local agricultural extension officer before applying any treatment."
    )
    if problem_type:
        return f"Problem: {problem_type}. {base}"
    return base


class AlertService:
    """Service for generating and storing alerts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _has_recent_alert(self, problem_type: str, area: str) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=DEDUP_WINDOW_HOURS)
        stmt = select(Alert).where(
            Alert.problem_type == problem_type,
            Alert.area == area,
            Alert.risk_level == "HIGH",
            Alert.created_at >= cutoff,
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    def create_alert(
        self,
        problem_type: str,
        area: str,
        risk_level: str,
        risk_score: float,
        reasons: list[str],
        preventive_guidance: Optional[str] = None,
    ) -> Optional[Alert]:
        """Create and store an alert if not a duplicate. Returns None if skipped."""
        if risk_level != "HIGH":
            return None

        if self._has_recent_alert(problem_type, area):
            logger.info("Duplicate high-risk alert suppressed for %s / %s", problem_type, area)
            return None

        guidance = preventive_guidance or _preventive_guidance(problem_type)

        # No SMS provider configured -> do not claim delivery
        delivery_status = AlertStatus.SKIPPED.value
        if settings.SMS_PROVIDER:
            delivery_status = AlertStatus.PENDING.value

        alert = Alert(
            problem_type=problem_type,
            area=area,
            risk_level=risk_level,
            risk_score=risk_score,
            reasons="\n".join(reasons),
            preventive_guidance=guidance,
            delivery_status=delivery_status,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_alerts(
        self,
        skip: int = 0,
        limit: int = 100,
        area: Optional[str] = None,
        problem_type: Optional[str] = None,
    ) -> tuple[list[Alert], int]:
        from sqlalchemy import func, select

        stmt = select(Alert)
        count_stmt = select(func.count(Alert.id))
        if area:
            stmt = stmt.where(Alert.area == area)
            count_stmt = count_stmt.where(Alert.area == area)
        if problem_type:
            stmt = stmt.where(Alert.problem_type == problem_type)
            count_stmt = count_stmt.where(Alert.problem_type == problem_type)
        stmt = stmt.order_by(Alert.created_at.desc()).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        alerts = list(result.scalars().all())
        total = self.db.execute(count_stmt).scalar() or 0
        return alerts, int(total)
    @staticmethod
    def alert_to_response(alert: Alert) -> "AlertResponse":
        from app.schemas.alert import AlertResponse

        reasons = [r for r in (alert.reasons or "").split("\n") if r.strip()]
        return AlertResponse(
            id=alert.id,
            problem_type=alert.problem_type,
            area=alert.area,
            risk_level=alert.risk_level,
            risk_score=alert.risk_score,
            reasons=reasons,
            preventive_guidance=alert.preventive_guidance or "",
            delivery_status=alert.delivery_status,
            created_at=alert.created_at,
        )
