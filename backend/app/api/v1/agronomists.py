import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_current_agronomist
from app.models.user import User, UserRole, Agronomist, Organization
from app.models.report import CropReport, ReportStatus, ReportSeverity, ReportHistory
from app.models.ai import AIResult
from app.models.alert import Notification, NotificationChannel, NotificationStatus
from app.schemas.agronomist import (
    AgronomistProfileResponse,
    AgronomistProfileUpdate,
    ReportVerificationRequest,
    ReportAssignmentRequest,
)
from app.schemas.report import CropReportResponse
from app.api.v1.reports import format_report_response

router = APIRouter(prefix="/agronomists", tags=["Agronomists"])


def format_agronomist_profile(agronomist: Agronomist) -> AgronomistProfileResponse:
    """Helper to convert Agronomist model to response schema."""
    org_name = agronomist.organization.name if agronomist.organization else None
    districts = []
    sectors = []

    if agronomist.assigned_districts:
        try:
            districts = json.loads(agronomist.assigned_districts)
        except Exception:
            districts = [d.strip() for d in agronomist.assigned_districts.split(",") if d.strip()]

    if agronomist.assigned_sectors:
        try:
            sectors = json.loads(agronomist.assigned_sectors)
        except Exception:
            sectors = [s.strip() for s in agronomist.assigned_sectors.split(",") if s.strip()]

    return AgronomistProfileResponse(
        id=agronomist.id,
        user_id=agronomist.user_id,
        full_name=agronomist.user.full_name,
        phone_number=agronomist.user.phone_number,
        email=agronomist.user.email,
        license_number=agronomist.license_number,
        qualification=agronomist.qualification,
        assigned_districts=districts,
        assigned_sectors=sectors,
        organization_id=agronomist.organization_id,
        organization_name=org_name,
        is_active=agronomist.is_active,
        created_at=agronomist.created_at,
    )


@router.get("/profile", response_model=AgronomistProfileResponse)
def get_my_agronomist_profile(
    current_agronomist: Agronomist = Depends(get_current_agronomist),
):
    """
    Retrieves profile, license details, and assigned geographic zones of the logged-in agronomist.
    """
    return format_agronomist_profile(current_agronomist)


@router.put("/profile", response_model=AgronomistProfileResponse)
def update_agronomist_profile(
    profile_in: AgronomistProfileUpdate,
    current_agronomist: Agronomist = Depends(get_current_agronomist),
    db: Session = Depends(get_db),
):
    """
    Updates agronomist qualification and assigned operational districts/sectors.
    """
    if profile_in.full_name is not None:
        current_agronomist.user.full_name = profile_in.full_name
    if profile_in.qualification is not None:
        current_agronomist.qualification = profile_in.qualification
    if profile_in.assigned_districts is not None:
        current_agronomist.assigned_districts = json.dumps(profile_in.assigned_districts)
    if profile_in.assigned_sectors is not None:
        current_agronomist.assigned_sectors = json.dumps(profile_in.assigned_sectors)

    db.commit()
    db.refresh(current_agronomist)
    return format_agronomist_profile(current_agronomist)


