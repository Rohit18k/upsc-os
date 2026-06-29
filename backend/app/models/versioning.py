from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class ContentVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "content_versions"

    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    citations: Mapped[List["Citation"]] = relationship(
        "Citation", back_populates="content_version", cascade="all, delete-orphan"
    )


class Citation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "citations"

    content_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_versions.id"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    source_title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    page_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    content_version: Mapped["ContentVersion"] = relationship("ContentVersion", back_populates="citations")


class SourceDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "source_documents"

    source_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata_json", JSON, nullable=True)
    is_authoritative: Mapped[bool] = mapped_column(Boolean, default=True)
    duplicate_of: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)


class DuplicateRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "duplicate_records"

    primary_content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    primary_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duplicate_content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    duplicate_content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, default=1.0)
    detection_method: Mapped[str] = mapped_column(String(50), default="exact_hash")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_action: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)


class VerificationRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "verification_records"

    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    matched_sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    verification_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    discrepancies: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verified_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
