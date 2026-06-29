from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.response import success_response
from app.models.versioning import ContentVersion, VerificationRecord, DuplicateRecord
from app.models.syllabus import Subject, Module, Topic, Subtopic, Concept
from app.models.pyq import PYQ
from app.models.books import Book
from app.models.answers import ModelAnswer, ConclusionTemplate
from app.models.mapping import ContentMapping

router = APIRouter()


@router.get("/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    subject_count = (await db.execute(select(func.count(Subject.id)))).scalar() or 0
    module_count = (await db.execute(select(func.count(Module.id)))).scalar() or 0
    topic_count = (await db.execute(select(func.count(Topic.id)))).scalar() or 0
    subtopic_count = (await db.execute(select(func.count(Subtopic.id)))).scalar() or 0
    concept_count = (await db.execute(select(func.count(Concept.id)))).scalar() or 0

    lessons = await db.execute(
        select(func.count(ContentVersion.id)).where(
            ContentVersion.content_type == "lesson"
        )
    )
    lesson_count = lessons.scalar() or 0

    flashcards = await db.execute(
        select(func.count(ContentVersion.id)).where(
            ContentVersion.content_type == "flashcard"
        )
    )
    flashcard_count = flashcards.scalar() or 0

    revision_notes = await db.execute(
        select(func.count(ContentVersion.id)).where(
            ContentVersion.content_type == "revision_note"
        )
    )
    revision_count = revision_notes.scalar() or 0

    book_count = (await db.execute(select(func.count(Book.id)))).scalar() or 0
    pyq_count = (await db.execute(select(func.count(PYQ.id)))).scalar() or 0
    answer_count = (await db.execute(select(func.count(ModelAnswer.id)))).scalar() or 0
    conclusion_count = (await db.execute(select(func.count(ConclusionTemplate.id)))).scalar() or 0

    mappings = (await db.execute(select(func.count(ContentMapping.id)))).scalar() or 0

    total_content = lesson_count + flashcard_count + revision_count + answer_count

    val_failures = await db.execute(
        select(func.count(VerificationRecord.id)).where(
            VerificationRecord.status == "flagged"
        )
    )
    validation_failures = val_failures.scalar() or 0

    duplicates = (await db.execute(select(func.count(DuplicateRecord.id)))).scalar() or 0

    verified = await db.execute(
        select(func.count(VerificationRecord.id)).where(
            VerificationRecord.status == "verified"
        )
    )
    verified_count = verified.scalar() or 0
    total_verified = verified_count + validation_failures
    confidence_pct = round(
        (verified_count / max(total_verified, 1)) * 100, 1
    )

    topics_with_content = await db.execute(
        select(func.count(func.distinct(ContentMapping.syllabus_node_id))).where(
            ContentMapping.syllabus_node_type == "topic"
        )
    )
    covered_topics = topics_with_content.scalar() or 0
    coverage_pct = round(
        (covered_topics / max(topic_count, 1)) * 100, 1
    )

    return success_response({
        "syllabus": {
            "subjects": subject_count,
            "modules": module_count,
            "topics": topic_count,
            "subtopics": subtopic_count,
            "concepts": concept_count,
        },
        "content": {
            "lessons": lesson_count,
            "flashcards": flashcard_count,
            "revision_notes": revision_count,
            "model_answers": answer_count,
            "conclusion_templates": conclusion_count,
            "total_artifacts": total_content,
        },
        "ingestion": {
            "books": book_count,
            "pyqs": pyq_count,
        },
        "mappings": mappings,
        "quality": {
            "validation_failures": validation_failures,
            "duplicate_rate": round(duplicates / max(total_content, 1) * 100, 1),
            "confidence_score": confidence_pct,
            "verified_count": verified_count,
        },
        "coverage": {
            "topics_with_content": covered_topics,
            "total_topics": topic_count,
            "coverage_pct": coverage_pct,
        },
    })


@router.get("/coverage-by-subject")
async def coverage_by_subject(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subject).order_by(Subject.sort_order)
    )
    subjects = result.scalars().all()

    coverage = []
    for subject in subjects:
        modules_result = await db.execute(
            select(Module).where(Module.subject_id == subject.id)
        )
        modules = modules_result.scalars().all()

        total_topics = 0
        covered_topics = 0

        for module in modules:
            topics_result = await db.execute(
                select(Topic).where(Topic.module_id == module.id)
            )
            topics = topics_result.scalars().all()
            for topic in topics:
                total_topics += 1
                mapping = await db.execute(
                    select(ContentMapping).where(
                        ContentMapping.syllabus_node_id == topic.id,
                        ContentMapping.syllabus_node_type == "topic",
                    ).limit(1)
                )
                if mapping.scalar_one_or_none():
                    covered_topics += 1

        coverage.append({
            "subject_id": str(subject.id),
            "subject_name": subject.display_name,
            "total_topics": total_topics,
            "covered_topics": covered_topics,
            "coverage_pct": round(covered_topics / max(total_topics, 1) * 100, 1),
        })

    return success_response(coverage)


@router.get("/content-gaps")
async def dashboard_content_gaps(
    subject_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Topic)
    if subject_id:
        query = query.join(Module).where(Module.subject_id == subject_id)
    result = await db.execute(query)
    topics = result.scalars().all()

    gaps = []
    for topic in topics:
        content_result = await db.execute(
            select(func.count(ContentMapping.id)).where(
                ContentMapping.syllabus_node_id == topic.id,
                ContentMapping.syllabus_node_type == "topic",
            )
        )
        content_count = content_result.scalar() or 0

        pyq_result = await db.execute(
            select(func.count(PYQ.id)).where(
                PYQ.syllabus_node_id == topic.id,
                PYQ.syllabus_node_type == "topic",
            )
        )
        pyq_count = pyq_result.scalar() or 0

        if content_count == 0 or pyq_count == 0:
            gaps.append({
                "topic_id": str(topic.id),
                "topic_name": topic.display_name,
                "module_name": topic.module.display_name if topic.module else None,
                "has_content": content_count > 0,
                "has_pyqs": pyq_count > 0,
                "content_count": content_count,
                "pyq_count": pyq_count,
            })

    return success_response({
        "total_gaps": len(gaps),
        "gaps": sorted(gaps, key=lambda g: (g.get("module_name", ""), g["topic_name"])),
    })


@router.get("/validation-summary")
async def validation_summary(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(VerificationRecord).order_by(
        VerificationRecord.verified_at.desc()
    )
    if status:
        query = query.where(VerificationRecord.status == status)
    query = query.limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return success_response([
        {
            "id": str(r.id),
            "content_id": str(r.content_id),
            "content_type": r.content_type,
            "status": r.status,
            "confidence": r.confidence,
            "discrepancies": r.discrepancies or [],
            "verified_at": r.verified_at.isoformat() if r.verified_at else None,
        }
        for r in records
    ])
