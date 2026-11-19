import enum
from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    FARMER = "FARMER"
    AGRONOMIST = "AGRONOMIST"
    ORG_ADMIN = "ORG_ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"


class OrganizationType(str, enum.Enum):
    GOVERNMENT = "GOVERNMENT"       # e.g., RAB (Rwanda Agriculture Board)
    COOPERATIVE = "COOPERATIVE"     # Farmer Cooperatives
    NGO = "NGO"                     # Agricultural Non-Profits
    RESEARCH = "RESEARCH"           # Universities / Institutes


class OrganizationMemberRole(str, enum.Enum):
    ADMIN = "ADMIN"
    LEAD_AGRONOMIST = "LEAD_AGRONOMIST"
    AGRONOMIST = "AGRONOMIST"
    MEMBER = "MEMBER"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(32), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.FARMER, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # 1-to-1 Profiles
    farmer_profile = relationship("Farmer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    agronomist_profile = relationship("Agronomist", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Relationships
    org_memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Farmer(Base, TimestampMixin):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    national_id = Column(String(32), index=True, nullable=True)
    preferred_language = Column(String(8), default="rw", nullable=False)  # 'rw' (Kinyarwanda) or 'en' (English)
    cooperative_name = Column(String(128), nullable=True)
    is_phone_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="farmer_profile")
    locations = relationship("FarmerLocation", back_populates="farmer", cascade="all, delete-orphan")
    crop_reports = relationship("CropReport", back_populates="farmer", cascade="all, delete-orphan")


class Agronomist(Base, TimestampMixin):
    __tablename__ = "agronomists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    license_number = Column(String(64), unique=True, index=True, nullable=True)
    qualification = Column(String(128), nullable=True)  # e.g., 'BSc Crop Protection'
    assigned_districts = Column(Text, nullable=True)    # JSON string or comma-separated list of districts
    assigned_sectors = Column(Text, nullable=True)      # JSON string or comma-separated list of sectors
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="agronomist_profile")
    organization = relationship("Organization", back_populates="agronomists")
    assigned_reports = relationship("CropReport", back_populates="assigned_agronomist")


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)  # e.g., 'RAB', 'COOP-MUSANZE-01'
    type = Column(Enum(OrganizationType), default=OrganizationType.COOPERATIVE, nullable=False)
    district = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    agronomists = relationship("Agronomist", back_populates="organization")
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(OrganizationMemberRole), default=OrganizationMemberRole.MEMBER, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="org_memberships")
