"""Shared, concurrency-safe crop-report creation service.

Used by the app POST ``/reports/`` (``app/api/v1/reports.py``) and by the USSD
and IVR flows. Service logic lives in the services layer (matching
``ai_client.py``); the USSD/IVR flows must not import from an API router module.

Concurrency safety (finding #3): the ``report_code`` race (two sessions read
the same count, compute the same code, the second commit hits the UNIQUE
constraint) is fixed by catching ``IntegrityError`` on ``db.flush()`` *inside a
SAVEPOINT* (``with db.begin_nested():``). The context manager rolls back the
SAVEPOINT only — the candidate insert is discarded, but the outer transaction
(including any pending ``USSDSession``/``IVRSession`` row added earlier in the
turn) is preserved. The next attempt regenerates with a 6-hex random suffix.
The first attempt keeps the clean ``AG####`` shape so existing
``report_code.startswith("AG")`` assertions still hold.

Location fallback (finding #5): the rule is identical to the original
``submit_crop_report`` — falsy ``district`` triggers a single all-or-nothing
fallback to the farmer's primary location (district/sector/cell/village/
latitude/longitude TOGETHER), then to ``("Musanze","Muhoza")`` only when no
primary location exists. It is NOT a per-field cascade, so the existing app
report test (no location -> Musanze/Muhoza) stays green.
"""
import json
import logging
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.crop import Crop
from app.models.report import (
    CropReport,
    ReportChannel,
    ReportSeverity,
    ReportStatus,
    ReportHistory,
)
from app.services.ai_client import process_report_ai_analysis

logger = logging.getLogger("agriguard.report_service")


def create_crop_report(
    db: Session,
    farmer,
    *,
    crop_id: int,
    channel: ReportChannel,
    description: Optional[str] = None,
    symptoms: Optional[List[str]] = None,
    severity: ReportSeverity = ReportSeverity.LOW,
    location_override: Optional[dict] = None,
    actor_user_id: Optional[int] = None,
) -> CropReport:
    """Create a CropReport with a SAVEPOINT-scoped concurrency-safe report_code.

    Behavior mirrors the original ``submit_crop_report`` exactly (location
    fallback, history row, auto AI analysis when symptoms are non-empty).
    """
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Crop with ID {crop_id} does not exist.",
        )

    # Location fallback — EXACT rule mirroring reports.py (finding #5):
    # if location_override is None OR location_override['district'] is falsy,
    # fall back to the farmer's primary location (all six fields TOGETHER),
    # then to ("Musanze","Muhoza") only when no primary location exists.
    district = location_override.get("district") if location_override else None
    sector = location_override.get("sector") if location_override else None
    cell = location_override.get("cell") if location_override else None
    village = location_override.get("village") if location_override else None
    latitude = location_override.get("latitude") if location_override else None
    longitude = location_override.get("longitude") if location_override else None

    if not district:  # falsy district -> all-or-nothing fallback
        primary_loc = next((loc for loc in farmer.locations if loc.is_primary), None)
        if not primary_loc and farmer.locations:
            primary_loc = farmer.locations[0]
        if primary_loc:
            district = primary_loc.district
            sector = primary_loc.sector
            cell = primary_loc.cell
            village = primary_loc.village
            latitude = primary_loc.latitude
            longitude = primary_loc.longitude
        else:
            district, sector = "Musanze", "Muhoza"

    symptoms_val = json.dumps(symptoms or [])
    base = f"AG{db.query(CropReport).count() + 1:04d}"
    report = None
    for attempt in range(6):  # concurrency-safe code generation
        code = base if attempt == 0 else f"{base}-{uuid.uuid4().hex[:6].upper()}"
        candidate = CropReport(
            report_code=code,
            farmer_id=farmer.id,
            crop_id=crop.id,
            channel=channel,
            description=description,
            symptoms=symptoms_val,
            district=district,
            sector=sector,
            cell=cell,
            village=village,
            latitude=latitude,
            longitude=longitude,
            severity=severity,
            status=ReportStatus.PENDING,
        )
        try:
            with db.begin_nested():  # SAVEPOINT (finding #3)
                db.add(candidate)
                db.flush()  # forces UNIQUE check inside the savepoint
            report = candidate  # savepoint released (committed into outer txn)
            break
        except IntegrityError:
            # begin_nested() context manager already rolled back the SAVEPOINT only;
            # the outer transaction + any pending session row are intact.
            if attempt == 5:
                raise
            continue  # regenerate with a random suffix

    db.add(
        ReportHistory(
            report_id=report.id,
            changed_by_user_id=actor_user_id,
            previous_status=None,
            new_status=ReportStatus.PENDING.value,
            action_type="REPORT_CREATED",
            notes=f"Report created via {channel.value}.",
        )
    )
    db.commit()
    db.refresh(report)

    # auto AI + notification, exactly like the app flow (AI triggers when
    # symptoms are non-empty, producing an AIResult and a PENDING Notification).
    if symptoms:
        try:
            process_report_ai_analysis(report_id=report.id, db=db)
            db.refresh(report)
        except Exception as exc:
            logger.warning(f"Auto AI analysis skipped: {exc}")
    else:
        try:
            from app.services.outbreak_service import check_and_raise_outbreak

            check_and_raise_outbreak(report, db)
        except Exception as exc:
            logger.warning(
                "Outbreak check failed in report_service (report_id=%s): %r",
                report.id,
                exc,
            )
    return report
