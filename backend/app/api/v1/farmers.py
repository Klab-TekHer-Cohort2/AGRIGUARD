from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user, get_current_farmer, get_current_agronomist, verify_gateway_secret
from app.models.user import User, UserRole, Farmer
from app.models.location import FarmerLocation
from app.models.report import CropReport
from app.schemas.farmer import (
    FarmerProfileResponse,
    FarmerProfileUpdate,
    FarmerLookupResponse,
)
from app.schemas.location import LocationResponse
from app.api.v1.auth import normalize_phone_number

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.get("/profile", response_model=FarmerProfileResponse)
def get_my_farmer_profile(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Retrieves full profile of the currently logged-in farmer,
    including registered locations and report counts.
    """
    total_reports = db.query(CropReport).filter(CropReport.farmer_id == current_farmer.id).count()
    locations = [LocationResponse.model_validate(loc) for loc in current_farmer.locations]

    return FarmerProfileResponse(
        id=current_farmer.id,
        user_id=current_farmer.user.id,
        phone_number=current_farmer.user.phone_number,
        full_name=current_farmer.user.full_name,
        email=current_farmer.user.email,
        preferred_language=current_farmer.preferred_language,
        national_id=current_farmer.national_id,
        cooperative_name=current_farmer.cooperative_name,
        is_phone_verified=current_farmer.is_phone_verified,
        locations=locations,
        total_reports=total_reports,
        created_at=current_farmer.created_at,
    )


@router.put("/profile", response_model=FarmerProfileResponse)
def update_farmer_profile(
    profile_in: FarmerProfileUpdate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Updates profile details (language preference, cooperative, national ID, or name).
    """
    user = current_farmer.user

    if profile_in.full_name is not None:
        user.full_name = profile_in.full_name
    if profile_in.email is not None:
        user.email = profile_in.email
    if profile_in.preferred_language is not None:
        current_farmer.preferred_language = profile_in.preferred_language
    if profile_in.national_id is not None:
        current_farmer.national_id = profile_in.national_id
    if profile_in.cooperative_name is not None:
        current_farmer.cooperative_name = profile_in.cooperative_name

    db.commit()
    db.refresh(current_farmer)
    db.refresh(user)

    total_reports = db.query(CropReport).filter(CropReport.farmer_id == current_farmer.id).count()
    locations = [LocationResponse.model_validate(loc) for loc in current_farmer.locations]

    return FarmerProfileResponse(
        id=current_farmer.id,
        user_id=user.id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        email=user.email,
        preferred_language=current_farmer.preferred_language,
        national_id=current_farmer.national_id,
        cooperative_name=current_farmer.cooperative_name,
        is_phone_verified=current_farmer.is_phone_verified,
        locations=locations,
        total_reports=total_reports,
        created_at=current_farmer.created_at,
    )


@router.get("/by-phone/{phone_number}", response_model=FarmerLookupResponse)
def lookup_farmer_by_phone(
    phone_number: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_gateway_secret),
):
    """
    Lightweight identification endpoint used by USSD and IVR services.

    Gated behind the shared gateway secret (NOT JWT) and trimmed to the minimal
    identification fields: ``is_registered``, ``farmer_id``, ``preferred_language``,
    ``full_name`` plus the echoed ``phone_number`` (the caller already supplied
    it). ``user_id`` and location/village fields were removed to close a PII leak.
    """
    clean_phone = normalize_phone_number(phone_number)
    user = db.query(User).filter(User.phone_number == clean_phone).first()

    if not user or not user.farmer_profile:
        return FarmerLookupResponse(
            is_registered=False,
            phone_number=clean_phone,
            preferred_language="rw",
        )

    farmer = user.farmer_profile
    return FarmerLookupResponse(
        is_registered=True,
        farmer_id=farmer.id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        preferred_language=farmer.preferred_language,
    )


@router.get("/", response_model=List[FarmerProfileResponse])
def list_farmers(
    district: Optional[str] = Query(None, description="Filter by district"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists farmers. Accessible to Agronomists and Administrators.
    Supports geographic filtering by district and sector.
    """
    if current_user.role not in [UserRole.AGRONOMIST, UserRole.SYSTEM_ADMIN, UserRole.ORG_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorized personnel.",
        )

    query = db.query(Farmer).join(User)

    if district:
        query = query.join(FarmerLocation).filter(FarmerLocation.district.ilike(f"%{district}%"))
    if sector:
        query = query.join(FarmerLocation).filter(FarmerLocation.sector.ilike(f"%{sector}%"))

    farmers = query.offset(skip).limit(limit).all()

    results = []
    for f in farmers:
        total_reports = db.query(CropReport).filter(CropReport.farmer_id == f.id).count()
        locations = [LocationResponse.model_validate(loc) for loc in f.locations]
        results.append(
            FarmerProfileResponse(
                id=f.id,
                user_id=f.user.id,
                phone_number=f.user.phone_number,
                full_name=f.user.full_name,
                email=f.user.email,
                preferred_language=f.preferred_language,
                national_id=f.national_id,
                cooperative_name=f.cooperative_name,
                is_phone_verified=f.is_phone_verified,
                locations=locations,
                total_reports=total_reports,
                created_at=f.created_at,
            )
        )
    return results
