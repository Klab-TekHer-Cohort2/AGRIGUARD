"""USSD interaction Pydantic schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.alert import AlertResponse


class USSDAction(str, Enum):
    """USSD interaction actions."""

    MENU = "menu"
    SUBMIT = "submit"
    BACK = "back"


class USSDRequest(BaseModel):
    """USSD interaction request."""

    session_id: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=10)
    text: str = Field("", max_length=500)
    action: USSDAction = USSDAction.MENU


class USSDResponse(BaseModel):
    """USSD interaction response."""

    message: str
    is_end: bool = False
    report_id: Optional[int] = None
    alerts: list[AlertResponse] = []