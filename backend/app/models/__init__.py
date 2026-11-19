"""
SQLAlchemy Models for AgriGuard Relational Database.
All 16 tables required by the system specification are defined here.
"""

from app.models.base import TimestampMixin
from app.models.user import (
    User,
    UserRole,
    Farmer,
    Agronomist,
    Organization,
    OrganizationType,
    OrganizationMember,
    OrganizationMemberRole,
)
from app.models.location import FarmerLocation
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
from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.models.session import USSDSession, IVRSession
from app.models.audit import AuditLog

__all__ = [
    "TimestampMixin",
    "User",
    "UserRole",
    "Farmer",
    "Agronomist",
    "Organization",
    "OrganizationType",
    "OrganizationMember",
    "OrganizationMemberRole",
    "FarmerLocation",
    "Crop",
    "CropReport",
    "ReportChannel",
    "ReportSeverity",
    "ReportStatus",
    "ReportImage",
    "ReportHistory",
    "AIResult",
    "Alert",
    "AlertSeverity",
    "AlertStatus",
    "Notification",
    "NotificationChannel",
    "NotificationStatus",
    "USSDSession",
    "IVRSession",
    "AuditLog",
]
