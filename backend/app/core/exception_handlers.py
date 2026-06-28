import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.logging import security_logger


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_type: str = "about:blank",
        instance: Optional[str] = None,
        extensions: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_type = error_type
        self.instance = instance
        self.extensions = extensions or {}


class AuthenticationError(AppException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=401, detail=detail, error_type="authentication-error")


class AuthorizationError(AppException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail, error_type="authorization-error")


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail, error_type="not-found")


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=409, detail=detail, error_type="conflict")


class ValidationError(AppException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=422, detail=detail, error_type="validation-error")


class RateLimitError(AppException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail, error_type="rate-limit-exceeded")


def create_problem_response(
    status: int,
    detail: str,
    error_type: str = "about:blank",
    instance: Optional[str] = None,
    trace_id: Optional[str] = None,
    extensions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    response = {
        "type": error_type,
        "title": _get_title_for_status(status),
        "status": status,
        "detail": detail,
        "trace_id": trace_id or str(uuid.uuid4()),
    }
    if instance:
        response["instance"] = instance
    if extensions:
        response.update(extensions)
    return response


def _get_title_for_status(status: int) -> str:
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return titles.get(status, "Error")


async def app_exception_handler(request: Request, exc: AppException):
    trace_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else str(uuid.uuid4())
    return JSONResponse(
        status_code=exc.status_code,
        content=create_problem_response(
            status=exc.status_code,
            detail=exc.detail,
            error_type=exc.error_type,
            instance=str(request.url),
            trace_id=trace_id,
            extensions=exc.extensions,
        ),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else str(uuid.uuid4())
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(l) for l in error.get("loc", [])),
                "message": error.get("msg", "Validation error"),
                "type": error.get("type", ""),
            }
        )
    return JSONResponse(
        status_code=422,
        content=create_problem_response(
            status=422,
            detail="Request validation failed",
            error_type="validation-error",
            instance=str(request.url),
            trace_id=trace_id,
            extensions={"errors": errors},
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else str(uuid.uuid4())
    security_logger.log(
        event="unhandled_exception",
        severity="error",
        ip_address=request.client.host if request.client else None,
        details={"trace_id": trace_id, "path": str(request.url)},
    )
    return JSONResponse(
        status_code=500,
        content=create_problem_response(
            status=500,
            detail="An unexpected error occurred",
            error_type="internal-error",
            instance=str(request.url),
            trace_id=trace_id,
        ),
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
