from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import time


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
        if key not in self.buckets:
            return max_requests
        _, tokens = self.buckets[key]
        return max(0, tokens)


rate_limiter = TokenBucketRateLimiter()
