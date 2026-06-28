from enum import Enum
from typing import List, Optional, Set


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    READONLY = "readonly"


class Permission(str, Enum):
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    CONTENT_CREATE = "content:create"
    CONTENT_READ = "content:read"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_USERS = "system:users"


ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE,
        Permission.CONTENT_DELETE,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_LOGS,
        Permission.SYSTEM_USERS,
    },
    Role.MANAGER: {
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE,
        Permission.CONTENT_DELETE,
        Permission.SYSTEM_LOGS,
    },
    Role.USER: {
        Permission.USER_READ,
        Permission.CONTENT_READ,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_UPDATE,
    },
    Role.READONLY: {
        Permission.USER_READ,
        Permission.CONTENT_READ,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_permissions_for_role(role: Role) -> Set[Permission]:
    return ROLE_PERMISSIONS.get(role, set())


def require_permission(required_permissions: List[Permission], user_permissions: Set[Permission]) -> bool:
    return all(p in user_permissions for p in required_permissions)
