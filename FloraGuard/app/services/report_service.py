"""Report management service.

Handles creation, retrieval, and validation of reports from all channels.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Report
from app.schemas.report import ReportResponse


def _validate_image(file: UploadFile) -> None:
    """Validate uploaded image file type and size."""
    if file.content_type not in settings.allowed_image_types_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed: {', '.join(settings.allowed_image_types_list)}",
        )

    # Check size by reading in chunks
    file.file.seek(0, 2)  # seek to end
    size = file.file.tell()
    file.file.seek(0)  # rewind

    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_411_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image too large: {size} bytes. "
                   f"Maximum: {settings.MAX_IMAGE_SIZE_MB} MB",
        )


def _save_upload(file: UploadFile) -> str:
    """Save uploaded file to disk and return the relative path."""
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "upload.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = settings.UPLOAD_DIR / filename

    file.file.seek(0)
    content = file.file.read()
    filepath.write_bytes(content)
    return str(filepath.relative_to(settings.BASE_DIR))


class ReportService:
    """Service for managing pest/disease reports."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_report(
        self,
        input_channel: str,
        problem_type: str,
        severity: str,
        area: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        description: Optional[str] = None,
        image_path: Optional[str] = None,
        confidence: Optional[float] = None,
        weather_temperature: Optional[float] = None,
        weather_humidity: Optional[float] = None,
    ) -> Report:
        """Create and persist a new report."""
        report = Report(
            input_channel=input_channel,
            problem_type=problem_type,
            severity=severity,
            area=area,
            latitude=latitude,
            longitude=longitude,
            description=description,
            image_path=image_path,
            confidence=confidence,
            weather_temperature=weather_temperature,
            weather_humidity=weather_humidity,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def create_smartphone_report(
        self,
        problem_type: str,
        severity: str,
        area: str,
        upload_file: Optional[UploadFile] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        description: Optional[str] = None,
        ai_confidence: Optional[float] = None,
        weather_temperature: Optional[float] = None,
        weather_humidity: Optional[float] = None,
    ) -> Report:
        """Create a smartphone report with optional image upload."""
        image_path = None
        if upload_file is not None:
            _validate_image(upload_file)
            image_path = _save_upload(upload_file)

        return self.create_report(
            input_channel="smartphone",
            problem_type=problem_type,
            severity=severity,
            area=area,
            latitude=latitude,
            longitude=longitude,
            description=description,
            image_path=image_path,
            confidence=ai_confidence,
            weather_temperature=weather_temperature,
            weather_humidity=weather_humidity,
        )

    def create_ussd_report(
        self,
        problem_type: str,
        severity: str,
        area: str,
        description: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        weather_temperature: Optional[float] = None,
        weather_humidity: Optional[float] = None,
    ) -> Report:
        """Create a USSD report. No image, no AI confidence."""
        return self.create_report(
            input_channel="ussd",
            problem_type=problem_type,
            severity=severity,
            area=area,
            latitude=latitude,
            longitude=longitude,
            description=description,
            image_path=None,
            confidence=None,
            weather_temperature=weather_temperature,
            weather_humidity=weather_humidity,
        )

    def create_ivr_report(
        self,
        problem_type: str,
        severity: str,
        area: str,
        description: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        weather_temperature: Optional[float] = None,
        weather_humidity: Optional[float] = None,
    ) -> Report:
        """Create an IVR report. No image, no AI confidence."""
        return self.create_report(
            input_channel="ivr",
            problem_type=problem_type,
            severity=severity,
            area=area,
            latitude=latitude,
            longitude=longitude,
            description=description,
            image_path=None,
            confidence=None,
            weather_temperature=weather_temperature,
            weather_humidity=weather_humidity,
        )

    def get_report(self, report_id: int) -> Optional[Report]:
        """Get a single report by ID."""
        stmt = select(Report).where(Report.id == report_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def list_reports(
        self,
        skip: int = 0,
        limit: int = 100,
        input_channel: Optional[str] = None,
        area: Optional[str] = None,
        problem_type: Optional[str] = None,
    ) -> tuple[Sequence[Report], int]:
        """List reports with optional filtering and pagination."""
        stmt = select(Report)
        count_stmt = select(func.count(Report.id))

        if input_channel:
            stmt = stmt.where(Report.input_channel == input_channel)
            count_stmt = count_stmt.where(Report.input_channel == input_channel)
        if area:
            stmt = stmt.where(Report.area == area)
            count_stmt = count_stmt.where(Report.area == area)
        if problem_type:
            stmt = stmt.where(Report.problem_type == problem_type)
            count_stmt = count_stmt.where(Report.problem_type == problem_type)

        stmt = stmt.order_by(Report.created_at.desc()).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        reports = result.scalars().all()

        count_result = self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        return reports, total

    def delete_report(self, report_id: int) -> bool:
        """Delete a report by ID."""
        report = self.get_report(report_id)
        if report is None:
            return False
        self.db.delete(report)
        self.db.commit()
        return True

    @staticmethod
    def report_to_response(report: Report) -> ReportResponse:
        """Convert a Report model to a response schema."""
        return ReportResponse(
            id=report.id,
            input_channel=report.input_channel,
            problem_type=report.problem_type,
            severity=report.severity,
            confidence=report.confidence,
            area=report.area,
            latitude=report.latitude,
            longitude=report.longitude,
            image_path=report.image_path,
            description=report.description,
            weather_temperature=report.weather_temperature,
            weather_humidity=report.weather_humidity,
            created_at=report.created_at,
        )
