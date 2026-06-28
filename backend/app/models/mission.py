import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class StudentMission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_missions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    optimization_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_optimization_plans.id", ondelete="SET NULL"),
        nullable=True,
    )

    type: Mapped[str] = mapped_column(String(50), nullable=False)  # "daily", "weekly", "revision", "recovery", "crash"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(String(100), nullable=False)

    # List of tasks, e.g. [{"id": str, "description": str, "content_reference": str, "difficulty": str, "time_estimate": float, "expected_gain": float, "status": str}]
    ordered_tasks: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    status: Mapped[str] = mapped_column(String(50), default="assigned", server_default="'assigned'", nullable=False)  # "assigned", "completed", "skipped", "failed"
    difficulty_level: Mapped[str] = mapped_column(String(50), default="medium", server_default="'medium'", nullable=False)  # "easy", "medium", "hard", "challenge", "recovery"
    
    estimated_time: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)  # in hours
    
    expected_readiness_gain: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    expected_mastery_gain: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    
    actual_readiness_gain: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    actual_mastery_gain: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)

    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    execution_quality: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)

    # Dependencies (list of dependent concept codes)
    dependencies: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    completion_criteria: Mapped[str] = mapped_column(String(500), nullable=False)
    success_metrics: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Evidence tracking (logs or notes)
    evidence: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", backref="missions")
    optimization_plan = relationship("StudentOptimizationPlan", backref="missions")
