from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.core.response import success_response
from app.models.syllabus import Subject, Module, Topic, Subtopic, Concept

router = APIRouter()


@router.get("/subjects")
async def list_subjects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subject).order_by(Subject.sort_order)
    )
    subjects = result.scalars().all()
    return success_response([
        {
            "id": str(s.id),
            "name": s.name,
            "display_name": s.display_name,
            "exam_type": s.exam_type,
            "gs_paper": s.gs_paper,
            "is_optional": s.is_optional,
            "sort_order": s.sort_order,
            "icon": s.icon,
            "estimated_hours": s.estimated_hours,
            "pyq_weightage": s.pyq_weightage,
        }
        for s in subjects
    ])


@router.get("/subjects/{subject_id}")
async def get_subject(subject_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subject).where(Subject.id == subject_id)
    )
    subject = result.scalar_one_or_none()
    if not subject:
        from app.core.exception_handlers import NotFoundError
        raise NotFoundError("Subject not found")
    return success_response({
        "id": str(subject.id),
        "name": subject.name,
        "display_name": subject.display_name,
        "description": subject.description,
        "exam_type": subject.exam_type,
        "gs_paper": subject.gs_paper,
        "is_optional": subject.is_optional,
        "sort_order": subject.sort_order,
        "icon": subject.icon,
        "estimated_hours": subject.estimated_hours,
        "pyq_weightage": subject.pyq_weightage,
    })


@router.get("/modules")
async def list_modules(
    subject_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Module).options(selectinload(Module.subject)).order_by(Module.sort_order)
    if subject_id:
        query = query.where(Module.subject_id == subject_id)
    result = await db.execute(query)
    modules = result.scalars().all()
    return success_response([
        {
            "id": str(m.id),
            "subject_id": str(m.subject_id),
            "name": m.name,
            "display_name": m.display_name,
            "description": m.description,
            "sort_order": m.sort_order,
            "estimated_hours": m.estimated_hours,
            "pyq_weightage": m.pyq_weightage,
        }
        for m in modules
    ])


@router.get("/topics")
async def list_topics(
    module_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Topic).order_by(Topic.sort_order)
    if module_id:
        query = query.where(Topic.module_id == module_id)
    result = await db.execute(query)
    topics = result.scalars().all()
    return success_response([
        {
            "id": str(t.id),
            "module_id": str(t.module_id),
            "name": t.name,
            "display_name": t.display_name,
            "difficulty": t.difficulty,
            "estimated_minutes": t.estimated_minutes,
            "sort_order": t.sort_order,
            "pyq_frequency": t.pyq_frequency,
            "expected_weightage": t.expected_weightage,
        }
        for t in topics
    ])


@router.get("/subtopics")
async def list_subtopics(
    topic_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Subtopic).order_by(Subtopic.sort_order)
    if topic_id:
        query = query.where(Subtopic.topic_id == topic_id)
    result = await db.execute(query)
    subtopics = result.scalars().all()
    return success_response([
        {
            "id": str(s.id),
            "topic_id": str(s.topic_id),
            "name": s.name,
            "display_name": s.display_name,
            "difficulty": s.difficulty,
            "estimated_minutes": s.estimated_minutes,
            "sort_order": s.sort_order,
        }
        for s in subtopics
    ])


@router.get("/concepts")
async def list_concepts(
    topic_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Concept).order_by(Concept.sort_order)
    if topic_id:
        query = query.where(Concept.topic_id == topic_id)
    result = await db.execute(query)
    concepts = result.scalars().all()
    return success_response([
        {
            "id": str(c.id),
            "topic_id": str(c.topic_id),
            "name": c.name,
            "display_name": c.display_name,
            "definition": c.definition,
            "difficulty": c.difficulty,
            "sort_order": c.sort_order,
            "estimated_minutes": c.estimated_minutes,
            "pyq_frequency": c.pyq_frequency,
            "expected_weightage": c.expected_weightage,
        }
        for c in concepts
    ])


@router.get("/tree")
async def get_full_tree(db: AsyncSession = Depends(get_db)):
    subjects_result = await db.execute(
        select(Subject).options(
            selectinload(Subject.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.subtopics),
            selectinload(Subject.modules)
            .selectinload(Module.topics)
            .selectinload(Topic.concepts),
        ).order_by(Subject.sort_order)
    )
    subjects = subjects_result.scalars().all()
    return success_response([
        {
            "id": str(s.id),
            "name": s.name,
            "display_name": s.display_name,
            "exam_type": s.exam_type,
            "gs_paper": s.gs_paper,
            "is_optional": s.is_optional,
            "modules": [
                {
                    "id": str(m.id),
                    "name": m.name,
                    "display_name": m.display_name,
                    "sort_order": m.sort_order,
                    "topics": [
                        {
                            "id": str(t.id),
                            "name": t.name,
                            "display_name": t.display_name,
                            "difficulty": t.difficulty,
                            "estimated_minutes": t.estimated_minutes,
                            "pyq_frequency": t.pyq_frequency,
                            "expected_weightage": t.expected_weightage,
                            "subtopics": [
                                {
                                    "id": str(st.id),
                                    "name": st.name,
                                    "display_name": st.display_name,
                                    "difficulty": st.difficulty,
                                    "estimated_minutes": st.estimated_minutes,
                                }
                                for st in t.subtopics
                            ],
                            "concepts": [
                                {
                                    "id": str(c.id),
                                    "name": c.name,
                                    "display_name": c.display_name,
                                    "difficulty": c.difficulty,
                                    "estimated_minutes": c.estimated_minutes,
                                    "pyq_frequency": c.pyq_frequency,
                                    "expected_weightage": c.expected_weightage,
                                }
                                for c in t.concepts
                            ],
                        }
                        for t in m.topics
                    ],
                }
                for m in s.modules
            ],
        }
        for s in subjects
    ])


@router.get("/search")
async def search_syllabus(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    pattern = f"%{q}%"
    subjects = (await db.execute(select(Subject).where(Subject.name.ilike(pattern)))).scalars().all()
    modules = (await db.execute(select(Module).where(Module.name.ilike(pattern)))).scalars().all()
    topics = (await db.execute(select(Topic).where(Topic.name.ilike(pattern)))).scalars().all()
    concepts = (await db.execute(select(Concept).where(Concept.name.ilike(pattern)))).scalars().all()

    results = []
    for s in subjects:
        results.append({"type": "subject", "id": str(s.id), "name": s.display_name})
    for m in modules:
        results.append({"type": "module", "id": str(m.id), "name": m.display_name})
    for t in topics:
        results.append({"type": "topic", "id": str(t.id), "name": t.display_name})
    for c in concepts:
        results.append({"type": "concept", "id": str(c.id), "name": c.display_name})
    return success_response(results)
