from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class FarmerLocation(Base, TimestampMixin):
    __tablename__ = "farmer_locations"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Rwandan administrative hierarchy
    province = Column(String(64), nullable=True)     # e.g., 'Northern Province' / 'Amajyaruguru'
    district = Column(String(64), nullable=False, index=True)  # e.g., 'Musanze'
    sector = Column(String(64), nullable=False, index=True)    # e.g., 'Muhoza'
    cell = Column(String(64), nullable=True, index=True)       # e.g., 'Mpenge'
    village = Column(String(64), nullable=True, index=True)    # Umudugudu e.g., 'Gasharu'
    
    # Optional GPS coordinates
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Primary residence/farm indicator
    is_primary = Column(Boolean, default=True, nullable=False)

    # Relationship
    farmer = relationship("Farmer", back_populates="locations")
