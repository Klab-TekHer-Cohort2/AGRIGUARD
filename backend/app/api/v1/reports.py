import json
import logging
import uuid
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_current_farmer
from app.core.config import settings
from app.models.user import User, UserRole, Farmer
from app.models.crop import Crop
from app.models.report import (
    CropReport,
    ReportChannel,
    ReportSeverity,
    ReportStatus,
    ReportImage,
    ReportHistory,
)
from app.models.ai import AIResult
from app.schemas.report import (
    CropReportCreate,
    CropReportResponse,
    ReportImageResponse,
    ReportHistoryResponse,
    AIResultSummary,
)
from app.services.ai_client import process_report_ai_analysis
from app.services import report_service

logger = logging.getLogger("agriguard.reports")

router = APIRouter(prefix="/reports", tags=["Agricultural Reports"])

IMAGE_EXTENSIONS = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def format_report_response(report: CropReport) -> CropReportResponse:
    """Helper that enriches a CropReport model into a detailed response schema."""
    images = [ReportImageResponse.model_validate(img) for img in report.images]
    history = [ReportHistoryResponse.model_validate(h) for h in report.history]

    ai_summary = None
    if report.ai_result:
        ai_summary = AIResultSummary.model_validate(report.ai_result)

    return CropReportResponse(
        id=report.id,
        report_code=report.report_code,
        farmer_id=report.farmer_id,
        farmer_name=report.farmer.user.full_name if report.farmer and report.farmer.user else None,
        farmer_phone=report.farmer.user.phone_number if report.farmer and report.farmer.user else None,
        crop_id=report.crop_id,
        crop_name_en=report.crop.name_en if report.crop else None,
        crop_name_rw=report.crop.name_rw if report.crop else None,
        channel=report.channel,
        description=report.description,
        symptoms=report.symptoms or [],
        district=report.district,
        sector=report.sector,
        cell=report.cell,
        village=report.village,
        latitude=report.latitude,
        longitude=report.longitude,
        severity=report.severity,
        status=report.status,
        agronomist_notes=report.agronomist_notes,
        verified_at=report.verified_at,
        images=images,
        ai_result=ai_summary,
        history=history,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post("/", response_model=CropReportResponse, status_code=status.HTTP_201_CREATED)
def submit_crop_report(
    report_in: CropReportCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Submits a crop problem report.
    Farmers can report symptoms, describe visible damage, and specify location.
    If location is omitted, farmer's primary registered farm location is used.

    Thin wrapper over the shared ``report_service.create_crop_report`` so the
    app, USSD, and IVR flows share one concurrency-safe code path. Response
    shape and status codes are unchanged.
    """
    new_report = report_service.create_crop_report(
        db,
        current_farmer,
        crop_id=report_in.crop_id,
        channel=report_in.channel,
        description=report_in.description,
        symptoms=report_in.symptoms,
        severity=report_in.severity,
        location_override={
            "district": report_in.district,
            "sector": report_in.sector,
            "cell": report_in.cell,
            "village": report_in.village,
            "latitude": report_in.latitude,
            "longitude": report_in.longitude,
        },
        actor_user_id=current_farmer.user_id,
    )
    return format_report_response(new_report)


@router.post("/{report_id}/images", response_model=ReportImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_crop_image(
    report_id: int,
    file: UploadFile = File(...),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Uploads a crop photograph for diagnosis through image-capable channels (App/Web).
    Validates file format (JPEG, PNG, WebP) and size limit.
    """
    report = db.query(CropReport).filter(
        CropReport.id == report_id,
        CropReport.farmer_id == current_farmer.id,
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or does not belong to you.",
        )

    # Validate the untrusted MIME type and filename extension independently.
    file_ext = Path(file.filename or "").suffix.lower()
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {file.content_type}. Supported types: JPEG, PNG, WebP.",
        )
    if IMAGE_EXTENSIONS.get(file_ext) != file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image filename extension must match the supported image type.",
        )

    # Read at most one byte over the limit so oversized uploads are not buffered fully.
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size exceeds the maximum limit of {settings.MAX_IMAGE_SIZE_MB}MB.",
        )

    valid_signature = (
        (file.content_type == "image/jpeg" and content.startswith(b"\xff\xd8\xff"))
        or (file.content_type == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
        or (
            file.content_type == "image/webp"
            and len(content) >= 12
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
        )
    )
    if not valid_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image content does not match the supported image type.",
        )

    # Use a canonical extension derived from the validated content type.
    file_ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[file.content_type]
    unique_filename = f"report_{report_id}_{uuid.uuid4().hex[:10]}{file_ext}"
    dest_path = settings.upload_path / unique_filename

    # Save to disk
    with open(dest_path, "wb") as f:
        f.write(content)

    # Record in database
    image_record = ReportImage(
        report_id=report.id,
        image_url=f"/uploads/{unique_filename}",
        file_name=unique_filename,
        file_size_bytes=len(content),
        mime_type=file.content_type,
        upload_channel=report.channel.value,
    )
    db.add(image_record)

    # Log history
    history = ReportHistory(
        report_id=report.id,
        changed_by_user_id=current_farmer.user_id,
        previous_status=report.status.value,
        new_status=report.status.value,
        action_type="IMAGE_UPLOADED",
        notes=f"Crop photograph uploaded: {unique_filename}",
    )
    db.add(history)
    db.commit()
    db.refresh(image_record)

    # Automatically trigger AI image-based detection
    try:
        process_report_ai_analysis(report_id=report.id, db=db, image_path=str(dest_path))
    except Exception as exc:
        logger.warning(f"Auto AI image analysis skipped: {exc}")

    return image_record


