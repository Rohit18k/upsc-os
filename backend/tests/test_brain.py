import uuid
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.brain.models import (
    BrainQuery, BrainResponse, Evidence, Intent, IntentType, StudentContext,
)
from app.services.brain.router import IntentRouter
from app.services.brain.ranker import ContextRanker
from app.services.brain.compressor import ContextCompressor
from app.services.brain.cache import AICostOptimizer, SemanticCache
from app.services.brain.stream import StreamingEngine


class TestIntentRouter:
    def setup_method(self):
        self.router = IntentRouter()

    @pytest.mark.asyncio
    async def test_detect_learn_concept(self):
        intent = await self.router.detect("What is the Constitution of India?")
        assert intent.type == IntentType.LEARN_CONCEPT
        assert intent.confidence > 0.3

    @pytest.mark.asyncio
    async def test_detect_pyq(self):
        intent = await self.router.detect("How was the monsoon asked in 2022 PYQ?")
        assert intent.type == IntentType.PYQ_DISCUSSION
        assert intent.confidence > 0.3

    @pytest.mark.asyncio
    async def test_detect_revision(self):
        intent = await self.router.detect("Quick revision notes for Polity")
        assert intent.type == IntentType.REVISION

    @pytest.mark.asyncio
    async def test_detect_book_question(self):
        intent = await self.router.detect("Explain chapter 4 of Laxmikanth")
        assert intent.type in (IntentType.BOOK_EXPLANATION, IntentType.LEARN_CONCEPT)

    @pytest.mark.asyncio
    async def test_clarification_on_empty(self):
        intent = await self.router.detect("xyzabc")
        assert intent.type == IntentType.CLARIFICATION

    @pytest.mark.asyncio
    async def test_extract_entities(self):
        intent = await self.router.detect("Explain Fundamental Rights in Polity")
        assert intent.type == IntentType.LEARN_CONCEPT
        assert "topic" in intent.extracted_entities
        assert "subject" in intent.extracted_entities

    @pytest.mark.asyncio
    async def test_mentor_coaching(self):
        intent = await self.router.detect("What strategy should I follow for History?")
        assert intent.type in (IntentType.MENTOR_COACHING, IntentType.LEARN_CONCEPT)

    @pytest.mark.asyncio
    async def test_air_prediction(self):
        intent = await self.router.detect("What rank can I expect with 60% accuracy?")
        assert intent.type == IntentType.AIR_PREDICTION


class TestContextRanker:
    def setup_method(self):
        self.ranker = ContextRanker()

    @pytest.mark.asyncio
    async def test_rank_empty(self):
        result = await self.ranker.rank([], None)
        assert result == []

    @pytest.mark.asyncio
    async def test_rank_preserves_order(self):
        ev1 = Evidence(
            content_id=uuid.uuid4(), content_type="lesson", title="A",
            snippet="test", source="book", score=0.9,
        )
        ev2 = Evidence(
            content_id=uuid.uuid4(), content_type="lesson", title="B",
            snippet="test", source="pyq", score=0.5,
        )
        result = await self.ranker.rank([ev1, ev2])
        assert result[0].score >= result[1].score

    @pytest.mark.asyncio
    async def test_weakness_boost(self):
        ev = Evidence(
            content_id=uuid.uuid4(), content_type="topic", title="Constitution",
            snippet="test", source="syllabus", score=0.5,
            syllabus_node_id=uuid.uuid4(), syllabus_node_type="topic",
        )
        ctx = StudentContext(
            student_id=uuid.uuid4(),
            mastery_scores={str(ev.syllabus_node_id): 0.3},
        )
        result = await self.ranker.rank([ev], ctx)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_rerank_with_query(self):
        ev = Evidence(
            content_id=uuid.uuid4(), content_type="lesson", title="Fundamental Rights",
            snippet="Rights in Constitution", source="book", score=0.5,
        )
        result = await self.ranker.rerank_with_query([ev], "fundamental rights")
        assert result[0].score > 0.5


class TestContextCompressor:
    def setup_method(self):
        self.compressor = ContextCompressor(max_tokens=500)

    @pytest.mark.asyncio
    async def test_compress_empty(self):
        result = await self.compressor.compress([], max_evidence=5)
        assert len(result.evidence) == 0

    @pytest.mark.asyncio
    async def test_compress_deduplicates(self):
        ev = Evidence(
            content_id=uuid.uuid4(), content_type="lesson", title="Test",
            snippet="Same content here for testing", source="book", score=0.8,
        )
        result = await self.compressor.compress([ev, ev], max_evidence=5)
        assert len(result.evidence) <= 1

    @pytest.mark.asyncio
    async def test_compress_removes_low_score(self):
        ev1 = Evidence(
            content_id=uuid.uuid4(), content_type="lesson", title="High",
            snippet="Good content", source="book", score=0.8,
        )
        ev2 = Evidence(
            content_id=uuid.uuid4(), content_type="lesson", title="Low",
            snippet="Bad content", source="book", score=0.05,
        )
        result = await self.compressor.compress([ev1, ev2], min_score=0.1)
        assert len(result.evidence) == 1
        assert result.evidence[0].score == 0.8


class TestSemanticCache:
    def setup_method(self):
        self.cache = SemanticCache(max_size=10, ttl_seconds=60)

    def test_set_and_get(self):
        self.cache.set("test", {"id": 1}, "value")
        result = self.cache.get("test", {"id": 1})
        assert result == "value"

    def test_miss(self):
        result = self.cache.get("test", {"id": 999})
        assert result is None

    def test_eviction(self):
        for i in range(15):
            self.cache.set("test", {"i": i}, f"v{i}")
        assert len(self.cache._cache) <= 10

    def test_hit_rate(self):
        self.cache.set("a", {"k": 1}, "v1")
        self.cache.get("a", {"k": 1})
        self.cache.get("a", {"k": 2})
        assert self.cache.hit_rate() == 0.5


class TestAICostOptimizer:
    def setup_method(self):
        self.opt = AICostOptimizer()

    def test_select_budget_for_small(self):
        model = self.opt.select_model("revision", 300)
        assert model in ("gpt-4o-mini", "claude-3-haiku", "gemini-1.5-flash")

    def test_select_premium_for_complex(self):
        model = self.opt.select_model("learn_concept", 3000)
        assert model in ("gpt-4o", "claude-3.5-sonnet", "gemini-1.5-pro")

    def test_track_usage(self):
        self.opt.track_usage("gpt-4o-mini", 500)
        summary = self.opt.usage_summary()
        assert summary["total_tokens"] == 500
        assert summary["total_cost"] > 0


class TestStreamingEngine:
    def setup_method(self):
        self.engine = StreamingEngine()

    @pytest.mark.asyncio
    async def test_stream_response(self):
        response = BrainResponse(
            answer="Test answer for UPSC preparation.",
            intent=Intent(type=IntentType.LEARN_CONCEPT, confidence=0.8, raw_query="test"),
        )
        events = []
        async for event in self.engine.stream_response(response):
            events.append(event)
        assert len(events) > 0
        assert any("event: start" in e for e in events)
        assert any("event: complete" in e for e in events)

    def test_cancel(self):
        stream_id = "test-stream"
        self.engine.active_streams[stream_id] = 100.0
        assert self.engine.cancel(stream_id) is True
        assert stream_id not in self.engine.active_streams
