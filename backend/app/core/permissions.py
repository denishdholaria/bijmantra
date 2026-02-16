"""
Parashakti Framework - Permission System

Role-based access control (RBAC) with division-level permissions.
"""

from enum import Enum
from typing import List, Optional, Set
from functools import wraps
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


class Permission(str, Enum):
    """All available permissions in the system."""

    # Plant Sciences Division
    READ_PLANT_SCIENCES = "read:plant_sciences"
    WRITE_PLANT_SCIENCES = "write:plant_sciences"
    ADMIN_PLANT_SCIENCES = "admin:plant_sciences"

    # Seed Bank Division
    READ_SEED_BANK = "read:seed_bank"
    WRITE_SEED_BANK = "write:seed_bank"
    ADMIN_SEED_BANK = "admin:seed_bank"

    # Earth Systems Division
    READ_EARTH_SYSTEMS = "read:earth_systems"
    WRITE_EARTH_SYSTEMS = "write:earth_systems"

    # Commercial Division
    READ_COMMERCIAL = "read:commercial"
    WRITE_COMMERCIAL = "write:commercial"
    ADMIN_COMMERCIAL = "admin:commercial"

    # Integration Hub
    READ_INTEGRATIONS = "read:integrations"
    MANAGE_INTEGRATIONS = "manage:integrations"

    # System Administration
    READ_USERS = "read:users"
    MANAGE_USERS = "manage:users"
    ADMIN_SYSTEM = "admin:system"
    VIEW_AUDIT_LOG = "view:audit_log"


class Role(str, Enum):
    """Predefined roles with permission sets."""
    VIEWER = "viewer"
    BREEDER = "breeder"
    RESEARCHER = "researcher"
    DATA_MANAGER = "data_manager"
    ADMIN = "admin"
    SUPERUSER = "superuser"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.READ_PLANT_SCIENCES,
        Permission.READ_SEED_BANK,
        Permission.READ_EARTH_SYSTEMS,
    },
    Role.BREEDER: {
        Permission.READ_PLANT_SCIENCES,
        Permission.WRITE_PLANT_SCIENCES,
        Permission.READ_SEED_BANK,
        Permission.READ_EARTH_SYSTEMS,
    },
    Role.RESEARCHER: {
        Permission.READ_PLANT_SCIENCES,
        Permission.WRITE_PLANT_SCIENCES,
        Permission.READ_SEED_BANK,
        Permission.WRITE_SEED_BANK,
        Permission.READ_EARTH_SYSTEMS,
        Permission.WRITE_EARTH_SYSTEMS,
        Permission.READ_INTEGRATIONS,
    },
    Role.DATA_MANAGER: {
        Permission.READ_PLANT_SCIENCES,
        Permission.WRITE_PLANT_SCIENCES,
        Permission.ADMIN_PLANT_SCIENCES,
        Permission.READ_SEED_BANK,
        Permission.WRITE_SEED_BANK,
        Permission.READ_EARTH_SYSTEMS,
        Permission.READ_INTEGRATIONS,
        Permission.MANAGE_INTEGRATIONS,
    },
    Role.ADMIN: {
        Permission.READ_PLANT_SCIENCES,
        Permission.WRITE_PLANT_SCIENCES,
        Permission.ADMIN_PLANT_SCIENCES,
        Permission.READ_SEED_BANK,
        Permission.WRITE_SEED_BANK,
        Permission.ADMIN_SEED_BANK,
        Permission.READ_EARTH_SYSTEMS,
        Permission.WRITE_EARTH_SYSTEMS,
        Permission.READ_COMMERCIAL,
        Permission.WRITE_COMMERCIAL,
        Permission.READ_INTEGRATIONS,
        Permission.MANAGE_INTEGRATIONS,
        Permission.READ_USERS,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOG,
    },
    Role.SUPERUSER: set(Permission),  # All permissions
}


def get_role_permissions(role: Role) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())


def get_user_permissions(roles: List[str], extra_permissions: List[str] = None) -> Set[str]:
    """
    Get combined permissions for a user based on their roles.
    
    Args:
        roles: List of role names
        extra_permissions: Additional permissions granted directly
    
    Returns:
        Set of permission strings
    """
    permissions = set()

    for role_name in roles:
        try:
            role = Role(role_name)
            role_perms = get_role_permissions(role)
            permissions.update(p.value for p in role_perms)
        except ValueError:
            pass  # Unknown role, skip

    if extra_permissions:
        permissions.update(extra_permissions)

    return permissions


class PermissionChecker:
    """
    Dependency for checking permissions on endpoints.
    
    Usage:
        @router.get("/programs")
        async def list_programs(
            _: None = Depends(PermissionChecker([Permission.READ_PLANT_SCIENCES]))
        ):
            ...
    """

    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> None:
        # Get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
            )

        # Superusers bypass permission checks
        if getattr(user, "is_superuser", False):
            return

        # Get user's permissions
        user_roles = getattr(user, "roles", [])
        user_extra_perms = getattr(user, "permissions", [])
        user_permissions = get_user_permissions(user_roles, user_extra_perms)

        # Check required permissions
        required = {p.value for p in self.required_permissions}
        missing = required - user_permissions

        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"Missing permissions: {', '.join(missing)}",
            )


def require_permissions(*permissions: Permission):
    """
    Decorator for requiring permissions on endpoint functions.
    
    Usage:
        @router.get("/programs")
        @require_permissions(Permission.READ_PLANT_SCIENCES)
        async def list_programs():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Permission check is handled by PermissionChecker dependency
            return await func(*args, **kwargs)

        # Add dependency to function
        if not hasattr(wrapper, "__dependencies__"):
            wrapper.__dependencies__ = []
        wrapper.__dependencies__.append(Depends(PermissionChecker(list(permissions))))

        return wrapper
    return decorator


def require_any_permission(*permissions: Permission):
    """Check if user has ANY of the specified permissions."""

    class AnyPermissionChecker:
        def __init__(self, perms: List[Permission]):
            self.permissions = perms

        async def __call__(self, request: Request) -> None:
            user = getattr(request.state, "user", None)

            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")

            if getattr(user, "is_superuser", False):
                return

            user_roles = getattr(user, "roles", [])
            user_permissions = get_user_permissions(user_roles)
            required = {p.value for p in self.permissions}

            if not required.intersection(user_permissions):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions",
                )

    return Depends(AnyPermissionChecker(list(permissions)))


# Convenience dependencies for common permission checks
require_plant_sciences_read = Depends(PermissionChecker([Permission.READ_PLANT_SCIENCES]))
require_plant_sciences_write = Depends(PermissionChecker([Permission.WRITE_PLANT_SCIENCES]))
require_admin = Depends(PermissionChecker([Permission.ADMIN_SYSTEM]))
