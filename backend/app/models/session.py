from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from app.core.database import Base
from app.models.base import TimestampMixin, utc_now


class USSDSession(Base, TimestampMixin):
    __tablename__ = "ussd_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), unique=True, index=True, nullable=False)
    phone_number = Column(String(32), index=True, nullable=False)
    service_code = Column(String(32), default="*777#", nullable=False)
    
    current_menu = Column(String(64), default="MAIN_MENU", nullable=False)
    language = Column(String(8), default="rw", nullable=False)  # 'rw' or 'en'
    temp_payload = Column(Text, default="{}", nullable=False)  # JSON dictionary of wizard state
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_activity = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class IVRSession(Base, TimestampMixin):
    __tablename__ = "ivr_sessions"

    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String(128), unique=True, index=True, nullable=False)
    phone_number = Column(String(32), index=True, nullable=False)
    caller_name = Column(String(128), nullable=True)
    
    language = Column(String(8), default="rw", nullable=False)  # 'rw' or 'en'
    current_step = Column(String(64), default="WELCOME", nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    dtmf_log = Column(Text, default="[]", nullable=False)       # JSON list of keypad digits pressed
    recording_url = Column(String(255), nullable=True)          # Audio recording link if farmer leaves voice report
    status = Column(String(32), default="IN_PROGRESS", nullable=False)  # RINGING, IN_PROGRESS, COMPLETED, FAILED
