from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    trace_id: str
    instance: Optional[str] = None
    errors: Optional[List[Dict[str, str]]] = None


def success_response(data: Any = None, message: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    if meta:
        response["meta"] = meta
    return response


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "success": True,
        "data": items,
        "meta": {
            "pagination": PaginationMeta(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1,
            )
        },
    }
