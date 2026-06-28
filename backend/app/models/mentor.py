import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class StudentMentorMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_mentor_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    weak_concepts: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    repeated_mistakes: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    frequently_asked_questions: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    learning_preferences: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    writing_weaknesses: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    revision_habits: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    confidence_trends: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    burnout_history: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    motivation_patterns: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", backref="mentor_memory")


class MentorInteraction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "mentor_interactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    query: Mapped[str] = mapped_column(String(1000), nullable=False)
    response: Mapped[str] = mapped_column(String(5000), nullable=False)
    
    mode: Mapped[str] = mapped_column(String(50), nullable=False)  # "chat", "socratic", "answer-review", "gap-simulation"
    
    tokens_prompt: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    tokens_completion: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    
    cost: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    latency: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    
    intent: Mapped[str] = mapped_column(String(100), nullable=False)
    citation: Mapped[str] = mapped_column(String(255), nullable=True)
    user_facing_explanation: Mapped[str] = mapped_column(String(1000), nullable=False)

    user = relationship("User", backref="mentor_interactions")
