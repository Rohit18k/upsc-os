import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TaskSchema(BaseModel):
    id: str
    description: str
    content_reference: str
    difficulty: str
    time_estimate: float
    expected_gain: float
    status: str  # "assigned", "completed", "skipped"


class MissionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    optimization_plan_id: Optional[uuid.UUID] = None
    type: str
    title: str
    goal: str
    ordered_tasks: List[TaskSchema]
    status: str
    difficulty_level: str
    estimated_time: float
    expected_readiness_gain: float
    expected_mastery_gain: float
    actual_readiness_gain: float
    actual_mastery_gain: float
    completion_percentage: float
    quality_score: float
    execution_quality: float
    consistency_score: float
    dependencies: List[str]
    completion_criteria: str
    success_metrics: str
    evidence: Dict[str, Any]
    expiry: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class MissionExplanationResponse(BaseModel):
    mission_id: uuid.UUID
    title: str
    overall_why: str
    expected_outcomes: Dict[str, str]
    task_explanations: List[Dict[str, str]]
    risk_addressed: str
