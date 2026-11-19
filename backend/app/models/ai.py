from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class AIResult(Base, TimestampMixin):
    __tablename__ = "ai_results"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("crop_reports.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Model Metadata
    model_name = Column(String(64), default="agriguard-pest-detector", nullable=False)
    model_version = Column(String(32), default="v1.0.0", nullable=False)
    
    # Diagnosis Outputs
    predicted_pest_en = Column(String(128), nullable=False, index=True)
    predicted_pest_rw = Column(String(128), nullable=True, index=True)
    confidence_score = Column(Float, nullable=False)                       # 0.00 to 1.00
    detected_severity = Column(String(32), default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    
    # Treatment & Details
    recommendations = Column(Text, nullable=True)                          # JSON list of action steps
    bounding_boxes = Column(Text, nullable=True)                           # JSON list of detected bounding boxes [x, y, w, h]
    raw_response = Column(Text, nullable=True)                             # Full raw payload from AI developer API
    inference_latency_ms = Column(Integer, nullable=True)                  # Latency in milliseconds
    
    # Flags for Active Learning / ML Retraining Feedback
    is_mock = Column(Boolean, default=False, nullable=False)
    is_verified_correct = Column(Boolean, nullable=True)                   # Agronomist feedback: True if AI was correct

    # Relationship
    report = relationship("CropReport", back_populates="ai_result")
