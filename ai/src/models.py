"""Data models (result contracts) for the AgriGuard AI component.

Plain ``dataclasses`` so results are easy to inspect in a notebook and trivially
serialisable to JSON / dict for the FastAPI service and the team's backend.

These contracts mirror the JSON shapes consumed by Persons 1 (frontend) and 3
(backend); keeping them stable means swapping the Colab ML layer in/out of the
FastAPI service needs no contract changes.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ConfidenceResult:
    """Confidence tier + numeric score (section 9). Independent of severity."""
    score: float
    level: str            # "High" | "Medium" | "Low"
    tier: str             # "high" | "medium" | "low"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EscalationResult:
    """Agronomist escalation decision (section 11)."""
    needs_agronomist: bool
    reasons: List[str] = field(default_factory=list)
    reason: str = "none"  # comma-joined reasons, for compact logging/USSD

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CropAnalysisResult:
    """Full structured result of analysing one crop report (section 5).

    Returned by ``crop_analysis.analyze_report``. Field names use snake_case for
    Python idiomatic use; the FastAPI service maps these to the camelCase JSON
    contract consumed by the frontend/backend.
    """
    crop: str
    crop_id: str
    category: str
    possible_problem: Optional[str]
    problem_id: Optional[str]
    confidence: float
    confidence_level: str
    severity: str
    recommendation: List[str]
    recommendation_text: str
    needs_agronomist: bool
    escalation_reason: str
    language: str
    image_analysed: bool
    source: str            # "ml" (trained classifier) | "keyword" (fallback)
    vision_source: str      # "real-model" | "simulated-demo" | "none"
    disclaimer: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OutbreakRiskResult:
    """Community outbreak risk result (sections 19/20). PROTOTYPE scoring."""
    risk_level: str         # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    risk_score: float       # 0-100 transparent heuristic (NOT a probability)
    problem: Optional[str]
    crop: Optional[str]
    crop_id: Optional[str]
    problem_id: Optional[str]
    category: Optional[str]
    report_count: int
    affected_area: Optional[str]
    affected_area_center: Optional[Dict[str, float]]
    geo_concentrated: bool
    alert_recommended: bool
    reason: str
    radius_km: float
    time_window_days: int
    is_prototype: bool = True
    disclaimer: str = "Prototype Community Risk Score — not a scientifically validated forecasting model."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AssistantAnswer:
    """Grounded answer to a farmer question (sections 14/15)."""
    question: str
    answer: str
    language: str
    sources: List[Dict[str, str]] = field(default_factory=list)
    confidence: float = 0.0
    needs_agronomist: bool = False
    reason: str = "none"
    retrieval_method: str = "keyword"  # "embeddings" | "keyword"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AlertableFarmer:
    """A farmer eligible for a personalised prototype 5 km alert (section 22)."""
    farmer_id: str
    name: Optional[str]
    community: Optional[str]
    distance_km: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
