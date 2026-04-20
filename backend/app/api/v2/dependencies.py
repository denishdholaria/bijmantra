"""
API Dependencies

DEPRECATED (ADR-005): Use app.api.deps instead.
This module provides a parallel get_current_user that uses request.state
instead of JWT token decode. All new code should import from app.api.deps.
This file will be removed once all consumers have migrated.
"""

import warnings
warnings.warn(
    "app.api.v2.dependencies is deprecated. Use app.api.deps instead (ADR-005).",
    DeprecationWarning,
    stacklevel=2,
)

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.core import user as crud_user
from app.middleware.tenant_context import get_tenant_db
from app.models.core import User


async def get_current_user(request: Request, db: AsyncSession = Depends(get_tenant_db)) -> User:
    """
    Get current user from request state and database.
    """
    user_id = getattr(request.state, "user_id", None)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await crud_user.get(db, id=user_id)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user
