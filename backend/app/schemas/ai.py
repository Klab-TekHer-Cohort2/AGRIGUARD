import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AIPredictionPayload(BaseModel):
    """
    Contract definition for the response expected from the AI Developer's API.
    """
    model_name: str = "agriguard-pest-detector"
    model_version: str = "v1.0.0"
    predicted_pest_en: str = Field(..., description="English name of predicted pest or disease")
    predicted_pest_rw: Optional[str] = Field(None, description="Kinyarwanda name")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.00 to 1.00")
    detected_severity: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    recommendations: List[str] = Field(default_factory=list, description="Immediate preventive or curative actions")
    bounding_boxes: Optional[List[Dict[str, Any]]] = Field(None, description="Detected bounding box coordinates")
    raw_response: Optional[Dict[str, Any]] = None
    inference_latency_ms: Optional[int] = None
    is_mock: bool = False


class AIResultResponse(BaseModel):
    id: int
    report_id: int
    report_code: Optional[str] = None
    model_name: str
    model_version: str
    predicted_pest_en: str
    predicted_pest_rw: Optional[str] = None
    confidence_score: float
    detected_severity: str
    recommendations: Optional[Union[List[str], str]] = None
    bounding_boxes: Optional[Union[List[Dict[str, Any]], str]] = None
    inference_latency_ms: Optional[int] = None
    is_mock: bool
    is_verified_correct: Optional[bool] = None
    created_at: datetime

    @field_validator("recommendations", mode="before")
    def parse_recommendations(cls, val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return [val]
        return val

    @field_validator("bounding_boxes", mode="before")
    def parse_bounding_boxes(cls, val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return None
        return val

    model_config = ConfigDict(from_attributes=True)


class AIDatasetExportItem(BaseModel):
    """
    Active Learning Dataset schema for the AI Developer.
    Contains verified ground truth labels confirmed by agronomists.
    """
    report_code: str
    crop_name: str
    crop_scientific_name: Optional[str] = None
    image_url: Optional[str] = None
    symptoms_reported: List[str] = []
    district: str
    sector: str
    ai_predicted_pest: str
    ai_confidence: float
    ground_truth_pest: str
    is_ai_correct: bool
    agronomist_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
