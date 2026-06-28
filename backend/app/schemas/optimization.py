import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class OptimizationPlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    goal: str
    priority: str
    reasoning_reference: str
    decision_references: List[uuid.UUID]
    ordered_actions: List[Dict[str, Any]]
    expected_readiness_gain: float
    expected_mastery_gain: float
    expected_retention_gain: float
    estimated_completion_time: float
    confidence: float
    expiry: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class StrategyOptionResponse(BaseModel):
    name: str
    description: str
    expected_benefit: str
    risk: str
    estimated_completion_time: str


class ROIMetricResponse(BaseModel):
    action: str
    roi: float
    gains: Dict[str, float]
    time_hours: float


class ConstraintResponse(BaseModel):
    daily_hours: float
    working_status: str
    days_until_exam: int
    weekly_hours_cap: float
    admissible: bool
