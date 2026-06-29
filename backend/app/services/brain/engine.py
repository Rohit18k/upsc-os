import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.brain.models import (
    BrainQuery, BrainResponse, Evidence, IntentType, StudentContext,
)
from app.services.brain.metrics import MetricSample
from app.services.brain.router import IntentRouter
from app.services.brain.graph import KnowledgeGraphTraverser
from app.services.brain.retriever import HybridRetriever
from app.services.brain.context import StudentContextEngine
from app.services.brain.ranker import ContextRanker
from app.services.brain.compressor import ContextCompressor
from app.services.brain.prompter import PromptOrchestrator
from app.services.brain.guard import HallucinationGuard
from app.services.brain.stream import stream_engine, StreamingEngine
from app.services.brain.metrics import metrics, BrainMetrics
from app.services.brain.cache import cost_optimizer, AICostOptimizer


class BrainEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.router = IntentRouter()
        self.graph = KnowledgeGraphTraverser(db)
        self.retriever = HybridRetriever(db)
        self.context_engine = StudentContextEngine(db)
        self.ranker = ContextRanker()
        self.compressor = ContextCompressor()
        self.prompter = PromptOrchestrator()
        self.guard = HallucinationGuard(db)

    async def process(self, query: BrainQuery) -> BrainResponse:
        start = time.time()
        conv_id = query.conversation_id or str(uuid.uuid4())

        cached = await cost_optimizer.get_cached_response(query)
        if cached:
            cached.cache_hit = True
            cached.conversation_id = conv_id
            return cached

        cached_intent = await cost_optimizer.get_cached_intent(query.raw_text)
        if cached_intent:
            intent = cached_intent
        else:
            intent = await self.router.detect(query.raw_text)
            await cost_optimizer.cache_intent(query.raw_text, intent)

        retrieval_start = time.time()

        student_ctx = StudentContext(student_id=query.student_id or uuid.uuid4())
        if query.student_id:
            student_ctx = await self.context_engine.get_context(
                query.student_id, query.raw_text
            )

        entity_topic = intent.extracted_entities.get("topic")
        entity_subject = intent.extracted_entities.get("subject")

        kg_evidence: List[Evidence] = []
        if entity_topic:
            topic = await self.graph.find_topic(entity_topic)
            if topic:
                kg_evidence.extend(await self.graph.get_prerequisites(topic.id))
                kg_evidence.extend(await self.graph.get_dependents(topic.id))
        elif entity_subject:
            pass

        search_result = await self.retriever.search(
            query=query.raw_text,
            syllabus_node_id=None,
            limit=30,
        )

        all_evidence = kg_evidence + search_result.results

        ranked = await self.ranker.rank(all_evidence, student_ctx)
        ranked = await self.ranker.rerank_with_query(ranked, query.raw_text)

        compressed = await self.compressor.compress(ranked, max_evidence=12)

        evidence_text = await self.compressor.compress_for_prompt(
            compressed.evidence, intent.type.value
        )

        extra = {
            "topic_name": entity_topic or query.raw_text,
            "concept_name": entity_topic or query.raw_text,
            "student_answer": query.extra_params.get("student_answer", ""),
        }

        prompt = await self.prompter.build(
            intent=intent.type.value,
            evidence_text=evidence_text,
            student_context=student_ctx.to_dict(),
            query=query.raw_text,
            extra=extra,
        )

        model = cost_optimizer.select_model(
            intent.type.value, compressed.total_tokens, query.model
        )

        retrieval_latency = time.time() - retrieval_start

        llm_start = time.time()
        answer = self._generate_answer(prompt, intent, compressed, student_ctx)
        llm_latency = time.time() - llm_start

        guard_result = await self.guard.verify(answer, compressed.evidence)

        if not guard_result["passed"]:
            answer = await self.guard.safe_response(guard_result, answer)

        token_count = len(prompt.split()) + len(answer.split())
        cost_optimizer.track_usage(model, token_count)

        confidence = min(
            intent.confidence * 0.3
            + (len(compressed.evidence) / 12.0) * 0.3
            + (1.0 if guard_result["passed"] else 0.2) * 0.4,
            1.0,
        )

        total_latency = time.time() - start

        response = BrainResponse(
            answer=answer,
            intent=intent,
            evidence=compressed.evidence,
            citations=[e.to_dict() for e in compressed.evidence[:5]],
            confidence=round(confidence, 3),
            coverage_score=round(len(compressed.evidence) / 12.0, 3),
            next_steps=self._next_steps(intent, compressed.evidence),
            model_used=model,
            latency_ms=round(total_latency * 1000, 1),
            grounded=guard_result["passed"],
            cache_hit=False,
            conversation_id=conv_id,
        )

        if confidence > 0.7:
            await cost_optimizer.cache_response(query, response)

        metrics.record(MetricSample(
            intent=intent.type.value,
            retrieval_latency=retrieval_latency,
            llm_latency=llm_latency,
            total_latency=total_latency,
            cache_hit=False,
            token_count=token_count,
            model=model,
            evidence_count=len(compressed.evidence),
            confidence=confidence,
            cost=cost_optimizer.COST_PER_TOKEN.get(model, 0) * token_count,
            hallucination_blocked=not guard_result["passed"],
        ))

        return response

    def _generate_answer(
        self,
        prompt: str,
        intent: Any,
        compressed: Any,
        ctx: StudentContext,
    ) -> str:
        evidence = compressed.evidence
        intent_type = intent.type.value

        if not evidence:
            return (
                "I don't have enough information in my knowledge base to answer that "
                "question accurately. Here's what I know:\n\n"
                f"- Your query was about: {intent.raw_query}\n"
                f"- I detected this as: {intent_type}\n"
                "- I searched my knowledge base but found no relevant evidence.\n\n"
                "Could you please rephrase your question or ask about a specific topic?"
            )

        parts = [f"## Answer\n\n"]
        refs = []

        for i, e in enumerate(evidence[:8], 1):
            refs.append(f"[{i}] {e.title} — {e.source}")
            if i == 1:
                parts.append(f"Based on the retrieved information: {e.snippet[:500]}\n\n")

        parts.append(f"**Sources**: {len(evidence)} evidence items retrieved.\n\n")
        parts.append("### References\n")
        parts.extend(f"{r}\n" for r in refs[:5])

        if ctx.weak_subjects:
            parts.append(
                f"\n*Your weak areas ({', '.join(ctx.weak_subjects[:3])}) "
                f"overlap with this topic — focus extra attention here.*\n"
            )

        return "".join(parts)

    def _next_steps(
        self, intent: Any, evidence: List[Evidence]
    ) -> List[str]:
        steps = []
        if intent.type == IntentType.LEARN_CONCEPT:
            steps.append("Practice PYQs on this topic")
            steps.append("Review related concepts in the knowledge graph")
        elif intent.type == IntentType.REVISION:
            steps.append("Take a quick quiz on this topic")
            steps.append("Flag for last-week revision")
        elif intent.type == IntentType.PYQ_DISCUSSION:
            steps.append("Attempt 5 more PYQs on this subject")
            steps.append("Review answer-writing structure")
        else:
            if not evidence:
                steps.append("Try rephrasing your question")
            else:
                steps.append("Ask a follow-up for deeper explanation")
        return steps

    async def stream(
        self, query: BrainQuery
    ) -> AsyncGenerator[str, None]:
        response = await self.process(query)
        async for event in stream_engine.stream_response(response):
            yield event


brain_engine = BrainEngine

async def get_brain_engine(db: AsyncSession = Depends(get_db)) -> BrainEngine:
    return BrainEngine(db)
