from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.user import OrganizationType, OrganizationMemberRole


class OrganizationCreate(BaseModel):
    name: str = Field(..., description="Organization name e.g., Rwanda Agriculture Board or Cooperative")
    code: str = Field(..., description="Unique acronym or registration code e.g., RAB, KOABIKI")
    type: OrganizationType = Field(OrganizationType.COOPERATIVE, description="GOVERNMENT, COOPERATIVE, NGO, RESEARCH")
    district: Optional[str] = Field(None, description="Headquarters or operating district")
    description: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    district: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    code: str
    type: OrganizationType
    district: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    member_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationMemberResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    full_name: str
    phone_number: str
    role: OrganizationMemberRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignMemberRequest(BaseModel):
    user_id: int = Field(..., description="User ID to add as a member")
    role: OrganizationMemberRole = Field(OrganizationMemberRole.AGRONOMIST, description="ADMIN, LEAD_AGRONOMIST, AGRONOMIST, MEMBER")
