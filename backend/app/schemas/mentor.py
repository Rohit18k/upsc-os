import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class MentorBriefingResponse(BaseModel):
    briefing_text: str
    yesterday_stats: Dict[str, Any]
    retention_warning: Optional[str] = None
    recalculation_triggered: bool
    evidence: Dict[str, Any]


class MentorReviewResponse(BaseModel):
    review_text: str
    stats: Dict[str, Any]
    tomorrow_focus: str


class MentorChatResponse(BaseModel):
    reply: str
    citation: Optional[str] = None
    suggested_actions: List[str]
    interaction_id: uuid.UUID
    cost_metrics: Dict[str, Any]


class MentorSocraticResponse(BaseModel):
    reply: str
    step: int
    hints_remaining: int
    is_mastered: bool
    suggested_actions: List[str]
    interaction_id: uuid.UUID


class MentorAnswerReviewResponse(BaseModel):
    score: float
    strengths: List[str]
    weaknesses: List[str]
    improved_answer: str
    improvement_tasks: List[str]
    interaction_id: uuid.UUID


class MentorGapSimulationResponse(BaseModel):
    simulated_subject: str
    readiness_impact: float
    knowledge_impact: float
    retention_impact: float
    expected_marks_lost: float
    dependency_chain: List[str]
    explanation: str


class MentorMemoryResponse(BaseModel):
    weak_concepts: List[str]
    learning_preferences: Dict[str, Any]
    repeated_mistakes: Dict[str, int]
    writing_weaknesses: List[str]
    revision_habits: Dict[str, Any]
    confidence_trends: List[Dict[str, Any]]
    burnout_history: List[Dict[str, Any]]
