from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class Book(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    author: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    edition: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    isbn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True)
    book_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_authoritative: Mapped[bool] = mapped_column(Boolean, default=True)
    total_chapters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    chapters: Mapped[List["BookChapter"]] = relationship(
        "BookChapter", back_populates="book", cascade="all, delete-orphan", order_by="BookChapter.chapter_number"
    )

    __table_args__ = (
        UniqueConstraint("title", "author", "edition", name="uq_book"),
    )


class BookChapter(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "book_chapters"

    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id"), nullable=False, index=True
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    book: Mapped["Book"] = relationship("Book", back_populates="chapters")
    concept_mappings: Mapped[List["BookConceptMapping"]] = relationship(
        "BookConceptMapping", back_populates="chapter", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("book_id", "chapter_number", name="uq_chapter_per_book"),
    )


class BookConceptMapping(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "book_concept_mappings"

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("book_chapters.id"), nullable=False, index=True
    )
    syllabus_node_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    syllabus_node_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    concept_name: Mapped[str] = mapped_column(String(255), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    page_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    chapter: Mapped["BookChapter"] = relationship("BookChapter", back_populates="concept_mappings")

    __table_args__ = (
        UniqueConstraint("chapter_id", "concept_name", name="uq_concept_per_chapter"),
    )
