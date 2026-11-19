import enum
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class ReportChannel(str, enum.Enum):
    USSD = "USSD"
    IVR = "IVR"
    APP = "APP"
    WEB = "WEB"
    SMS = "SMS"


class ReportSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    AI_ANALYZED = "AI_ANALYZED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"


class CropReport(Base, TimestampMixin):
    __tablename__ = "crop_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_code = Column(String(32), unique=True, index=True, nullable=False)  # e.g., 'AG001'
    
    # Foreign Keys
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_agronomist_id = Column(Integer, ForeignKey("agronomists.id", ondelete="SET NULL"), nullable=True, index=True)

    # Submission Metadata
    channel = Column(Enum(ReportChannel), default=ReportChannel.APP, nullable=False)
    description = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)  # JSON-encoded array of symptom strings
    
    # Location Snapshot at time of reporting
    district = Column(String(64), nullable=False, index=True)
    sector = Column(String(64), nullable=False, index=True)
    cell = Column(String(64), nullable=True)
    village = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Triage and Verification
    severity = Column(Enum(ReportSeverity), default=ReportSeverity.LOW, nullable=False, index=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False, index=True)
    agronomist_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    farmer = relationship("Farmer", back_populates="crop_reports")
    crop = relationship("Crop", back_populates="reports")
    assigned_agronomist = relationship("Agronomist", back_populates="assigned_reports")
    images = relationship("ReportImage", back_populates="report", cascade="all, delete-orphan")
    ai_result = relationship("AIResult", back_populates="report", uselist=False, cascade="all, delete-orphan")
    history = relationship("ReportHistory", back_populates="report", cascade="all, delete-orphan", order_by="desc(ReportHistory.created_at)")


class ReportImage(Base, TimestampMixin):
    __tablename__ = "report_images"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("crop_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String(255), nullable=False)
    file_name = Column(String(128), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(64), default="image/jpeg", nullable=False)
    upload_channel = Column(String(32), default="APP", nullable=False)

    # Relationship
    report = relationship("CropReport", back_populates="images")


class ReportHistory(Base):
    __tablename__ = "report_history"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("crop_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    action_type = Column(String(64), nullable=False)  # e.g., 'CREATED', 'AI_PROCESSED', 'AGRONOMIST_VERIFIED'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    report = relationship("CropReport", back_populates="history")
