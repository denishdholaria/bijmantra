"""Permission dependency/decorator utilities."""

from typing import Callable

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.services.authorization import has_permission


def require_permission(permission_code: str) -> Callable:
    """Dependency factory enforcing a permission code for an endpoint."""

    async def _checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        if current_user.is_superuser:
            return
        allowed = await has_permission(db, current_user.id, permission_code)
        if not allowed:
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission_code}")

    return Depends(_checker)
