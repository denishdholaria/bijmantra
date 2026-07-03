"""
API Dependencies
Authentication, authorization, and common dependencies
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.keycloak_auth import (
    KeycloakTokenError,
    is_configured_keycloak_issuer_token,
    resolve_keycloak_user,
    verify_keycloak_token,
)
from app.core.security import decode_access_token
from app.crud.core import user as user_crud
from app.models.core import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def _get_user_from_local_token(db: AsyncSession, token: str) -> User | None:
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id: int | None = payload.get("sub")
    if user_id is None:
        return None

    try:
        user_pk = int(user_id)
    except (TypeError, ValueError):
        return None

    return await user_crud.get(db, id=user_pk)


async def _get_user_from_keycloak_token(db: AsyncSession, token: str) -> User | None:
    if not settings.KEYCLOAK_ENABLED:
        return None

    try:
        claims = await verify_keycloak_token(token)
    except KeycloakTokenError:
        return None

    return await resolve_keycloak_user(db, claims)


async def get_optional_user(
    db: AsyncSession = Depends(get_db), token: str | None = Depends(oauth2_scheme_optional)
) -> User | None:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that work with or without authentication.
    """
    if not token:
        return None

    if settings.KEYCLOAK_ENABLED and is_configured_keycloak_issuer_token(token):
        db_user = await _get_user_from_keycloak_token(db, token)
    else:
        db_user = await _get_user_from_local_token(db, token)
        if db_user is None and settings.KEYCLOAK_ENABLED:
            db_user = await _get_user_from_keycloak_token(db, token)

    if db_user is None or not db_user.is_active:
        return None

    return db_user


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if settings.KEYCLOAK_ENABLED and is_configured_keycloak_issuer_token(token):
        db_user = await _get_user_from_keycloak_token(db, token)
    else:
        db_user = await _get_user_from_local_token(db, token)
        if db_user is None and settings.KEYCLOAK_ENABLED:
            db_user = await _get_user_from_keycloak_token(db, token)

    if db_user is None:
        raise credentials_exception

    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return db_user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user


def get_organization_id(current_user: User = Depends(get_current_active_user)) -> int:
    """
    Get organization ID from current user
    """
    return current_user.organization_id
