import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class StudentDecision(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_decisions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)  # "high", "medium", "low"

    # Store reasoning details (e.g. list of strings)
    reasoning: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Evidence details backing the decision
    evidence: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    confidence: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)

    # Expected gain dict: {"readiness": float, "mastery": float}
    expected_gain: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    estimated_time: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)  # in hours

    # List of dependent node codes
    dependencies: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    risk: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", backref="decisions")
