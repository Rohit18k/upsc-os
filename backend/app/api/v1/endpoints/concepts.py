from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.core.response import success_response
from app.models.mapping import ContentMapping, CrossReference, KnowledgeEdge
from app.models.learning_signals import SyllabusSignal, PYQSignal
from app.models.syllabus import Concept, Topic, Module, Subject

router = APIRouter()


@router.get("/mappings")
async def get_content_mappings(
    syllabus_node_id: UUID = Query(...),
    syllabus_node_type: str = Query(...),
    content_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(ContentMapping).where(
        ContentMapping.syllabus_node_id == syllabus_node_id,
        ContentMapping.syllabus_node_type == syllabus_node_type,
    )
    if content_type:
        query = query.where(ContentMapping.content_type == content_type)
    query = query.order_by(ContentMapping.signal_strength.desc())
    result = await db.execute(query)
    mappings = result.scalars().all()
    return success_response([
        {
            "id": str(m.id),
            "content_id": str(m.content_id),
            "content_type": m.content_type,
            "relevance_score": m.relevance_score,
            "signal_strength": m.signal_strength,
            "signal_source": m.signal_source,
            "is_verified": m.is_verified,
        }
        for m in mappings
    ])


@router.get("/signals/{node_id}")
async def get_node_signals(
    node_id: UUID,
    node_type: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SyllabusSignal).where(
            SyllabusSignal.node_id == node_id,
            SyllabusSignal.node_type == node_type,
        )
    )
    signal = result.scalar_one_or_none()
    if not signal:
        return success_response(None)
    return success_response({
        "id": str(signal.id),
        "node_id": str(signal.node_id),
        "node_type": signal.node_type,
        "total_pyqs": signal.total_pyqs,
        "pyq_frequency_score": signal.pyq_frequency_score,
        "weightage_score": signal.weightage_score,
        "difficulty_score": signal.difficulty_score,
        "recency_score": signal.recency_score,
        "coverage_score": signal.coverage_score,
        "overall_importance": signal.overall_importance,
        "trend_direction": signal.trend_direction,
    })


@router.get("/signals")
async def get_signals_bulk(
    node_type: str = Query(...),
    sort_by: str = Query("overall_importance"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    valid_sorts = {
        "overall_importance": SyllabusSignal.overall_importance,
        "pyq_frequency_score": SyllabusSignal.pyq_frequency_score,
        "weightage_score": SyllabusSignal.weightage_score,
        "difficulty_score": SyllabusSignal.difficulty_score,
        "recency_score": SyllabusSignal.recency_score,
    }
    order_col = valid_sorts.get(sort_by, SyllabusSignal.overall_importance)
    result = await db.execute(
        select(SyllabusSignal)
        .where(SyllabusSignal.node_type == node_type)
        .order_by(order_col.desc())
        .limit(limit)
    )
    signals = result.scalars().all()
    return success_response([
        {
            "node_id": str(s.node_id),
            "node_type": s.node_type,
            "total_pyqs": s.total_pyqs,
            "pyq_frequency_score": s.pyq_frequency_score,
            "weightage_score": s.weightage_score,
            "difficulty_score": s.difficulty_score,
            "recency_score": s.recency_score,
            "coverage_score": s.coverage_score,
            "overall_importance": s.overall_importance,
            "trend_direction": s.trend_direction,
        }
        for s in signals
    ])


@router.get("/relationships")
async def get_concept_relationships(
    concept_id: UUID,
    edge_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(KnowledgeEdge).where(
        (KnowledgeEdge.source_concept_id == concept_id) |
        (KnowledgeEdge.target_concept_id == concept_id)
    )
    if edge_type:
        query = query.where(KnowledgeEdge.edge_type == edge_type)
    result = await db.execute(query)
    edges = result.scalars().all()
    return success_response([
        {
            "id": str(e.id),
            "source_concept_id": str(e.source_concept_id),
            "target_concept_id": str(e.target_concept_id),
            "edge_type": e.edge_type,
            "weight": e.weight,
            "source": e.source,
        }
        for e in edges
    ])


@router.get("/cross-references")
async def get_cross_references(
    node_id: UUID,
    node_type: str = Query(...),
    direction: str = Query("outgoing"),
    db: AsyncSession = Depends(get_db),
):
    if direction == "outgoing":
        result = await db.execute(
            select(CrossReference).where(
                CrossReference.source_node_id == node_id,
                CrossReference.source_node_type == node_type,
            )
        )
    else:
        result = await db.execute(
            select(CrossReference).where(
                CrossReference.target_node_id == node_id,
                CrossReference.target_node_type == node_type,
            )
        )
    refs = result.scalars().all()
    return success_response([
        {
            "id": str(r.id),
            "source_node_id": str(r.source_node_id),
            "source_node_type": r.source_node_type,
            "target_node_id": str(r.target_node_id),
            "target_node_type": r.target_node_type,
            "relationship_type": r.relationship_type,
            "strength": r.strength,
        }
        for r in refs
    ])
