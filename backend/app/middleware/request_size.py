"""
Request body size limit middleware.
Prevents massive upload abuse and zip bomb attacks.
"""
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


# Default: 10MB for normal requests, configurable per-path
DEFAULT_MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_MAX_BODY_SIZE = 50 * 1024 * 1024  # 50MB for file uploads

UPLOAD_PATHS = [
    "/api/v1/student/upload",
    "/api/v1/student/document",
]


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only check for methods that have a body
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length is None:
            # No content-length header — allow the request but let
            # downstream streaming handlers handle chunked transfers
            return await call_next(request)

        try:
            body_size = int(content_length)
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=400,
                content={
                    "type": "invalid-content-length",
                    "title": "Bad Request",
                    "status": 400,
                    "detail": "Invalid Content-Length header",
                },
            )

        # Determine max size based on path
        path = request.url.path
        max_size = DEFAULT_MAX_BODY_SIZE
        for upload_path in UPLOAD_PATHS:
            if path.startswith(upload_path):
                max_size = UPLOAD_MAX_BODY_SIZE
                break

        if body_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return JSONResponse(
                status_code=413,
                content={
                    "type": "payload-too-large",
                    "title": "Payload Too Large",
                    "status": 413,
                    "detail": f"Request body exceeds maximum allowed size of {max_mb:.0f}MB",
                },
            )

        return await call_next(request)
