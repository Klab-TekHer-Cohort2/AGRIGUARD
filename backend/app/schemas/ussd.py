"""Pydantic v2 schemas for the USSD channel (Africa's-Talking convention).

Bounds enforce input validation (finding #2 / #4 / #7):
- ``max_length`` on text fields, ``max_length=8`` on symptom lists (each item
  truncated to <=160), ``Literal["rw","en"]`` on language, ``ge`` on crop_id.

USSD is form-encoded, so ``USSDRequest`` is the *canonical contract* documenting
the bounds the router's ``Form(...)`` parameters enforce (422 at FastAPI). The
router uses explicit ``Form(...)`` params (see ``app/ussd/router.py``); this
model is not a body dependency. ``USSDOutput`` is the single neutral menu
output (finding #1): its ``text`` has NO ``max_length`` cap because menu text
is server-generated and the gateway is responsible for truncation (capping it
would reject the ~190-char multi-crop REPORT_CROP screen with a 500).
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class USSDRequest(BaseModel):
    """Canonical wire contract documenting the bounds the router Form() params enforce."""

    sessionId: str = Field(..., min_length=1, max_length=128)
    serviceCode: str = Field("*777#", max_length=32)  # optional (finding #7)
    phoneNumber: str = Field(..., min_length=6, max_length=32)
    text: str = Field("", max_length=640)

    @field_validator("text")
    @classmethod
    def strip_text(cls, v):
        return (v or "").strip()


class USSDOutput(BaseModel):
    """Single neutral menu output (finding #1): no max_length on text (server-controlled)."""

    continue_session: bool
    text: str  # NO max_length cap (server-controlled; gateway truncates)
    new_menu: Optional[str] = None
    language: Literal["rw", "en"] = "rw"


class USSDSelfRegister(BaseModel):
    """Bounds for the registration payload captured across the USSD wizard."""

    full_name: str = Field(..., min_length=2, max_length=128)
    district: str = Field(..., min_length=2, max_length=64)
    preferred_language: Literal["rw", "en"] = "rw"


class USSDReportDraft(BaseModel):
    """Bounds for the in-session report draft."""

    crop_id: int = Field(..., ge=1)
    description: Optional[str] = Field(None, max_length=640)
    symptoms: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("symptoms")
    @classmethod
    def bound_sym(cls, v):
        return [s[:160] for s in v]
