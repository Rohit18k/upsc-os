import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MetricSample:
    intent: str
    retrieval_latency: float
    llm_latency: float
    total_latency: float
    cache_hit: bool
    token_count: int
    model: str
    evidence_count: int
    confidence: float
    cost: float
    hallucination_blocked: bool


class BrainMetrics:
    def __init__(self):
        self.samples: List[MetricSample] = []
        self._counts: Dict[str, int] = {}

    def record(self, sample: MetricSample):
        self.samples.append(sample)
        self._counts[sample.intent] = self._counts.get(sample.intent, 0) + 1

    def summary(self) -> Dict:
        if not self.samples:
            return {"status": "no_data"}

        recent = self.samples[-1000:]
        total_time = sum(s.total_latency for s in recent)
        avg_total = total_time / len(recent)
        avg_retrieval = sum(s.retrieval_latency for s in recent) / len(recent)
        avg_llm = sum(s.llm_latency for s in recent) / len(recent)
        avg_confidence = sum(s.confidence for s in recent) / len(recent)
        cache_hits = sum(1 for s in recent if s.cache_hit)
        hallucination_blocks = sum(1 for s in recent if s.hallucination_blocked)
        total_cost = sum(s.cost for s in recent)

        return {
            "total_queries": len(recent),
            "avg_latency_ms": round(avg_total * 1000, 1),
            "avg_retrieval_latency_ms": round(avg_retrieval * 1000, 1),
            "avg_llm_latency_ms": round(avg_llm * 1000, 1),
            "avg_confidence": round(avg_confidence, 3),
            "cache_hit_rate": round(cache_hits / len(recent), 3),
            "hallucination_blocked": hallucination_blocks,
            "total_cost": round(total_cost, 6),
            "intent_breakdown": self._counts,
        }

    def to_prometheus(self) -> str:
        s = self.summary()
        lines = [
            "# HELP brain_total_queries Total queries processed",
            f"brain_total_queries {s.get('total_queries', 0)}",
            "# HELP brain_avg_latency_ms Average latency",
            f"brain_avg_latency_ms {s.get('avg_latency_ms', 0)}",
            "# HELP brain_avg_confidence Average confidence",
            f"brain_avg_confidence {s.get('avg_confidence', 0)}",
            "# HELP brain_cache_hit_rate Cache hit ratio",
            f"brain_cache_hit_rate {s.get('cache_hit_rate', 0)}",
            "# HELP brain_total_cost Total cost",
            f"brain_total_cost {s.get('total_cost', 0)}",
        ]
        for intent, count in self._counts.items():
            lines.append(f'brain_intent_count{{intent="{intent}"}} {count}')
        return "\n".join(lines) + "\n"


metrics = BrainMetrics()
