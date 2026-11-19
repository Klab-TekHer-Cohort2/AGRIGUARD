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
from app.models.base import TimestampMixin


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


class NotificationChannel(str, enum.Enum):
    SMS = "SMS"
    IN_APP = "IN_APP"
    USSD = "USSD"
    IVR = "IVR"


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    READ = "READ"


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title_en = Column(String(128), nullable=False)
    title_rw = Column(String(128), nullable=False)
    message_en = Column(Text, nullable=False)
    message_rw = Column(Text, nullable=False)
    
    # Geographic Scope & Target
    crop_id = Column(Integer, ForeignKey("crops.id", ondelete="SET NULL"), nullable=True, index=True)
    target_district = Column(String(64), nullable=False, index=True)
    target_sector = Column(String(64), nullable=True, index=True)
    outbreak_radius_km = Column(Float, default=10.0, nullable=False)
    
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False, index=True)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Outbreak-engine columns
    pest_name = Column(String(128), nullable=True, index=True)
    source_report_id = Column(Integer, ForeignKey("crop_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    affected_report_count = Column(Integer, default=1, nullable=False)
    resolved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    crop = relationship("Crop", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")
    source_report = relationship("CropReport", foreign_keys=[source_report_id])


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True, index=True)
    report_id = Column(Integer, ForeignKey("crop_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    
    channel = Column(Enum(NotificationChannel), default=NotificationChannel.SMS, nullable=False)
    recipient_phone = Column(String(32), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    provider_message_id = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
    alert = relationship("Alert", back_populates="notifications")
