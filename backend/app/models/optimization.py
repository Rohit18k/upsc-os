import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class StudentOptimizationPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_optimization_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)  # "high", "medium", "low"
    
    reasoning_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # List of Decision Object UUIDs that contributed to this plan
    decision_references: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Ordered list of actions to perform
    ordered_actions: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    expected_readiness_gain: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    expected_mastery_gain: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    expected_retention_gain: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    
    estimated_completion_time: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)  # in hours
    confidence: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)

    expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="'active'", nullable=False)  # "active", "expired", "superceded"

    # Relationships
    user = relationship("User", backref="optimization_plans")
