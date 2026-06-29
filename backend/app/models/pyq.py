from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class QuestionPaper(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "question_papers"

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    paper_type: Mapped[str] = mapped_column(String(20), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(20), default="prelims")
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gs_paper: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    optional_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_marks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    questions: Mapped[List["PYQ"]] = relationship(
        "PYQ", back_populates="question_paper", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("year", "paper_type", "exam_type", "gs_paper",
                         name="uq_question_paper"),
    )


class PYQ(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pyqs"

    question_paper_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_papers.id"), nullable=True, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    paper_type: Mapped[str] = mapped_column(String(20), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(20), default="prelims")
    subject: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), default="mcq")
    options: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answer_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    concepts_tested: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    elimination_hints: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    common_mistakes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    references: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    marks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    negative_marks: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    syllabus_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    syllabus_node_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    question_paper: Mapped[Optional["QuestionPaper"]] = relationship(
        "QuestionPaper", back_populates="questions"
    )

    __table_args__ = (
        UniqueConstraint("year", "paper_type", "exam_type", "question_number",
                         "subject", name="uq_pyq"),
    )


class PYQAttempt(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pyq_attempts"

    pyq_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pyqs.id"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    selected_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    time_taken_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    pyq: Mapped["PYQ"] = relationship("PYQ")
