"""Outbreak-risk scoring and community alert creation."""
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.neo4j_client import neo4j_client
from app.models.ai import AIResult
from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.models.location import FarmerLocation
from app.models.report import CropReport, ReportSeverity
from app.models.user import Farmer, User

logger = logging.getLogger("agriguard.outbreak_service")

_SEVERITY_WEIGHTS = {
    ReportSeverity.CRITICAL: 4,
    ReportSeverity.HIGH: 3,
    ReportSeverity.MEDIUM: 2,
    ReportSeverity.LOW: 1,
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometres."""
    earth_radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return earth_radius_km * 2 * math.asin(math.sqrt(min(1.0, value)))


def get_weather_risk_factor(district: str) -> float:
    """STUB: returns 1.0 always. Replace with real weather API (e.g., OpenWeatherMap) in a future sprint."""
    return 1.0


def _get_nearby_reports(
    db: Session,
    trigger_report: CropReport,
    pest_name_en: str,
    window_days: int = 30,
) -> List[CropReport]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    query = (
        db.query(CropReport)
        .join(AIResult, AIResult.report_id == CropReport.id)
        .filter(
            AIResult.predicted_pest_en == pest_name_en,
            CropReport.created_at >= cutoff,
            CropReport.id != trigger_report.id,
        )
    )

    if trigger_report.latitude is None or trigger_report.longitude is None:
        return query.filter(CropReport.district == trigger_report.district).all()

    radius_km = settings.OUTBREAK_RADIUS_KM
    latitude_margin = radius_km / 111.0
    longitude_margin = radius_km / (
        111.0 * max(0.001, abs(math.cos(math.radians(trigger_report.latitude))))
    )
    candidates = query.filter(
        CropReport.latitude.between(
            trigger_report.latitude - latitude_margin,
            trigger_report.latitude + latitude_margin,
        ),
        CropReport.longitude.between(
            trigger_report.longitude - longitude_margin,
            trigger_report.longitude + longitude_margin,
        ),
    ).all()

    return [
        candidate
        for candidate in candidates
        if candidate.latitude is not None
        and candidate.longitude is not None
        and _haversine(
            trigger_report.latitude,
            trigger_report.longitude,
            candidate.latitude,
            candidate.longitude,
        )
        <= radius_km
    ]


def _compute_risk_score(reports: List[CropReport]) -> float:
    if not reports:
        return 0.0

    weighted_sum = 0
    for report in reports:
        severity = report.severity or ReportSeverity.LOW
        severity_weight = _SEVERITY_WEIGHTS.get(severity, 1)
        if report.ai_result and report.ai_result.detected_severity:
            ai_weight = _SEVERITY_WEIGHTS.get(
                report.ai_result.detected_severity.upper(), 0
            )
            severity_weight = max(severity_weight, ai_weight)
        weighted_sum += severity_weight

    raw_score = weighted_sum / (len(reports) * 4)
    weather_factor = get_weather_risk_factor(reports[0].district)
    return min(1.0, max(0.0, raw_score * weather_factor))


def _map_score_to_severity(score: float) -> AlertSeverity:
    if score >= 0.8:
        return AlertSeverity.CRITICAL
    if score >= 0.6:
        return AlertSeverity.HIGH
    if score >= 0.4:
        return AlertSeverity.MEDIUM
    return AlertSeverity.INFO


def _active_alert_exists(
    db: Session,
    pest_name_en: str,
    district: str,
    cooldown_hours: int,
) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
    return (
        db.query(Alert)
        .filter(
            Alert.pest_name == pest_name_en,
            Alert.target_district == district,
            Alert.status == AlertStatus.ACTIVE,
            Alert.created_at >= cutoff,
        )
        .first()
        is not None
    )


def _enqueue_notifications(db: Session, alert: Alert, district: str) -> None:
    farmers = (
        db.query(Farmer)
        .join(Farmer.locations)
        .filter(
            FarmerLocation.district == district,
            Farmer.user.has(User.is_active.is_(True)),
        )
        .distinct()
        .all()
    )
    for farmer in farmers:
        if not farmer.user:
            continue
        use_kinyarwanda = farmer.preferred_language == "rw"
        db.add(
            Notification(
                user_id=farmer.user_id,
                alert_id=alert.id,
                channel=NotificationChannel.SMS,
                recipient_phone=farmer.user.phone_number,
                title=alert.title_rw if use_kinyarwanda else alert.title_en,
                message=alert.message_rw if use_kinyarwanda else alert.message_en,
                status=NotificationStatus.PENDING,
            )
        )


def _build_alert_messages(
    pest_name_en: str,
    pest_name_rw: str,
    severity_label: str,
    neo4j_tips: List[str],
    language: str = "rw",
    district: str = "",
    neo4j_tips_rw: Optional[List[str]] = None,
) -> Tuple[str, str, str, str]:
    """Build matching English and Kinyarwanda alert titles and messages."""
    tips_en = " ".join(str(tip) for tip in neo4j_tips[:2])
    tips_rw = " ".join(str(tip) for tip in (neo4j_tips_rw or [])[:2])
    if not tips_en:
        tips_en = "Monitor crops closely."
    if not tips_rw:
        tips_rw = "Kurikirana umurima neza."
    if language == "rw" and not neo4j_tips_rw and neo4j_tips:
        tips_rw = " ".join(str(tip) for tip in neo4j_tips[:2])

    title_en = f"Outbreak Alert: {pest_name_en} in {district}"[:128]
    title_rw = f"Impuruza: {pest_name_rw} mu {district}"[:128]
    message_en = (
        f"{severity_label} outbreak risk: multiple cases of {pest_name_en} "
        f"detected in {district}. Prevention: {tips_en}"
    )
    message_rw = (
        f"Ibyago by'icyorezo ({severity_label}): habonetse ibibazo byinshi bya "
        f"{pest_name_rw} mu karere ka {district}. Uburyo bwo kubikumira: {tips_rw}"
    )
    return title_en, title_rw, message_en, message_rw


def check_and_raise_outbreak(
    report: CropReport,
    db: Session,
) -> Optional[Alert]:
    """Create an active alert when enough nearby reports indicate an outbreak."""
    ai_result = report.ai_result
    pest_name_en = ai_result.predicted_pest_en if ai_result else None
    if not pest_name_en:
        return None

    nearby_reports = _get_nearby_reports(db, report, pest_name_en)
    if len(nearby_reports) < max(0, settings.OUTBREAK_MIN_REPORTS - 1):
        return None

    all_reports = nearby_reports + [report]
    score = _compute_risk_score(all_reports)
    if score < 0.4:
        return None

    if _active_alert_exists(
        db,
        pest_name_en,
        report.district,
        settings.ALERT_COOLDOWN_HOURS,
    ):
        logger.info(
            "Outbreak check skipped (active alert within cooldown): pest=%s district=%s",
            pest_name_en,
            report.district,
        )
        return None

    crop_name = report.crop.name_en if report.crop else "Maize"
    recommendations_en = neo4j_client.infer_pest_from_symptoms(
        crop_name, [], language="en"
    ).get("recommendations") or []
    recommendations_rw = neo4j_client.infer_pest_from_symptoms(
        crop_name, [], language="rw"
    ).get("recommendations") or []
    tips_en = " ".join(str(tip) for tip in recommendations_en[:2]) or "Monitor crops closely."
    tips_rw = " ".join(str(tip) for tip in recommendations_rw[:2]) or "Kurikirana umurima neza."
    pest_name_rw = ai_result.predicted_pest_rw or pest_name_en
    title_en, title_rw, message_en, message_rw = _build_alert_messages(
        pest_name_en=pest_name_en,
        pest_name_rw=pest_name_rw,
        severity_label=_map_score_to_severity(score).value,
        neo4j_tips=[str(tip) for tip in recommendations_en[:2]],
        district=report.district,
        neo4j_tips_rw=[str(tip) for tip in recommendations_rw[:2]],
    )

    alert = Alert(
        title_en=title_en,
        title_rw=title_rw,
        message_en=message_en,
        message_rw=message_rw,
        target_district=report.district,
        target_sector=report.sector or None,
        pest_name=pest_name_en,
        severity=_map_score_to_severity(score),
        status=AlertStatus.ACTIVE,
        source_report_id=report.id,
        affected_report_count=len(all_reports),
        crop_id=report.crop_id,
        outbreak_radius_km=settings.OUTBREAK_RADIUS_KM,
    )
    db.add(alert)
    db.flush()
    _enqueue_notifications(db, alert, report.district)
    db.commit()
    db.refresh(alert)

    logger.info(
        "Outbreak alert created: id=%s pest=%s district=%s score=%.3f reports=%d",
        alert.id,
        pest_name_en,
        report.district,
        score,
        len(all_reports),
    )
    return alert