@router.get("/my-reports", response_model=List[CropReportResponse])
def get_my_reports(
    status_filter: Optional[ReportStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Retrieves all crop problem reports submitted by the logged-in farmer.
    """
    query = db.query(CropReport).filter(CropReport.farmer_id == current_farmer.id)
    if status_filter:
        query = query.filter(CropReport.status == status_filter)

    reports = query.order_by(CropReport.created_at.desc()).offset(skip).limit(limit).all()
    return [format_report_response(r) for r in reports]


@router.get("/{report_code_or_id}", response_model=CropReportResponse)
def get_report_detail(
    report_code_or_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves detailed report information, image attachments, AI prediction,
    and verification history. Searchable by report code (e.g., AG0001) or numeric ID.
    """
    report = None
    if report_code_or_id.isdigit():
        report = db.query(CropReport).filter(CropReport.id == int(report_code_or_id)).first()

    if not report:
        report = db.query(CropReport).filter(CropReport.report_code == report_code_or_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_code_or_id}' not found.",
        )

    # Authorization: farmer can view own report; agronomists/admins can view all reports
    if current_user.role == UserRole.FARMER and current_user.farmer_profile:
        if report.farmer_id != current_user.farmer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this report.",
            )

    return format_report_response(report)


@router.get("/", response_model=List[CropReportResponse])
def list_all_reports(
    district: Optional[str] = Query(None, description="Filter by district"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    crop_id: Optional[int] = Query(None, description="Filter by crop"),
    severity: Optional[ReportSeverity] = Query(None, description="Filter by severity"),
    status: Optional[ReportStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists agricultural reports with comprehensive filters.
    Accessible to Agronomists and System Administrators.
    """
    if current_user.role not in [UserRole.AGRONOMIST, UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorized personnel.",
        )

    query = db.query(CropReport)

    if district:
        query = query.filter(CropReport.district.ilike(f"%{district}%"))
    if sector:
        query = query.filter(CropReport.sector.ilike(f"%{sector}%"))
    if crop_id:
        query = query.filter(CropReport.crop_id == crop_id)
    if severity:
        query = query.filter(CropReport.severity == severity)
    if status:
        query = query.filter(CropReport.status == status)

    reports = query.order_by(CropReport.created_at.desc()).offset(skip).limit(limit).all()
    return [format_report_response(r) for r in reports]
