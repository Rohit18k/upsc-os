import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from app.services.brain.models import BrainQuery, BrainResponse


class SemanticCache:
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _key(self, prefix: str, data: Any) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return f"{prefix}:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

    def get(self, prefix: str, data: Any) -> Optional[Any]:
        key = self._key(prefix, data)
        entry = self._cache.get(key)
        if entry is None:
            self.misses += 1
            return None
        ts, value = entry
        if time.time() - ts > self.ttl:
            del self._cache[key]
            self.misses += 1
            return None
        self.hits += 1
        return value

    def set(self, prefix: str, data: Any, value: Any):
        key = self._key(prefix, data)
        if len(self._cache) >= self.max_size:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest]
        self._cache[key] = (time.time(), value)

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def clear(self):
        self._cache.clear()
        self.hits = 0
        self.misses = 0


class AICostOptimizer:
    def __init__(self):
        self.intent_cache = SemanticCache(max_size=500, ttl_seconds=300)
        self.response_cache = SemanticCache(max_size=2000, ttl_seconds=86400)
        self.embedding_cache = SemanticCache(max_size=5000, ttl_seconds=86400)
        self.context_cache = SemanticCache(max_size=1000, ttl_seconds=600)
        self._model_usage: Dict[str, int] = {}
        self._total_cost: float = 0.0

    COST_PER_TOKEN = {
        "gpt-4o": 0.00001,
        "gpt-4o-mini": 0.0000015,
        "claude-3.5-sonnet": 0.000003,
        "claude-3-haiku": 0.0000005,
        "gemini-1.5-pro": 0.0000035,
        "gemini-1.5-flash": 0.00000035,
        "default": 0.0000015,
    }

    PREMIUM_MODELS = {"gpt-4o", "claude-3.5-sonnet", "gemini-1.5-pro"}
    BUDGET_MODELS = {"gpt-4o-mini", "claude-3-haiku", "gemini-1.5-flash"}

    async def get_cached_intent(self, query: str) -> Optional[Any]:
        return self.intent_cache.get("intent", {"q": query})

    async def cache_intent(self, query: str, intent: Any):
        self.intent_cache.set("intent", {"q": query}, intent)

    async def get_cached_response(self, query: BrainQuery) -> Optional[BrainResponse]:
        data = {
            "q": query.raw_text,
            "sid": str(query.student_id) if query.student_id else None,
        }
        return self.response_cache.get("response", data)

    async def cache_response(self, query: BrainQuery, response: BrainResponse):
        data = {
            "q": query.raw_text,
            "sid": str(query.student_id) if query.student_id else None,
        }
        self.response_cache.set("response", data, response)

    def select_model(
        self,
        intent_type: str,
        token_count: int,
        preferred: Optional[str] = None,
    ) -> str:
        if preferred and preferred in self.COST_PER_TOKEN:
            return preferred

        if token_count < 500:
            return "gpt-4o-mini"
        if token_count < 2000:
            return "claude-3-haiku"
        if intent_type in ("learn_concept", "answer_review", "air_prediction"):
            return "gpt-4o"
        if intent_type in ("revision", "pyq_discussion", "mission_help"):
            return "gpt-4o-mini"
        return "gemini-1.5-flash"

    def track_usage(self, model: str, tokens: int):
        self._model_usage[model] = self._model_usage.get(model, 0) + tokens
        cost = self.COST_PER_TOKEN.get(model, self.COST_PER_TOKEN["default"])
        self._total_cost += tokens * cost

    def usage_summary(self) -> Dict[str, Any]:
        total_tokens = sum(self._model_usage.values())
        premium_tokens = sum(
            v for k, v in self._model_usage.items() if k in self.PREMIUM_MODELS
        )
        return {
            "total_tokens": total_tokens,
            "total_cost": round(self._total_cost, 6),
            "model_breakdown": self._model_usage,
            "premium_ratio": round(premium_tokens / max(total_tokens, 1), 4),
            "intent_cache_hit_rate": round(self.intent_cache.hit_rate(), 3),
            "response_cache_hit_rate": round(self.response_cache.hit_rate(), 3),
        }


cost_optimizer = AICostOptimizer()
