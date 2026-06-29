from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class ModelAnswer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "model_answers"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    exam_type: Mapped[str] = mapped_column(String(20), default="mains")
    gs_paper: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marks: Mapped[int] = mapped_column(Integer, default=15)
    word_limit: Mapped[int] = mapped_column(Integer, default=250)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_pyq: Mapped[bool] = mapped_column(Boolean, default=False)
    syllabus_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    syllabus_node_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    structures: Mapped[List["AnswerStructure"]] = relationship(
        "AnswerStructure", back_populates="model_answer", cascade="all, delete-orphan"
    )
    keywords: Mapped[List["AnswerKeyword"]] = relationship(
        "AnswerKeyword", back_populates="model_answer", cascade="all, delete-orphan"
    )
    references: Mapped[List["AnswerReference"]] = relationship(
        "AnswerReference", back_populates="model_answer", cascade="all, delete-orphan"
    )


class AnswerStructure(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "answer_structures"

    model_answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_answers.id"), nullable=False, index=True
    )
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    model_answer: Mapped["ModelAnswer"] = relationship("ModelAnswer", back_populates="structures")


class AnswerKeyword(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "answer_keywords"

    model_answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_answers.id"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    importance: Mapped[str] = mapped_column(String(20), default="essential")
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    model_answer: Mapped["ModelAnswer"] = relationship("ModelAnswer", back_populates="keywords")


class AnswerReference(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "answer_references"

    model_answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_answers.id"), nullable=False, index=True
    )
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_value: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relevance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    model_answer: Mapped["ModelAnswer"] = relationship("ModelAnswer", back_populates="references")


class ConclusionTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conclusion_templates"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tone: Mapped[str] = mapped_column(String(50), default="balanced")
    word_count: Mapped[int] = mapped_column(Integer, default=50)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)
