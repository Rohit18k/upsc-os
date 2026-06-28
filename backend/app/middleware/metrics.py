import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_LATENCY_SECONDS


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        # Skip instrumentation on Prometheus metrics scrape route itself
        if path == "/metrics":
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        latency = time.time() - start_time

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=path,
            status=str(response.status_code)
        ).inc()

        HTTP_REQUEST_LATENCY_SECONDS.labels(
            method=request.method,
            path=path
        ).observe(latency)

        return response
