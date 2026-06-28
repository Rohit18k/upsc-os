import secrets
from typing import Optional

from fastapi import Request


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def validate_csrf_token(request: Request, token: str) -> bool:
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token:
        return False
    return secrets.compare_digest(cookie_token, token)


def get_csrf_token_from_header(request: Request) -> Optional[str]:
    return request.headers.get("X-CSRF-Token")
