import json
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import audit_logger


def sanitize_log_value(val: str) -> str:
    # Remove newlines, carriage returns, and unprintable characters to prevent log injection
    if not val:
        return ""
    return "".join(c for c in val if c.isprintable() and c not in ("\n", "\r"))


class AuditMiddleware(BaseHTTPMiddleware):
    AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in self.AUDIT_METHODS:
            return await call_next(request)

        correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)

        response = await call_next(request)

        if response.status_code < 500:
            clean_path = sanitize_log_value(request.url.path)
            clean_method = sanitize_log_value(request.method)
            audit_logger.log(
                action=f"{clean_method}_{clean_path}",
                resource=clean_path,
                user_id=user_id,
                ip_address=client_ip,
                correlation_id=correlation_id,
                details={
                    "method": clean_method,
                    "path": clean_path,
                    "status_code": response.status_code,
                },
            )

        return response

