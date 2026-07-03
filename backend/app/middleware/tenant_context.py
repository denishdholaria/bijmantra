"""
Tenant Context Middleware

Automatically sets the PostgreSQL session variable for RLS
based on the authenticated user's organization.

This middleware:
1. Extracts the JWT token from the Authorization header
2. Decodes the token to get user info
3. Sets the tenant context for RLS policies
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.keycloak_auth import (
    KeycloakTokenError,
    is_configured_keycloak_issuer_token,
    resolve_keycloak_user,
    verify_keycloak_token,
)
from app.core.security import decode_access_token
from app.models.core import User


logger = logging.getLogger(__name__)

RLS_ORGANIZATION_SETTING = "app.current_organization_id"
RLS_USER_SETTING = "app.current_user_id"


def _safe_int_context(value: object, default: int = -1) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning("Invalid RLS integer context value; using restricted default")
        return default


async def _set_local_config(session: AsyncSession, key: str, value: int) -> None:
    await session.execute(
        text("SELECT set_config(:key, :value, true)"),
        {"key": key, "value": str(value)},
    )


async def apply_tenant_context(
    session: AsyncSession,
    organization_id: object | None,
    is_superuser: bool = False,
    user_id: object | None = None,
) -> None:
    """Apply transaction-local RLS context for tenant and user-owned policies."""
    org_context = 0 if is_superuser else _safe_int_context(organization_id)
    user_context = _safe_int_context(user_id)

    await _set_local_config(session, RLS_ORGANIZATION_SETTING, org_context)
    await _set_local_config(session, RLS_USER_SETTING, user_context)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set tenant context for Row-Level Security.

    For each request:
    1. Extract JWT token from Authorization header
    2. Decode to get organization_id and is_superuser
    3. Store in request.state for use by dependencies

    The actual RLS context is set in the database dependency
    (get_db_with_tenant) to ensure it's within the same transaction.
    """

    # Paths that don't require tenant context
    EXEMPT_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v2/auth/login",
        "/api/v2/auth/register",
        "/api/v2/auth/refresh",
        "/api/v2/gdd/ping",
        "/api/v2/gdd/health",
        "/api/v2/gdd/test",
        "/api/v2/gdd/calculate",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tenant context for exempt paths
        path = request.url.path
        if path in self.EXEMPT_PATHS or path.startswith("/static"):
            return await call_next(request)

        # Extract tenant info from JWT
        tenant_info = await self._extract_tenant_info(request)

        # Store in request state for database dependency
        request.state.organization_id = tenant_info.get("organization_id")
        request.state.is_superuser = tenant_info.get("is_superuser", False)
        request.state.user_id = tenant_info.get("user_id")

        # Log for debugging
        if tenant_info.get("organization_id"):
            logger.debug(
                f"Tenant context: org_id={tenant_info['organization_id']}, "
                f"superuser={tenant_info['is_superuser']}"
            )

        return await call_next(request)

    async def _extract_tenant_info(self, request: Request) -> dict:
        """Extract tenant information from JWT token."""
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return {}

        token = auth_header.split(" ")[1]

        if settings.KEYCLOAK_ENABLED and is_configured_keycloak_issuer_token(token):
            return await self._extract_keycloak_tenant_info(token)

        payload = decode_access_token(token)

        if payload:
            token_context = {
                "organization_id": payload.get("organization_id"),
                "is_superuser": payload.get("is_superuser", False),
                "user_id": payload.get("sub"),
            }
            if payload.get("organization_id") is not None and payload.get("sub") is not None:
                return token_context

            resolved_context = await self._resolve_local_token_context(payload)
            return resolved_context or token_context

        if settings.KEYCLOAK_ENABLED:
            return await self._extract_keycloak_tenant_info(token)

        return {}

    async def _resolve_local_token_context(self, payload: dict) -> dict:
        """Resolve tenant context for legacy local JWTs missing organization claims."""
        user_id = payload.get("sub")
        if user_id is None:
            return {}

        try:
            user_pk = int(user_id)
        except (TypeError, ValueError):
            return {}

        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_pk)
            if user is None or not user.is_active:
                return {}

            return {
                "organization_id": user.organization_id,
                "is_superuser": user.is_superuser,
                "user_id": user.id,
            }

    async def _extract_keycloak_tenant_info(self, token: str) -> dict:
        """Resolve tenant context from a verified Keycloak token."""
        try:
            claims = await verify_keycloak_token(token)
        except KeycloakTokenError:
            return {}

        async with AsyncSessionLocal() as session:
            user = await resolve_keycloak_user(session, claims)
            if user is None:
                return {}

            return {
                "organization_id": user.organization_id,
                "is_superuser": user.is_superuser,
                "user_id": user.id,
            }


async def get_db_with_tenant() -> AsyncSession:
    """
    Database dependency that sets RLS tenant context.

    This should be used instead of get_db() for endpoints
    that need tenant isolation.

    Usage:
        @router.get("/programs")
        async def list_programs(
            db: AsyncSession = Depends(get_db_with_tenant)
        ):
            # All queries automatically filtered by organization_id
            result = await db.execute(select(Program))
            return result.scalars().all()
    """

    async with AsyncSessionLocal() as session:
        try:
            # Note: This function needs the request context
            # In practice, use the dependency below
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class TenantDatabaseDependency:
    """
    Callable dependency class for tenant-aware database sessions.

    Usage:
        get_tenant_db = TenantDatabaseDependency()

        @router.get("/programs")
        async def list_programs(
            db: AsyncSession = Depends(get_tenant_db)
        ):
            result = await db.execute(select(Program))
            return result.scalars().all()
    """

    async def __call__(self, request: Request) -> AsyncSession:
        async with AsyncSessionLocal() as session:
            try:
                # Set tenant context from request state
                org_id = getattr(request.state, "organization_id", None)
                is_superuser = getattr(request.state, "is_superuser", False)
                user_id = getattr(request.state, "user_id", None)

                await apply_tenant_context(
                    session,
                    organization_id=org_id,
                    is_superuser=is_superuser,
                    user_id=user_id,
                )

                if is_superuser:
                    logger.debug("RLS: Superuser mode (bypass)")
                elif org_id:
                    logger.debug(f"RLS: Tenant mode (org_id={org_id})")
                else:
                    logger.debug("RLS: No tenant context (restricted)")

                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Create singleton instance
get_tenant_db = TenantDatabaseDependency()
