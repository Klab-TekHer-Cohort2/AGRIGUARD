"""IVR interaction Pydantic schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.alert import AlertResponse
from app.schemas.report import Severity


class IVRCallStatus(str, Enum):
    """IVR call lifecycle states."""

    STARTED = "started"
    COLLECTING = "collecting"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class IVRRequest(BaseModel):
    """IVR interaction request."""

    call_id: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=10)
    status: IVRCallStatus
    problem_type: Optional[str] = None
    severity: Optional[Severity] = None
    area: Optional[str] = None
    confirmed: bool = False


class IVRResponse(BaseModel):
    """IVR interaction response."""

    message: str
    status: IVRCallStatus
    is_end: bool = False
    report_id: Optional[int] = None
    alerts: list[AlertResponse] = []