from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.location import LocationResponse


class FarmerProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_language: Optional[str] = None  # 'rw' or 'en'
    national_id: Optional[str] = None
    cooperative_name: Optional[str] = None


class FarmerProfileResponse(BaseModel):
    id: int
    user_id: int
    phone_number: str
    full_name: str
    email: Optional[str] = None
    preferred_language: str
    national_id: Optional[str] = None
    cooperative_name: Optional[str] = None
    is_phone_verified: bool
    locations: List[LocationResponse] = []
    total_reports: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FarmerLookupResponse(BaseModel):
    """
    Minimal identification schema for USSD and IVR sessions to identify a farmer
    instantly by phone number. Trimmed to the minimal identification set (PII
    such as user_id and location/village removed); gated behind the gateway
    shared secret. Class name + export kept so existing imports resolve.
    """
    is_registered: bool
    farmer_id: Optional[int] = None
    phone_number: str
    full_name: Optional[str] = None
    preferred_language: str = "rw"