@router.get("/assigned-reports", response_model=List[CropReportResponse])
def get_assigned_reports(
    status_filter: Optional[ReportStatus] = Query(None, description="Filter by report status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_agronomist: Agronomist = Depends(get_current_agronomist),
    db: Session = Depends(get_db),
):
    """
    Retrieves reports assigned directly to this agronomist or matching their assigned districts.
    """
    # Parse assigned districts
    assigned_districts = []
    if current_agronomist.assigned_districts:
        try:
            assigned_districts = json.loads(current_agronomist.assigned_districts)
        except Exception:
            assigned_districts = [d.strip() for d in current_agronomist.assigned_districts.split(",")]

    query = db.query(CropReport).filter(
        (CropReport.assigned_agronomist_id == current_agronomist.id) |
        (CropReport.district.in_(assigned_districts))
    )

    if status_filter:
        query = query.filter(CropReport.status == status_filter)

    reports = query.order_by(CropReport.created_at.desc()).offset(skip).limit(limit).all()
    return [format_report_response(r) for r in reports]


@router.post("/reports/{report_id}/assign", response_model=CropReportResponse)
def assign_report_to_agronomist(
    report_id: int,
    assign_in: ReportAssignmentRequest,
    current_agronomist: Agronomist = Depends(get_current_agronomist),
    db: Session = Depends(get_db),
):
    """
    Assigns a crop report to a designated agronomist for field investigation.
    """
    report = db.query(CropReport).filter(CropReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    target_agronomist = db.query(Agronomist).filter(Agronomist.id == assign_in.agronomist_id).first()
    if not target_agronomist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target agronomist not found.")

    report.assigned_agronomist_id = target_agronomist.id
    report.status = ReportStatus.UNDER_REVIEW

    # Log assignment history
    history = ReportHistory(
        report_id=report.id,
        changed_by_user_id=current_agronomist.user_id,
        previous_status=report.status.value,
        new_status=ReportStatus.UNDER_REVIEW.value,
        action_type="REPORT_ASSIGNED",
        notes=f"Report assigned to Agronomist {target_agronomist.user.full_name}.",
    )
    db.add(history)
    db.commit()
    db.refresh(report)

    return format_report_response(report)


@router.post("/reports/{report_id}/verify", response_model=CropReportResponse)
def verify_crop_report(
    report_id: int,
    verification: ReportVerificationRequest,
    current_agronomist: Agronomist = Depends(get_current_agronomist),
    db: Session = Depends(get_db),
):
    """
    Ground-Truth Verification Workflow:
    Agronomist validates or corrects the AI prediction, prescribes chemical or
    biological recommendations, and updates the report status.
    """
    report = db.query(CropReport).filter(CropReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    previous_status = report.status.value
    report.status = verification.status
    report.verified_at = datetime.now(timezone.utc)
    report.assigned_agronomist_id = current_agronomist.id

    combined_notes = verification.verification_notes
    if verification.agronomist_recommendations:
        recs_str = "; ".join(verification.agronomist_recommendations)
        combined_notes += f" | Inama z'Umwunganizi: {recs_str}"

    report.agronomist_notes = combined_notes

    if verification.verified_severity:
        report.severity = verification.verified_severity

    # Update AI result ground-truth feedback
    if report.ai_result:
        report.ai_result.is_verified_correct = verification.is_ai_correct
        if not verification.is_ai_correct and verification.verified_pest_name:
            # Document ground truth correction in AI result
            report.ai_result.raw_response = json.dumps({
                "corrected_by_agronomist": current_agronomist.user.full_name,
                "ground_truth_label": verification.verified_pest_name,
                "original_ai_prediction": report.ai_result.predicted_pest_en,
            })

    # Record verification history
    history = ReportHistory(
        report_id=report.id,
        changed_by_user_id=current_agronomist.user_id,
        previous_status=previous_status,
        new_status=verification.status.value,
        action_type="AGRONOMIST_VERIFIED",
        notes=(
            f"Verified by {current_agronomist.user.full_name}: "
            f"{'AI prediction CONFIRMED' if verification.is_ai_correct else 'AI prediction CORRECTED to ' + str(verification.verified_pest_name)}. "
            f"Notes: {verification.verification_notes}"
        ),
    )
    db.add(history)

    # Notify the farmer of agronomist verification
    if report.farmer and report.farmer.user:
        lang = report.farmer.preferred_language
        if lang == "rw":
            msg = (
                f"AgriGuard: Umwunganizi mu buhinzi {current_agronomist.user.full_name} "
                f"yasuzumye raporo yawe {report.report_code}. "
                f"Inama: {verification.verification_notes[:100]}"
            )
        else:
            msg = (
                f"AgriGuard: Agronomist {current_agronomist.user.full_name} "
                f"has verified report {report.report_code}. "
                f"Guidance: {verification.verification_notes[:100]}"
            )

        notif = Notification(
            user_id=report.farmer.user.id,
            report_id=report.id,
            channel=NotificationChannel.SMS,
            recipient_phone=report.farmer.user.phone_number,
            title="Agronomist Verification",
            message=msg,
            status=NotificationStatus.PENDING,
        )
        db.add(notif)

    db.commit()
    db.refresh(report)
    return format_report_response(report)


@router.get("/", response_model=List[AgronomistProfileResponse])
def list_agronomists(
    district: Optional[str] = Query(None, description="Filter by operational district"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists agronomists with optional geographic or organizational filters.
    """
    query = db.query(Agronomist).filter(Agronomist.is_active == True)
    if organization_id:
        query = query.filter(Agronomist.organization_id == organization_id)
    if district:
        query = query.filter(Agronomist.assigned_districts.ilike(f"%{district}%"))

    agronomists = query.all()
    return [format_agronomist_profile(a) for a in agronomists]
