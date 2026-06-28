from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from app.config.settings import get_settings
from app.security.rate_limit import rate_limiter

settings = get_settings()

PUBLIC_ENDPOINTS = [
    "/health",
    "/liveness",
    "/readiness",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/docs",
    "/api/redoc",
    "/openapi.json",
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(ep) for ep in PUBLIC_ENDPOINTS):
            max_requests = settings.RATE_LIMIT_REQUESTS * 2
        else:
            max_requests = settings.RATE_LIMIT_REQUESTS

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{path}"

        allowed, remaining = rate_limiter.check(key, max_requests, settings.RATE_LIMIT_WINDOW)

        if not allowed:
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "type": "rate-limit-exceeded",
                    "title": "Too Many Requests",
                    "status": HTTP_429_TOO_MANY_REQUESTS,
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": settings.RATE_LIMIT_WINDOW,
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(settings.RATE_LIMIT_WINDOW),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
