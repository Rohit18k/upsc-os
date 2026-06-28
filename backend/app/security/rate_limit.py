from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import time
import logging
from app.core.redis_pool import redis_pool

logger = logging.getLogger(__name__)


@dataclass
class RateLimitRule:
    requests: int
    window_seconds: int
    group: str = "default"


class TokenBucketRateLimiter:
    def __init__(self):
        self.buckets: Dict[str, Tuple[float, int]] = {}

    def check(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        now = time.time()
        client = redis_pool.client
        if client:
            try:
                redis_key = f"rate_limit:{key}"
                data = client.get(redis_key)
                if not data:
                    tokens = max_requests - 1
                    client.set(redis_key, f"{tokens}:{now}", ex=window_seconds)
                    return True, tokens

                parts = data.split(":")
                if len(parts) == 2:
                    tokens_val = float(parts[0])
                    last_time = float(parts[1])
                else:
                    tokens_val = float(max_requests)
                    last_time = now

                elapsed = now - last_time
                tokens = min(max_requests, tokens_val + (elapsed * max_requests / window_seconds))
                tokens = int(tokens)

                if tokens > 0:
                    client.set(redis_key, f"{tokens - 1}:{now}", ex=window_seconds)
                    return True, tokens - 1

                client.set(redis_key, f"0:{now}", ex=window_seconds)
                return False, 0
            except Exception as e:
                logger.warning(f"Redis rate limiter failed: {e}. Falling back to in-memory rate limiting.")

        # In-memory fallback
        if key not in self.buckets:
            self.buckets[key] = (now, max_requests - 1)
            return True, max_requests - 1

        last_time, tokens = self.buckets[key]
        elapsed = now - last_time
        tokens = min(max_requests, tokens + (elapsed * max_requests / window_seconds))
        tokens = int(tokens)

        if tokens > 0:
            self.buckets[key] = (now, tokens - 1)
            return True, tokens - 1

        return False, 0

    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        client = redis_pool.client
        if client:
            try:
                redis_key = f"rate_limit:{key}"
                data = client.get(redis_key)
                if not data:
                    return max_requests
                parts = data.split(":")
                if len(parts) == 2:
                    tokens_val = float(parts[0])
                    last_time = float(parts[1])
                else:
                    return max_requests

                now = time.time()
                elapsed = now - last_time
                tokens = min(max_requests, tokens_val + (elapsed * max_requests / window_seconds))
                return max(0, int(tokens))
            except Exception:
                pass

        if key not in self.buckets:
            return max_requests
        _, tokens = self.buckets[key]
        return max(0, tokens)


rate_limiter = TokenBucketRateLimiter()

