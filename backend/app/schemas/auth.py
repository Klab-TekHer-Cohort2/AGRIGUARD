from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    phone_number: str
    full_name: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class UserLogin(BaseModel):
    phone_number: str = Field(..., description="E.g., +250788123456 or 0788123456")
    password: str = Field(..., min_length=4)


class UserRegister(BaseModel):
    phone_number: str = Field(..., description="Primary phone number (used for USSD/IVR identification)")
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.FARMER

    # Farmer specific fields (optional during registration)
    preferred_language: str = Field("rw", description="'rw' (Kinyarwanda) or 'en' (English)")
    national_id: Optional[str] = None
    cooperative_name: Optional[str] = None

    # Initial Location (optional during registration)
    province: Optional[str] = None
    district: Optional[str] = None
    sector: Optional[str] = None
    cell: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class UserResponse(BaseModel):
    id: int
    phone_number: str
    email: Optional[str] = None
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
