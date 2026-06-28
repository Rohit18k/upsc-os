"""
Shared Redis connection pool with circuit breaker.
Provides graceful degradation when Redis is unavailable.
"""
import logging
import time
from typing import Optional

import redis

from app.config.settings import get_settings

logger = logging.getLogger("core.redis")
settings = get_settings()


class CircuitBreaker:
    """
    Simple circuit breaker implementation.
    States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing recovery)
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} consecutive failures. "
                f"Will retry after {self.recovery_timeout}s."
            )

    def record_success(self) -> None:
        self.failure_count = 0
        self.last_failure_time = None
        if self.state != "CLOSED":
            logger.info("Circuit breaker CLOSED — service recovered.")
        self.state = "CLOSED"

    def is_available(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN" and self.last_failure_time:
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker HALF_OPEN — testing recovery.")
                return True
        return False


class RedisPool:
    """
    Managed Redis connection pool with circuit breaker.
    Thread-safe singleton — initialize once, reuse everywhere.
    """

    def __init__(self):
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        self._initialized = False

    def _ensure_pool(self) -> None:
        if not self._initialized:
            try:
                self._pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=20,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=3.0,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                self._client = redis.Redis(connection_pool=self._pool)
                self._initialized = True
                logger.info("Redis connection pool initialized successfully.")
            except Exception as e:
                logger.warning(f"Redis connection pool initialization failed: {e}")
                self._circuit.record_failure()

    @property
    def client(self) -> Optional[redis.Redis]:
        """
        Get Redis client if circuit is closed.
        Returns None if Redis is unavailable (graceful degradation).
        """
        if not self._circuit.is_available():
            return None

        self._ensure_pool()
        return self._client

    def get(self, key: str) -> Optional[str]:
        """Safe Redis GET with circuit breaker."""
        client = self.client
        if client is None:
            return None
        try:
            result = client.get(key)
            self._circuit.record_success()
            return result
        except Exception as e:
            logger.warning(f"Redis GET failed for key={key}: {e}")
            self._circuit.record_failure()
            return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Safe Redis SET with circuit breaker."""
        client = self.client
        if client is None:
            return False
        try:
            client.set(key, value, ex=ex)
            self._circuit.record_success()
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for key={key}: {e}")
            self._circuit.record_failure()
            return False

    def delete(self, key: str) -> bool:
        """Safe Redis DELETE with circuit breaker."""
        client = self.client
        if client is None:
            return False
        try:
            client.delete(key)
            self._circuit.record_success()
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE failed for key={key}: {e}")
            self._circuit.record_failure()
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Safe Redis INCR with circuit breaker."""
        client = self.client
        if client is None:
            return None
        try:
            result = client.incr(key, amount)
            self._circuit.record_success()
            return result
        except Exception as e:
            logger.warning(f"Redis INCR failed for key={key}: {e}")
            self._circuit.record_failure()
            return None

    def expire(self, key: str, seconds: int) -> bool:
        """Safe Redis EXPIRE with circuit breaker."""
        client = self.client
        if client is None:
            return False
        try:
            client.expire(key, seconds)
            self._circuit.record_success()
            return True
        except Exception as e:
            logger.warning(f"Redis EXPIRE failed for key={key}: {e}")
            self._circuit.record_failure()
            return False

    def ping(self) -> bool:
        """Check Redis connectivity."""
        client = self.client
        if client is None:
            return False
        try:
            client.ping()
            self._circuit.record_success()
            return True
        except Exception:
            self._circuit.record_failure()
            return False


# Singleton instance
redis_pool = RedisPool()
