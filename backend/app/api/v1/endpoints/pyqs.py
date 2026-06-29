from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.response import success_response, paginated_response
from app.models.pyq import PYQ, QuestionPaper

router = APIRouter()


@router.get("/questions")
async def list_pyqs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = Query(None),
    exam_type: Optional[str] = Query(None),
    paper_type: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    syllabus_node_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(PYQ)
    count_query = select(func.count(PYQ.id))

    if year:
        query = query.where(PYQ.year == year)
        count_query = count_query.where(PYQ.year == year)
    if exam_type:
        query = query.where(PYQ.exam_type == exam_type)
        count_query = count_query.where(PYQ.exam_type == exam_type)
    if paper_type:
        query = query.where(PYQ.paper_type == paper_type)
        count_query = count_query.where(PYQ.paper_type == paper_type)
    if subject:
        query = query.where(PYQ.subject == subject)
        count_query = count_query.where(PYQ.subject == subject)
    if topic:
        query = query.where(PYQ.topic == topic)
        count_query = count_query.where(PYQ.topic == topic)
    if difficulty:
        query = query.where(PYQ.difficulty == difficulty)
        count_query = count_query.where(PYQ.difficulty == difficulty)
    if syllabus_node_id:
        query = query.where(PYQ.syllabus_node_id == syllabus_node_id)
        count_query = count_query.where(PYQ.syllabus_node_id == syllabus_node_id)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    query = query.order_by(PYQ.year.desc(), PYQ.question_number).offset(offset).limit(page_size)
    result = await db.execute(query)
    pyqs = result.scalars().all()

    return paginated_response(
        items=[
            {
                "id": str(p.id),
                "year": p.year,
                "exam_type": p.exam_type,
                "paper_type": p.paper_type,
                "subject": p.subject,
                "topic": p.topic,
                "question_number": p.question_number,
                "question_text": p.question_text,
                "question_type": p.question_type,
                "options": p.options,
                "correct_answer": p.correct_answer,
                "difficulty": p.difficulty,
                "concepts_tested": p.concepts_tested,
                "marks": p.marks,
                "negative_marks": p.negative_marks,
                "syllabus_node_id": str(p.syllabus_node_id) if p.syllabus_node_id else None,
                "syllabus_node_type": p.syllabus_node_type,
            }
            for p in pyqs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/questions/{pyq_id}")
async def get_pyq(pyq_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PYQ).where(PYQ.id == pyq_id))
    pyq = result.scalar_one_or_none()
    if not pyq:
        from app.core.exception_handlers import NotFoundError
        raise NotFoundError("PYQ not found")
    return success_response({
        "id": str(pyq.id),
        "year": pyq.year,
        "exam_type": pyq.exam_type,
        "paper_type": pyq.paper_type,
        "subject": pyq.subject,
        "topic": pyq.topic,
        "question_number": pyq.question_number,
        "question_text": pyq.question_text,
        "question_type": pyq.question_type,
        "options": pyq.options,
        "correct_answer": pyq.correct_answer,
        "answer_explanation": pyq.answer_explanation,
        "difficulty": pyq.difficulty,
        "concepts_tested": pyq.concepts_tested,
        "elimination_hints": pyq.elimination_hints,
        "common_mistakes": pyq.common_mistakes,
        "references": pyq.references,
        "marks": pyq.marks,
        "negative_marks": pyq.negative_marks,
        "syllabus_node_id": str(pyq.syllabus_node_id) if pyq.syllabus_node_id else None,
        "syllabus_node_type": pyq.syllabus_node_type,
        "source": pyq.source,
    })


@router.get("/years")
async def list_years(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PYQ.year).distinct().order_by(PYQ.year.desc())
    )
    years = [row[0] for row in result.all()]
    return success_response(years)


@router.get("/subjects")
async def list_pyq_subjects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PYQ.subject).distinct().order_by(PYQ.subject)
    )
    subjects = [row[0] for row in result.all()]
    return success_response(subjects)


@router.get("/by-syllabus-node/{node_id}")
async def get_pyqs_by_node(
    node_id: UUID,
    node_type: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PYQ).where(
            and_(
                PYQ.syllabus_node_id == node_id,
                PYQ.syllabus_node_type == node_type,
            )
        ).order_by(PYQ.year.desc())
    )
    pyqs = result.scalars().all()
    return success_response([
        {
            "id": str(p.id),
            "year": p.year,
            "exam_type": p.exam_type,
            "paper_type": p.paper_type,
            "question_number": p.question_number,
            "question_text": p.question_text[:200],
            "difficulty": p.difficulty,
            "marks": p.marks,
        }
        for p in pyqs
    ])
