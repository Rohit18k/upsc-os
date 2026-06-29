import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.books import Book, BookChapter, BookConceptMapping
from app.models.syllabus import Subject, Concept
from app.models.mapping import KnowledgeEdge


class BaseIngestor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_or_create_book(
        self,
        title: str,
        author: Optional[str] = None,
        edition: Optional[str] = None,
        publisher: Optional[str] = None,
        isbn: Optional[str] = None,
        book_type: str = "ncert",
        category: Optional[str] = None,
        description: Optional[str] = None,
        is_authoritative: bool = True,
        total_chapters: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Book:
        result = await self.db.execute(
            select(Book).where(
                Book.title == title,
                Book.author == author,
                Book.edition == edition,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        book = Book(
            title=title,
            author=author,
            edition=edition,
            publisher=publisher,
            isbn=isbn,
            book_type=book_type,
            category=category,
            description=description,
            is_authoritative=is_authoritative,
            total_chapters=total_chapters,
            extra_metadata=extra_metadata,
        )
        self.db.add(book)
        await self.db.flush()
        return book

    async def add_chapter(
        self,
        book: Book,
        chapter_number: int,
        title: str,
        description: Optional[str] = None,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None,
    ) -> BookChapter:
        result = await self.db.execute(
            select(BookChapter).where(
                BookChapter.book_id == book.id,
                BookChapter.chapter_number == chapter_number,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.title = title
            if description:
                existing.description = description
            await self.db.flush()
            return existing

        chapter = BookChapter(
            book_id=book.id,
            chapter_number=chapter_number,
            title=title,
            description=description,
            page_start=page_start,
            page_end=page_end,
        )
        self.db.add(chapter)
        await self.db.flush()
        return chapter

    async def map_concept_to_chapter(
        self,
        chapter: BookChapter,
        concept_name: str,
        syllabus_node_id: Optional[UUID] = None,
        syllabus_node_type: Optional[str] = None,
        relevance_score: float = 1.0,
        page_reference: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> BookConceptMapping:
        result = await self.db.execute(
            select(BookConceptMapping).where(
                BookConceptMapping.chapter_id == chapter.id,
                BookConceptMapping.concept_name == concept_name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        mapping = BookConceptMapping(
            chapter_id=chapter.id,
            syllabus_node_id=syllabus_node_id,
            syllabus_node_type=syllabus_node_type,
            concept_name=concept_name,
            relevance_score=relevance_score,
            page_reference=page_reference,
            notes=notes,
        )
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def add_knowledge_edge(
        self,
        source_concept_id: UUID,
        target_concept_id: UUID,
        edge_type: str = "prerequisite",
        weight: float = 1.0,
        source: Optional[str] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeEdge:
        result = await self.db.execute(
            select(KnowledgeEdge).where(
                KnowledgeEdge.source_concept_id == source_concept_id,
                KnowledgeEdge.target_concept_id == target_concept_id,
                KnowledgeEdge.edge_type == edge_type,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        edge = KnowledgeEdge(
            source_concept_id=source_concept_id,
            target_concept_id=target_concept_id,
            edge_type=edge_type,
            weight=weight,
            source=source,
            evidence=evidence,
        )
        self.db.add(edge)
        await self.db.flush()
        return edge
