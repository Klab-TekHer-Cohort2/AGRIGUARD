from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_farmer
from app.models.user import Farmer
from app.models.location import FarmerLocation
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse

router = APIRouter(prefix="/locations", tags=["Farmer Locations"])


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def add_farmer_location(
    loc_in: LocationCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Registers a new farm or plot location for the logged-in farmer.
    If marked as primary, unsets other existing primary locations.
    """
    if loc_in.is_primary:
        # Unset previous primary flags
        db.query(FarmerLocation).filter(
            FarmerLocation.farmer_id == current_farmer.id
        ).update({"is_primary": False})
        db.commit()

    new_loc = FarmerLocation(
        farmer_id=current_farmer.id,
        province=loc_in.province,
        district=loc_in.district,
        sector=loc_in.sector,
        cell=loc_in.cell,
        village=loc_in.village,
        latitude=loc_in.latitude,
        longitude=loc_in.longitude,
        is_primary=loc_in.is_primary,
    )
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc


@router.get("/my-locations", response_model=List[LocationResponse])
def get_farmer_locations(
    current_farmer: Farmer = Depends(get_current_farmer),
):
    """
    Retrieves all registered plot and farm locations for the logged-in farmer.
    """
    return current_farmer.locations


@router.put("/{location_id}/primary", response_model=LocationResponse)
def set_primary_location(
    location_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Sets a specific farm plot as the farmer's primary location.
    """
    location = db.query(FarmerLocation).filter(
        FarmerLocation.id == location_id,
        FarmerLocation.farmer_id == current_farmer.id,
    ).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found.",
        )

    # Unset all other primary locations
    db.query(FarmerLocation).filter(
        FarmerLocation.farmer_id == current_farmer.id
    ).update({"is_primary": False})

    location.is_primary = True
    db.commit()
    db.refresh(location)
    return location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farmer_location(
    location_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """
    Deletes a registered location. Prevents deleting if it's the only location.
    """
    locations = current_farmer.locations
    if len(locations) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the only registered location for this farmer.",
        )

    loc_to_delete = next((l for l in locations if l.id == location_id), None)
    if not loc_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found.",
        )

    db.delete(loc_to_delete)
    db.commit()
    return None
