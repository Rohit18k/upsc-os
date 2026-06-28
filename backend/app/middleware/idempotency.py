import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.redis_pool import redis_pool

logger = logging.getLogger("middleware.idempotency")


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Guarantees POST operations are idempotent if an Idempotency-Key header is supplied.
    Stores cached response payload, headers, and HTTP status code in Redis for 5 minutes.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method != "POST":
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        client = redis_pool.client
        if not client:
            return await call_next(request)

        redis_key = f"idempotency:{idempotency_key}"
        lock_key = f"idempotency_lock:{idempotency_key}"

        try:
            # 1. Check for existing processed request response
            cached_data = client.get(redis_key)
            if cached_data:
                logger.info(f"Idempotency hit for key={idempotency_key}")
                payload = json.loads(cached_data)
                return JSONResponse(
                    status_code=payload["status_code"],
                    content=payload["body"],
                    headers=payload["headers"]
                )

            # 2. Prevent concurrent processing of the exact same key (race conditions)
            # Try to acquire lock for 10 seconds
            is_locked = client.set(lock_key, "processing", ex=10, nx=True)
            if not is_locked:
                return JSONResponse(
                    status_code=409,
                    content={
                        "type": "idempotency-conflict",
                        "title": "Conflict",
                        "status": 409,
                        "detail": "A request with this idempotency key is already in progress.",
                    }
                )

            # Process downstream request
            response = await call_next(request)

            # Only cache safe responses (2xx and 4xx, avoid caching 5xx transient failures)
            if response.status_code < 500:
                # Capture body for caching
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                try:
                    body_dict = json.loads(response_body.decode("utf-8"))
                except Exception:
                    body_dict = response_body.decode("utf-8")

                # Structure response payload cache
                cache_payload = {
                    "status_code": response.status_code,
                    "body": body_dict,
                    "headers": dict(response.headers)
                }

                client.set(redis_key, json.dumps(cache_payload), ex=300)

                # Return fresh response matching the consumed stream
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

            return response

        except Exception as e:
            logger.error(f"Idempotency handler failed: {e}")
            return await call_next(request)
        finally:
            # Clean up concurrency lock
            try:
                client.delete(lock_key)
            except Exception:
                pass
