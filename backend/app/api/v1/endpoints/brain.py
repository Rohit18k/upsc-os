import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.response import success_response
from app.models.syllabus import Topic, Concept
from app.models.mapping import KnowledgeEdge
from app.services.brain.engine import BrainEngine, get_brain_engine
from app.services.brain.models import BrainQuery, BrainResponse, Intent
from app.services.brain.metrics import metrics
from app.services.brain.cache import cost_optimizer
from app.services.brain.graph import KnowledgeGraphTraverser
from app.services.brain.retriever import HybridRetriever
from app.services.brain.context import StudentContextEngine

router = APIRouter()


@router.post("/chat")
async def brain_chat(
    request: Request,
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    engine = await get_brain_engine(db)
    query = BrainQuery(
        raw_text=body.get("query", ""),
        student_id=body.get("student_id"),
        conversation_id=body.get("conversation_id"),
        stream=body.get("stream", False),
        max_tokens=body.get("max_tokens", 1024),
        temperature=body.get("temperature", 0.3),
        model=body.get("model"),
        extra_params=body.get("extra", {}),
    )
    response = await engine.process(query)
    return success_response(response.to_dict())


@router.post("/search")
async def brain_search(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    retriever = HybridRetriever(db)
    result = await retriever.search(
        query=body.get("query", ""),
        content_types=body.get("content_types"),
        syllabus_node_id=body.get("syllabus_node_id"),
        limit=body.get("limit", 20),
    )
    return success_response({
        "query": result.query,
        "results": [e.to_dict() for e in result.results],
        "total_found": result.total_found,
        "latency_ms": result.latency_ms,
        "sources": result.sources,
    })


@router.post("/retrieve")
async def brain_retrieve(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    retriever = HybridRetriever(db)
    evidence = await retriever.retrieve(
        query=body.get("query", ""),
        node_id=body.get("syllabus_node_id"),
        limit=body.get("limit", 20),
    )
    return success_response({
        "evidence": [e.to_dict() for e in evidence],
        "count": len(evidence),
    })


@router.post("/context")
async def brain_context(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    student_id = body.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="student_id required")
    ctx_engine = StudentContextEngine(db)
    ctx = await ctx_engine.get_context(
        UUID(student_id), body.get("query")
    )
    return success_response(ctx.to_dict())


@router.post("/explain")
async def brain_explain(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    engine = await get_brain_engine(db)
    topic_name = body.get("topic", body.get("query", ""))
    query = BrainQuery(
        raw_text=f"Explain {topic_name}",
        student_id=body.get("student_id"),
    )
    response = await engine.process(query)
    return success_response(response.to_dict())


@router.post("/stream")
async def brain_stream(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    engine = await get_brain_engine(db)
    query = BrainQuery(
        raw_text=body.get("query", ""),
        student_id=body.get("student_id"),
        conversation_id=body.get("conversation_id"),
        stream=True,
    )
    return StreamingResponse(
        engine.stream(query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/metrics")
async def brain_metrics():
    return success_response({
        "summary": metrics.summary(),
        "cache": {
            "intent_cache_hit_rate": cost_optimizer.intent_cache.hit_rate(),
            "response_cache_hit_rate": cost_optimizer.response_cache.hit_rate(),
        },
        "cost_optimizer": cost_optimizer.usage_summary(),
    })


@router.get("/prometheus")
async def brain_prometheus():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=metrics.to_prometheus(),
        media_type="text/plain",
    )


@router.get("/health")
async def brain_health():
    return success_response({
        "status": "healthy",
        "modules": [
            "intent_router", "hybrid_retriever", "knowledge_graph",
            "student_context", "ranker", "compressor", "prompter",
            "guard", "stream", "cache", "metrics",
        ],
        "total_queries": len(metrics.samples),
        "cache_hit_rate": cost_optimizer.response_cache.hit_rate(),
    })
