from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.core.response import success_response, paginated_response
from app.models.books import Book, BookChapter, BookConceptMapping

router = APIRouter()


@router.get("")
async def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    book_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_authoritative: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Book)
    count_query = select(func.count(Book.id))

    if book_type:
        query = query.where(Book.book_type == book_type)
        count_query = count_query.where(Book.book_type == book_type)
    if category:
        query = query.where(Book.category == category)
        count_query = count_query.where(Book.category == category)
    if is_authoritative is not None:
        query = query.where(Book.is_authoritative == is_authoritative)
        count_query = count_query.where(Book.is_authoritative == is_authoritative)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = query.order_by(Book.title).offset(offset).limit(page_size)
    result = await db.execute(query)
    books = result.scalars().all()

    return paginated_response(
        items=[
            {
                "id": str(b.id),
                "title": b.title,
                "author": b.author,
                "edition": b.edition,
                "publisher": b.publisher,
                "isbn": b.isbn,
                "book_type": b.book_type,
                "category": b.category,
                "description": b.description,
                "is_authoritative": b.is_authoritative,
                "total_chapters": b.total_chapters,
            }
            for b in books
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{book_id}")
async def get_book(book_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Book)
        .options(selectinload(Book.chapters))
        .where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        from app.core.exception_handlers import NotFoundError
        raise NotFoundError("Book not found")
    return success_response({
        "id": str(book.id),
        "title": book.title,
        "author": book.author,
        "edition": book.edition,
        "publisher": book.publisher,
        "isbn": book.isbn,
        "book_type": book.book_type,
        "category": book.category,
        "description": book.description,
        "is_authoritative": book.is_authoritative,
        "total_chapters": book.total_chapters,
        "chapters": [
            {
                "id": str(ch.id),
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "page_start": ch.page_start,
                "page_end": ch.page_end,
            }
            for ch in book.chapters
        ],
    })


@router.get("/{book_id}/chapters/{chapter_id}")
async def get_chapter(
    book_id: UUID,
    chapter_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BookChapter)
        .options(selectinload(BookChapter.concept_mappings))
        .where(
            BookChapter.id == chapter_id,
            BookChapter.book_id == book_id,
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        from app.core.exception_handlers import NotFoundError
        raise NotFoundError("Chapter not found")
    return success_response({
        "id": str(chapter.id),
        "book_id": str(chapter.book_id),
        "chapter_number": chapter.chapter_number,
        "title": chapter.title,
        "description": chapter.description,
        "page_start": chapter.page_start,
        "page_end": chapter.page_end,
        "concept_mappings": [
            {
                "id": str(cm.id),
                "concept_name": cm.concept_name,
                "syllabus_node_id": str(cm.syllabus_node_id) if cm.syllabus_node_id else None,
                "syllabus_node_type": cm.syllabus_node_type,
                "relevance_score": cm.relevance_score,
                "page_reference": cm.page_reference,
            }
            for cm in chapter.concept_mappings
        ],
    })


@router.get("/by-concept/{concept_name}")
async def find_books_by_concept(
    concept_name: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BookConceptMapping)
        .options(
            selectinload(BookConceptMapping.chapter).selectinload(BookChapter.book)
        )
        .where(BookConceptMapping.concept_name.ilike(f"%{concept_name}%"))
    )
    mappings = result.scalars().all()

    seen = set()
    books = []
    for m in mappings:
        if m.chapter and m.chapter.book and m.chapter.book.id not in seen:
            seen.add(m.chapter.book.id)
            books.append({
                "id": str(m.chapter.book.id),
                "title": m.chapter.book.title,
                "author": m.chapter.book.author,
                "chapter_number": m.chapter.chapter_number,
                "chapter_title": m.chapter.title,
                "relevance_score": m.relevance_score,
            })
    return success_response(books)
