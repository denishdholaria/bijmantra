"""RBAC permission helpers backed by DB roles/permissions."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_management import Role, UserRole
from app.models.audit import Permission as PermissionModel, RolePermission


async def has_permission(db: AsyncSession, user_id: int, permission_code: str) -> bool:
    """Return True if the user has the provided permission code."""
    stmt = (
        select(Role.permissions, PermissionModel.code)
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .outerjoin(RolePermission, RolePermission.role_id == Role.id)
        .outerjoin(PermissionModel, PermissionModel.id == RolePermission.permission_id)
        .where(UserRole.user_id == user_id)
    )
    result = await db.execute(stmt)
    for role_permissions_json, code in result.all():
        if code == permission_code:
            return True
        if isinstance(role_permissions_json, list) and permission_code in role_permissions_json:
            return True
    return False
