import asyncio
import json
import time
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from app.services.brain.models import BrainResponse


class StreamingEngine:
    def __init__(self, chunk_timeout: float = 30.0):
        self.chunk_timeout = chunk_timeout
        self.active_streams: Dict[str, float] = {}

    async def stream_response(
        self,
        response: BrainResponse,
        token_generator: Optional[Callable] = None,
    ) -> AsyncGenerator[str, None]:
        stream_id = response.conversation_id or str(time.time())
        self.active_streams[stream_id] = time.time()

        try:
            yield self._event("start", {
                "conversation_id": stream_id,
                "intent": response.intent.type.value,
                "evidence_count": len(response.evidence),
            })

            yield self._event("progress", {"step": "retrieval", "status": "complete"})

            yield self._event("evidence", {
                "citations": [
                    {"id": i + 1, "title": e.title, "source": e.source, "score": e.score}
                    for i, e in enumerate(response.evidence[:5])
                ],
            })

            yield self._event("progress", {"step": "reasoning", "status": "in_progress"})

            if token_generator:
                buffer = ""
                async for token in token_generator():
                    buffer += token
                    if len(buffer) >= 20 or token in (".", "!", "?"):
                        yield self._event("token", {"text": buffer})
                        buffer = ""
                        await asyncio.sleep(0.01)
                if buffer:
                    yield self._event("token", {"text": buffer})
            else:
                words = response.answer.split()
                buffer = ""
                for word in words:
                    buffer += word + " "
                    if len(buffer) >= 30:
                        yield self._event("token", {"text": buffer})
                        buffer = ""
                        await asyncio.sleep(0.005)
                if buffer:
                    yield self._event("token", {"text": buffer})

            yield self._event("progress", {"step": "validation", "status": "complete"})

            yield self._event("complete", {
                "confidence": response.confidence,
                "coverage_score": response.coverage_score,
                "model_used": response.model_used,
                "cache_hit": response.cache_hit,
                "grounded": response.grounded,
                "evidence_count": len(response.evidence),
                "next_steps": response.next_steps,
            })

        finally:
            self.active_streams.pop(stream_id, None)

    def _event(self, event_type: str, data: Dict[str, Any]) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    def is_active(self, stream_id: str) -> bool:
        return stream_id in self.active_streams

    def cancel(self, stream_id: str) -> bool:
        if stream_id in self.active_streams:
            self.active_streams.pop(stream_id)
            return True
        return False


stream_engine = StreamingEngine()
