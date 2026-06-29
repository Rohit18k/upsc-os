from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class Subject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exam_type: Mapped[str] = mapped_column(String(50), default="mains")
    gs_paper: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pyq_weightage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    modules: Mapped[List["Module"]] = relationship(
        "Module", back_populates="subject", cascade="all, delete-orphan", order_by="Module.sort_order"
    )


class Module(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "modules_syllabus"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pyq_weightage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="modules")
    topics: Mapped[List["Topic"]] = relationship(
        "Topic", back_populates="module", cascade="all, delete-orphan", order_by="Topic.sort_order"
    )

    __table_args__ = (
        UniqueConstraint("subject_id", "name", name="uq_module_name_per_subject"),
    )


class Topic(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "topics_syllabus"

    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules_syllabus.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=60)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    prerequisites: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    pyq_frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_weightage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    module: Mapped["Module"] = relationship("Module", back_populates="topics")
    subtopics: Mapped[List["Subtopic"]] = relationship(
        "Subtopic", back_populates="topic", cascade="all, delete-orphan", order_by="Subtopic.sort_order"
    )
    concepts: Mapped[List["Concept"]] = relationship(
        "Concept", back_populates="topic", cascade="all, delete-orphan", order_by="Concept.sort_order"
    )

    __table_args__ = (
        UniqueConstraint("module_id", "name", name="uq_topic_name_per_module"),
    )


class Subtopic(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subtopics_syllabus"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics_syllabus.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    prerequisites: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="subtopics")

    __table_args__ = (
        UniqueConstraint("topic_id", "name", name="uq_subtopic_name_per_topic"),
    )


class Concept(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "concepts_syllabus"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics_syllabus.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    prerequisites: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=20)
    pyq_frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_weightage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="concepts")
