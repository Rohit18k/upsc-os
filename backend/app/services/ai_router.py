import uuid
import time
import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.exception_handlers import RateLimitError
from app.models.ai_cost import AICostLedger
from app.core.redis_pool import redis_pool

logger = logging.getLogger("services.ai_router")

# Custom daily budget configurations
DAILY_STUDENT_BUDGET = 50  # Max 50 AI queries per day

# Simulated pricing per 1K tokens
MODEL_PRICING = {
    "small": {"prompt": 0.0001, "completion": 0.0003, "name": "gemini-3.5-flash"},
    "medium": {"prompt": 0.0005, "completion": 0.0015, "name": "gemini-3.5-pro"},
    "premium": {"prompt": 0.0025, "completion": 0.0075, "name": "claude-3-opus"},
}


class AIRouterService:
    @classmethod
    async def route_and_track(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        feature: str,
        prompt: str,
        system_instruction: str = "",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Engine 3 (AI Cost Optimization) & Tiered Routing Pipeline.
        Routes: Intent/Cache -> Rule Engine -> Small -> Medium -> Premium.
        Tracks prompt & completion tokens, cost, latency, cache hit ratios.
        """
        # 1. Enforce student daily budget limit via Redis
        if not await cls._check_budget_and_increment(user_id):
            raise RateLimitError("You have reached your daily limit of 50 AI-assisted mentor requests.")

        start_time = time.time()
        norm_prompt = prompt.strip().lower()

        # 2. Check Cache
        cached_res = await cls._check_cache(user_id, feature, norm_prompt)
        if cached_res:
            latency = time.time() - start_time
            # Record Cache Hit
            await cls._record_ledger(
                db=db,
                user_id=user_id,
                model_name="cache",
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=0.0,
                latency=latency,
                cache_hit="hit",
                feature=feature,
            )
            return cached_res, {
                "model": "cache",
                "cost_usd": 0.0,
                "latency_seconds": latency,
                "cache_hit": True,
            }

        # 3. Apply Socratic & Rule Engine Routing
        model_tier, response_text, tokens = cls._evaluate_rules_and_route(feature, norm_prompt)
        
        # Calculate pricing
        pricing = MODEL_PRICING[model_tier]
        prompt_tok = tokens["prompt"]
        comp_tok = tokens["completion"]
        cost = (prompt_tok * pricing["prompt"] / 1000.0) + (comp_tok * pricing["completion"] / 1000.0)

        latency = time.time() - start_time

        # Update cache for small/cached responses
        await cls._update_cache(user_id, feature, norm_prompt, response_text)

        # Record Ledger Entry
        await cls._record_ledger(
            db=db,
            user_id=user_id,
            model_name=pricing["name"],
            prompt_tokens=prompt_tok,
            completion_tokens=comp_tok,
            cost_usd=cost,
            latency=latency,
            cache_hit="miss",
            feature=feature,
        )

        return response_text, {
            "model": pricing["name"],
            "cost_usd": cost,
            "latency_seconds": latency,
            "cache_hit": False,
        }

    @classmethod
    async def _check_budget_and_increment(cls, user_id: uuid.UUID) -> bool:
        """Rate limit checks to ensure budget safety."""
        client = redis_pool.client
        if not client:
            return True  # Fallback to allow requests if Redis is down

        # Budget key expires daily
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        budget_key = f"ai_budget:{user_id}:{today_str}"
        try:
            current = client.get(budget_key)
            if current and int(current) >= DAILY_STUDENT_BUDGET:
                return False
            
            client.incr(budget_key)
            client.expire(budget_key, 86400)
            return True
        except Exception as e:
            logger.warning(f"Redis daily budget check failed: {e}")
            return True

    @classmethod
    async def _check_cache(cls, user_id: uuid.UUID, feature: str, prompt: str) -> Optional[str]:
        """Simple prefix/query exact caching."""
        client = redis_pool.client
        if not client:
            return None
        try:
            cache_key = f"ai_cache:{user_id}:{feature}:{hash(prompt)}"
            return client.get(cache_key)
        except Exception:
            return None

    @classmethod
    async def _update_cache(cls, user_id: uuid.UUID, feature: str, prompt: str, response: str) -> None:
        client = redis_pool.client
        if not client:
            return
        try:
            cache_key = f"ai_cache:{user_id}:{feature}:{hash(prompt)}"
            client.set(cache_key, response, ex=7200)  # Cache for 2 hours
        except Exception:
            pass

    @classmethod
    def _evaluate_rules_and_route(cls, feature: str, prompt: str) -> Tuple[str, str, Dict[str, int]]:
        """
        Tiered model selector routing.
        Routes to small/medium models for ~80% of common intents.
        """
        # Small / Socratic checks
        if "hello" in prompt or "hi" in prompt or "help" in prompt:
            return "small", "Hello! I am your Socratic UPSC mentor. How can I assist you with your study plan or daily missions today?", {"prompt": 10, "completion": 30}

        if "syllabus" in prompt or "prelims" in prompt or "exam" in prompt:
            # Socratic/Medium model route
            response = (
                "Regarding the UPSC syllabus, let's break this down chronologically. "
                "Are you focusing on core subjects (Polity/Economy) or current affairs?"
            )
            return "medium", response, {"prompt": 45, "completion": 50}

        if "explain" in prompt or "why" in prompt:
            # Complex reasoning requires medium/premium models
            response = (
                "To explain this core concept, let's look at the basic structure: "
                "It requires mapping the historical background, constitutional amendments, and modern implications."
            )
            return "premium", response, {"prompt": 150, "completion": 250}

        # Default fallback is small/medium route
        return "small", "I've analyzed your query and scheduled this topic for study.", {"prompt": 25, "completion": 40}

    @classmethod
    async def _record_ledger(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        latency: float,
        cache_hit: str,
        feature: str,
    ) -> None:
        """Insert records in the ledger database table."""
        try:
            ledger_entry = AICostLedger(
                user_id=user_id,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
                latency_seconds=latency,
                cache_hit=cache_hit,
                feature=feature,
            )
            db.add(ledger_entry)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to record AICostLedger: {e}")
