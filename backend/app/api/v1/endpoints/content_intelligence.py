from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.core.response import success_response
from app.models.syllabus import Subject, Module, Topic, Concept
from app.models.pyq import PYQ
from app.models.learning_signals import SyllabusSignal, PYQSignal

router = APIRouter()


@router.get("/syllabus-coverage")
async def syllabus_coverage_analysis(
    subject_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Subject).options(
        selectinload(Subject.modules)
        .selectinload(Module.topics)
        .selectinload(Topic.concepts),
    )
    if subject_id:
        query = query.where(Subject.id == subject_id)
    query = query.order_by(Subject.sort_order)
    subjects_result = await db.execute(query)
    subjects = subjects_result.scalars().all()

    analysis = []
    for subject in subjects:
        total_topics = 0
        topics_with_pyqs = 0
        total_concepts = 0
        concepts_with_pyqs = 0
        total_pyq_count = 0

        for module in subject.modules:
            for topic in module.topics:
                total_topics += 1
                pyq_result = await db.execute(
                    select(func.count(PYQ.id)).where(
                        PYQ.syllabus_node_id == topic.id,
                        PYQ.syllabus_node_type == "topic",
                    )
                )
                topic_pyq_count = pyq_result.scalar() or 0
                if topic_pyq_count > 0:
                    topics_with_pyqs += 1
                total_pyq_count += topic_pyq_count

                for concept in topic.concepts:
                    total_concepts += 1
                    concept_pyq_result = await db.execute(
                        select(func.count(PYQ.id)).where(
                            PYQ.syllabus_node_id == concept.id,
                            PYQ.syllabus_node_type == "concept",
                        )
                    )
                    if (concept_pyq_result.scalar() or 0) > 0:
                        concepts_with_pyqs += 1

        analysis.append({
            "subject_id": str(subject.id),
            "subject_name": subject.display_name,
            "total_topics": total_topics,
            "topics_with_pyqs": topics_with_pyqs,
            "topic_coverage_pct": round(topics_with_pyqs / total_topics * 100, 1) if total_topics else 0,
            "total_concepts": total_concepts,
            "concepts_with_pyqs": concepts_with_pyqs,
            "concept_coverage_pct": round(concepts_with_pyqs / total_concepts * 100, 1) if total_concepts else 0,
            "total_pyq_assignments": total_pyq_count,
        })

    return success_response(analysis)


@router.get("/high-value-topics")
async def high_value_topics(
    subject_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    signal_query = select(SyllabusSignal).where(
        SyllabusSignal.node_type == "topic"
    )
    if subject_id:
        signal_query = signal_query.where(
            SyllabusSignal.node_id.in_(
                select(Topic.id).join(Module).where(Module.subject_id == subject_id)
            )
        )
    signal_query = signal_query.order_by(
        SyllabusSignal.overall_importance.desc()
    ).limit(limit)
    result = await db.execute(signal_query)
    signals = result.scalars().all()

    topics = []
    for sig in signals:
        topic_result = await db.execute(
            select(Topic).where(Topic.id == sig.node_id)
        )
        topic = topic_result.scalar_one_or_none()
        if topic:
            topics.append({
                "topic_id": str(topic.id),
                "topic_name": topic.display_name,
                "overall_importance": sig.overall_importance,
                "pyq_frequency_score": sig.pyq_frequency_score,
                "weightage_score": sig.weightage_score,
                "difficulty_score": sig.difficulty_score,
                "recency_score": sig.recency_score,
                "trend_direction": sig.trend_direction,
                "total_pyqs": sig.total_pyqs,
            })

    return success_response({
        "strategy": "Topics ranked by computed signal strength combining PYQ frequency, weightage, recency, and difficulty",
        "high_value_topics": topics,
    })


@router.get("/content-gaps")
async def content_gaps(
    subject_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Topic).options(selectinload(Topic.module))
    if subject_id:
        query = query.join(Module).where(Module.subject_id == subject_id)
    result = await db.execute(query)
    topics = result.scalars().all()

    gaps = []
    for topic in topics:
        pyq_result = await db.execute(
            select(func.count(PYQ.id)).where(
                PYQ.syllabus_node_id == topic.id,
                PYQ.syllabus_node_type == "topic",
            )
        )
        pyq_count = pyq_result.scalar() or 0
        if pyq_count == 0:
            gaps.append({
                "topic_id": str(topic.id),
                "topic_name": topic.display_name,
                "module_name": topic.module.display_name if topic.module else None,
                "gap_type": "no_pyqs",
                "severity": "high",
            })

        concepts_result = await db.execute(
            select(Concept).where(Concept.topic_id == topic.id)
        )
        concepts = concepts_result.scalars().all()
        for concept in concepts:
            concept_pyq = await db.execute(
                select(func.count(PYQ.id)).where(
                    PYQ.syllabus_node_id == concept.id,
                    PYQ.syllabus_node_type == "concept",
                )
            )
            if (concept_pyq.scalar() or 0) == 0:
                gaps.append({
                    "topic_id": str(topic.id),
                    "topic_name": topic.display_name,
                    "concept_id": str(concept.id),
                    "concept_name": concept.display_name,
                    "gap_type": "concept_no_pyqs",
                    "severity": "medium",
                })

    return success_response({
        "total_gaps": len(gaps),
        "gaps": gaps,
    })
