from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class ContentMapping(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "content_mappings"

    syllabus_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    syllabus_node_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    signal_strength: Mapped[float] = mapped_column(Float, default=0.0)
    signal_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="manual"
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mapped_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mapping_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "syllabus_node_id", "syllabus_node_type",
            "content_id", "content_type",
            name="uq_content_mapping",
        ),
        Index("ix_mapping_syllabus_content", "syllabus_node_id", "syllabus_node_type", "content_type"),
    )


class CrossReference(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cross_references"

    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    source_node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    target_node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    strength: Mapped[float] = mapped_column(Float, default=0.5)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "source_node_id", "source_node_type",
            "target_node_id", "target_node_type", "relationship_type",
            name="uq_cross_reference",
        ),
        Index("ix_cross_ref_source", "source_node_id", "source_node_type"),
        Index("ix_cross_ref_target", "target_node_id", "target_node_type"),
    )


class KnowledgeEdge(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_edges"

    source_concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts_syllabus.id"), nullable=False, index=True
    )
    target_concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts_syllabus.id"), nullable=False, index=True
    )
    edge_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="prerequisite"
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    source_concept: Mapped["Concept"] = relationship(
        "Concept", foreign_keys=[source_concept_id]
    )
    target_concept: Mapped["Concept"] = relationship(
        "Concept", foreign_keys=[target_concept_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "source_concept_id", "target_concept_id", "edge_type",
            name="uq_knowledge_edge",
        ),
    )
