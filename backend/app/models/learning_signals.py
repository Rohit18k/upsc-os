from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class SyllabusSignal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "syllabus_signals"

    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    node_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    total_pyqs: Mapped[int] = mapped_column(Integer, default=0)
    pyq_frequency_score: Mapped[float] = mapped_column(Float, default=0.0)
    weightage_score: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)
    coverage_score: Mapped[float] = mapped_column(Float, default=0.0)
    overall_importance: Mapped[float] = mapped_column(Float, default=0.0)
    trend_direction: Mapped[str] = mapped_column(String(20), default="stable")
    computed_from: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("node_id", "node_type", name="uq_syllabus_signal"),
    )


class PYQSignal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pyq_signals"

    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    paper_type: Mapped[str] = mapped_column(String(20), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    total_marks: Mapped[float] = mapped_column(Float, default=0.0)
    avg_difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    signal_weight: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint(
            "node_id", "node_type", "year", "paper_type", "exam_type",
            name="uq_pyq_signal",
        ),
    )


class StudentSignal(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_signals"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    syllabus_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    syllabus_node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    avg_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    last_attempted: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "student_id", "syllabus_node_id", "syllabus_node_type",
            name="uq_student_signal",
        ),
    )
