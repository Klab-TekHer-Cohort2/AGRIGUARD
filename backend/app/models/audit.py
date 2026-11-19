from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)        # e.g., 'LOGIN', 'CREATE_REPORT', 'VERIFY_REPORT'
    resource_type = Column(String(64), nullable=False, index=True) # e.g., 'User', 'CropReport', 'Alert'
    resource_id = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)                          # JSON payload of the action details
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    user = relationship("User", back_populates="audit_logs")
