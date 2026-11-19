import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_admin
from app.models.crop import Crop
from app.schemas.crop import CropCreate, CropResponse

router = APIRouter(prefix="/crops", tags=["Crop Catalogue"])


@router.get("/", response_model=List[CropResponse])
def list_crops(
    category: Optional[str] = Query(None, description="Filter by crop category (CEREAL, TUBER, LEGUME, etc.)"),
    is_active: bool = Query(True, description="Filter active crops"),
    db: Session = Depends(get_db),
):
    """
    Returns catalogue of all agricultural crops cultivated in Rwanda
    with their English and Kinyarwanda names, common pests, and descriptions.
    """
    query = db.query(Crop).filter(Crop.is_active == is_active)
    if category:
        query = query.filter(Crop.category.ilike(f"%{category}%"))

    crops = query.all()
    return crops


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop_by_id(crop_id: int, db: Session = Depends(get_db)):
    """
    Retrieves detailed information and common pest profiles for a specific crop.
    """
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop with ID {crop_id} not found.",
        )
    return crop


@router.post("/", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(
    crop_in: CropCreate,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Adds a new crop to the catalogue. Restricted to Administrators.
    """
    existing = db.query(Crop).filter(
        (Crop.name_en.ilike(crop_in.name_en)) | (Crop.name_rw.ilike(crop_in.name_rw))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A crop with this English or Kinyarwanda name already exists.",
        )

    pests_val = json.dumps(crop_in.common_pests) if isinstance(crop_in.common_pests, list) else crop_in.common_pests

    crop = Crop(
        name_en=crop_in.name_en,
        name_rw=crop_in.name_rw,
        scientific_name=crop_in.scientific_name,
        category=crop_in.category,
        description=crop_in.description,
        common_pests=pests_val,
        is_active=crop_in.is_active,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop
