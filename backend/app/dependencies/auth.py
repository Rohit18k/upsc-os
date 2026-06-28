from typing import List, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exception_handlers import AuthenticationError, AuthorizationError
from app.security.jwt import decode_token
from app.security.rbac import Permission, Role, require_permission
from app.database.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> str:
    if credentials is None:
        raise AuthenticationError("Authentication required")

    token = credentials.credentials
    payload = decode_token(token, token_type="access")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    request.state.user_id = user_id
    request.state.user_role = payload.get("role", Role.READONLY.value)

    return str(user_id)


async def get_current_user_role(
    request: Request,
    user_id: str = Depends(get_current_user_id),
) -> str:
    return request.state.user_role


class RequirePermissions:
    def __init__(self, permissions: List[Permission]):
        self.permissions = permissions

    async def __call__(
        self,
        request: Request,
        role_str: str = Depends(get_current_user_role),
    ) -> bool:
        try:
            role = Role(role_str)
        except ValueError:
            raise AuthorizationError("Invalid role")

        from app.security.rbac import ROLE_PERMISSIONS
        user_permissions = ROLE_PERMISSIONS.get(role, set())
        if not require_permission(self.permissions, user_permissions):
            raise AuthorizationError("Insufficient permissions")

        return True


async def get_optional_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[str]:
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials, token_type="access")
        user_id = payload.get("sub")
        if user_id:
            request.state.user_id = user_id
            request.state.user_role = payload.get("role", Role.READONLY.value)
        return user_id
    except AuthenticationError:
        return None
