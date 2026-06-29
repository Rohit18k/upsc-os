from typing import Dict, List, Optional

from app.services.brain.models import CompressedContext, Evidence


TOKEN_ESTIMATE = 4


class ContextCompressor:
    def __init__(self, max_tokens: int = 4000, reserved_tokens: int = 500):
        self.max_tokens = max_tokens
        self.reserved_tokens = reserved_tokens
        self.available = max_tokens - reserved_tokens

    async def compress(
        self,
        evidence: List[Evidence],
        max_evidence: int = 15,
        min_score: float = 0.1,
    ) -> CompressedContext:
        filtered = [e for e in evidence if e.score >= min_score]

        deduplicated = self._deduplicate(filtered)

        truncated = deduplicated[:max_evidence]

        compressed = CompressedContext(
            evidence=truncated,
            max_tokens=self.max_tokens,
        )

        total_tokens = 0
        final = []
        for e in truncated:
            snippet_tokens = len(e.snippet.split()) // TOKEN_ESTIMATE
            overhead = 20
            if total_tokens + snippet_tokens + overhead > self.available:
                compressed.truncated = True
                break
            total_tokens += snippet_tokens + overhead
            final.append(e)

        compressed.evidence = final
        compressed.total_tokens = total_tokens
        return compressed

    async def compress_for_prompt(
        self,
        evidence: List[Evidence],
        intent: str,
        max_tokens: int = 3000,
    ) -> str:
        ctx = await self.compress(evidence, max_evidence=12)
        parts = [f"# Retrieved Evidence ({intent})", ""]

        for i, e in enumerate(ctx.evidence, 1):
            parts.append(f"[{i}] {e.source.upper()}: {e.title}")
            parts.append(f"   Score: {e.score:.2f}")
            parts.append(f"   {e.snippet[:500]}")
            parts.append("")

        return "\n".join(parts)

    def _deduplicate(self, items: List[Evidence]) -> List[Evidence]:
        seen = set()
        unique = []
        for item in items:
            key = (item.content_id, item.content_type, item.snippet[:100])
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
