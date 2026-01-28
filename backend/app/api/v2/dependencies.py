"""
API Dependencies
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.core import user as crud_user
from app.models.core import User
from app.middleware.tenant_context import get_tenant_db


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_tenant_db)
) -> User:
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
