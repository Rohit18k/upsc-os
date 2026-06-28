import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DiagnosisResponse(BaseModel):
    root_cause: str
    evidence: str
    confidence: float
    severity: str
    recommended_intervention_type: str


class BottleneckResponse(BaseModel):
    type: str
    priority: str  # "high", "medium", "low"
    impact: float
    confidence: float
    estimated_study_hours: float


class PredictionState(BaseModel):
    value: float
    lower_bound: float
    upper_bound: float


class PredictionDetails(BaseModel):
    knowledge: PredictionState
    retention: PredictionState
    practice: PredictionState
    writing: PredictionState
    coverage: PredictionState
    readiness: PredictionState


class PredictionResponse(BaseModel):
    projection_7_days: PredictionDetails
    projection_30_days: PredictionDetails
    projection_90_days: PredictionDetails


class InterventionResponse(BaseModel):
    category: str
    target_node: Optional[str] = None
    expected_mastery_gain: float
    expected_readiness_gain: float
    estimated_effort_hours: float
    priority: str
    explanation: List[str]


class DecisionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    priority: str
    reasoning: List[str]
    evidence: Dict[str, Any]
    confidence: float
    expected_gain: Dict[str, float]
    estimated_time: float
    dependencies: List[str]
    risk: Optional[str] = None
    expiry: datetime
    created_at: datetime

    class Config:
        from_attributes = True
