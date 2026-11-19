from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LocationBase(BaseModel):
    province: Optional[str] = Field("Northern Province", description="Province e.g., Northern / Amajyaruguru")
    district: str = Field(..., description="District e.g., Musanze, Nyabihu, Gicumbi")
    sector: str = Field(..., description="Sector e.g., Muhoza, Kinigi, Busogo")
    cell: Optional[str] = Field(None, description="Cell e.g., Mpenge, Cyuve")
    village: Optional[str] = Field(None, description="Village / Umudugudu e.g., Gasharu")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    province: Optional[str] = None
    district: Optional[str] = None
    sector: Optional[str] = None
    cell: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: Optional[bool] = None


class LocationResponse(LocationBase):
    id: int
    farmer_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
