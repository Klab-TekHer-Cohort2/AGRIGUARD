"""Pydantic v2 schemas for the IVR channel (generic voice-webhook convention).

``IVRRequest`` is the FastAPI body dependency (422 at FastAPI on a malformed
body) — finding #2. Bounds (finding #4 / #7): ``phone_number`` is REQUIRED
(``from`` alias) so the flow can identify the farmer; ``Literal["rw","en"]`` on
language; ``max_length`` on free text; ``digits`` sanitized to keypad
characters ``0-9*#``; numeric ``ge/le`` bounds on gather_digits.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class IVRRequest(BaseModel):
    call_sid: str = Field(..., min_length=1, max_length=128)
    phone_number: str = Field(..., min_length=6, max_length=32, alias="from")  # REQUIRED (finding #7)
    digits: Optional[str] = Field(None, max_length=32)
    recording_url: Optional[str] = Field(None, max_length=512)
    language: Optional[Literal["rw", "en"]] = None
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("digits")
    @classmethod
    def digits_only(cls, v):
        if v is None:
            return None
        v = "".join(c for c in v if c.isdigit() or c in "*#")
        return v or None


class IVROutput(BaseModel):
    """Neutral output; the adapter renders to JSON (a TwiML adapter would emit XML)."""

    action: Literal["say", "gather", "play", "hangup"] = "say"
    prompt: str = Field("", max_length=1000)
    gather_digits: int = Field(0, ge=0, le=32)
    language: Literal["rw", "en"] = "rw"
    session_state: str
