from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Crop(Base, TimestampMixin):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(64), unique=True, nullable=False, index=True)  # e.g., 'Maize'
    name_rw = Column(String(64), unique=True, nullable=False, index=True)  # e.g., 'Ibigori'
    scientific_name = Column(String(128), nullable=True)                  # e.g., 'Zea mays'
    category = Column(String(64), nullable=True, index=True)              # e.g., 'CEREAL', 'TUBER', 'LEGUME'
    description = Column(Text, nullable=True)
    common_pests = Column(Text, nullable=True)                            # JSON string listing common pests
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    reports = relationship("CropReport", back_populates="crop")
    alerts = relationship("Alert", back_populates="crop")
