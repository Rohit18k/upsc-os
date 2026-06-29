from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class IntentType(str, Enum):
    LEARN_CONCEPT = "learn_concept"
    REVISION = "revision"
    PYQ_DISCUSSION = "pyq_discussion"
    BOOK_EXPLANATION = "book_explanation"
    ANSWER_REVIEW = "answer_review"
    CURRENT_AFFAIRS = "current_affairs"
    MENTOR_COACHING = "mentor_coaching"
    MISSION_HELP = "mission_help"
    WEAK_AREA = "weak_area"
    GAP_SIMULATION = "gap_simulation"
    AIR_PREDICTION = "air_prediction"
    GENERAL_CHAT = "general_chat"
    CLARIFICATION = "clarification"


@dataclass
class Intent:
    type: IntentType
    confidence: float
    raw_query: str
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    sub_intent: Optional[str] = None


@dataclass
class Evidence:
    content_id: UUID
    content_type: str
    title: str
    snippet: str
    source: str
    syllabus_node_id: Optional[UUID] = None
    syllabus_node_type: Optional[str] = None
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    citation_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_id": str(self.content_id),
            "content_type": self.content_type,
            "title": self.title,
            "snippet": self.snippet[:300],
            "source": self.source,
            "syllabus_node_id": str(self.syllabus_node_id) if self.syllabus_node_id else None,
            "syllabus_node_type": self.syllabus_node_type,
            "score": self.score,
        }


@dataclass
class StudentContext:
    student_id: UUID
    weak_subjects: List[str] = field(default_factory=list)
    current_missions: List[Dict[str, Any]] = field(default_factory=list)
    mastery_scores: Dict[str, float] = field(default_factory=dict)
    memory_strength: Dict[str, float] = field(default_factory=dict)
    revision_backlog: List[str] = field(default_factory=list)
    writing_weakness: List[str] = field(default_factory=list)
    learning_preferences: Dict[str, Any] = field(default_factory=dict)
    study_hours_per_week: float = 0.0
    days_until_exam: Optional[int] = None
    mentor_memory: List[Dict[str, Any]] = field(default_factory=list)
    recent_searches: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": str(self.student_id),
            "weak_subjects": self.weak_subjects[:3],
            "current_missions": len(self.current_missions),
            "mastery_scores": dict(list(self.mastery_scores.items())[:10]),
            "revision_backlog": self.revision_backlog[:5],
            "writing_weakness": self.writing_weakness[:3],
            "study_hours_per_week": self.study_hours_per_week,
            "days_until_exam": self.days_until_exam,
        }


@dataclass
class CompressedContext:
    evidence: List[Evidence] = field(default_factory=list)
    total_tokens: int = 0
    max_tokens: int = 4000
    truncated: bool = False

    @property
    def prompt_text(self) -> str:
        parts = []
        for i, e in enumerate(self.evidence, 1):
            parts.append(f"[{i}] Source: {e.source} | {e.title}\n{e.snippet}")
        return "\n\n".join(parts)


@dataclass
class BrainQuery:
    raw_text: str
    student_id: Optional[UUID] = None
    conversation_id: Optional[str] = None
    stream: bool = False
    max_tokens: int = 1024
    temperature: float = 0.3
    model: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrainResponse:
    answer: str
    intent: Intent
    evidence: List[Evidence] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    coverage_score: float = 0.0
    next_steps: List[str] = field(default_factory=list)
    model_used: Optional[str] = None
    latency_ms: float = 0.0
    cache_hit: bool = False
    grounded: bool = True
    conversation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "intent": self.intent.type.value,
            "intent_confidence": self.intent.confidence,
            "evidence": [e.to_dict() for e in self.evidence[:5]],
            "citations": self.citations[:10],
            "confidence": self.confidence,
            "coverage_score": self.coverage_score,
            "next_steps": self.next_steps,
            "model_used": self.model_used,
            "grounded": self.grounded,
            "cache_hit": self.cache_hit,
            "conversation_id": self.conversation_id,
        }


@dataclass
class SearchResult:
    query: str
    results: List[Evidence] = field(default_factory=list)
    total_found: int = 0
    latency_ms: float = 0.0
    sources: List[str] = field(default_factory=list)
