"""
RBAC Row Level Security Middleware

This middleware provides fine-grained Role-Based Access Control (RBAC)
integrated with Row-Level Security (RLS) policies.

It extends the standard tenant isolation by adding user-specific context
to the database session, enabling policies that filter based on:
1. Organization ID (Tenant)
2. User ID (Owner)
3. User Roles (RBAC)
4. User Permissions (Capabilities)

Usage:
    # Add middleware to application (if global)
    app.add_middleware(RBACRowLevelSecurityMiddleware)

    # OR use the dependency in routers
    @router.get("/items")
    async def list_items(db: AsyncSession = Depends(get_rbac_db)):
        ...
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.models.core import User


logger = logging.getLogger(__name__)


class RBACRowLevelSecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to establish RBAC and RLS context for each request.

    Extracts user identity and roles from the JWT token.
    If roles/org are missing in the token (legacy tokens), fetches them from DB.
    Sets request.state for downstream dependencies.
    """

    # Paths that don't require context
    EXEMPT_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v2/auth/login",
        "/api/v2/auth/register",
        "/api/v2/auth/refresh",
        "/metrics",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Skip for exempt paths
        path = request.url.path
        if path in self.EXEMPT_PATHS or path.startswith("/static"):
            return await call_next(request)

        # Extract context
        try:
            context = await self._extract_context(request)

            # Store in request state
            request.state.user_id = context.get("user_id")
            request.state.organization_id = context.get("organization_id")
            request.state.roles = context.get("roles", [])
            request.state.permissions = context.get("permissions", [])
            request.state.is_superuser = context.get("is_superuser", False)

        except Exception as e:
            # Log error but don't block request (let downstream handle auth errors)
            logger.debug(f"Failed to extract RBAC context: {e}")

        return await call_next(request)

    async def _extract_context(self, request: Request) -> dict:
        """
        Extract user context from Authorization header.
        Fetches from DB if token is incomplete.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {}

        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)

        if not payload:
            return {}

        user_id = payload.get("sub")
        if not user_id:
            return {}

        # Check if token has all needed info (smart token)
        # Note: Current auth implementation only puts 'sub' in token
        # So we likely need to fetch from DB

        organization_id = payload.get("organization_id")
        roles = payload.get("roles")
        permissions = payload.get("permissions")
        is_superuser = payload.get("is_superuser")

        if organization_id is None or roles is None:
            # Fallback: Fetch from DB
            return await self._fetch_user_context(int(user_id))

        return {
            "user_id": int(user_id),
            "organization_id": organization_id,
            "roles": roles,
            "permissions": permissions,
            "is_superuser": is_superuser
        }

    async def _fetch_user_context(self, user_id: int) -> dict:
        """Fetch full user context from database."""
        async with AsyncSessionLocal() as session:
            try:
                stmt = select(User).where(User.id == user_id)
                # Conditionally load roles if relationship exists
                if hasattr(User, "roles"):
                    stmt = stmt.options(selectinload(User.roles))

                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if not user:
                    return {}

                # Extract roles
                # Assuming user.roles is a list of strings or objects with name
                roles_list = []
                if hasattr(user, "roles"):
                    # Check if roles are objects (e.g. Role model) or strings
                    # Usually relationships return objects. Assuming role.name exists or str(role) works.
                    # If it's a JSON column, it's already a list.
                    # Safe fallback: try to extract name or use string repr
                    raw_roles = user.roles
                    if isinstance(raw_roles, list):
                        roles_list = [
                            getattr(r, "name", str(r)) if not isinstance(r, str) else r
                            for r in raw_roles
                        ]

                # Permissions
                permissions_list = []
                if hasattr(user, "permissions"):
                    permissions_list = user.permissions

                return {
                    "user_id": user.id,
                    "organization_id": user.organization_id,
                    "roles": roles_list,
                    "permissions": permissions_list,
                    "is_superuser": user.is_superuser,
                }
            except Exception as e:
                logger.error(f"Error fetching user context for {user_id}: {e}")
                return {}


class RBACDatabaseDependency:
    """
    Dependency to get a database session with full RBAC/RLS context set.
    """

    async def __call__(self, request: Request) -> AsyncSession:
        async with AsyncSessionLocal() as session:
            try:
                # Set context variables
                await self._set_session_context(session, request)

                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def _set_session_context(self, session: AsyncSession, request: Request):
        """Set PostgreSQL session variables for RLS policies using set_config."""

        # Helper to set config safely
        async def set_conf(key: str, value: str):
            await session.execute(
                text(f"SELECT set_config(:key, :value, true)"),
                {"key": key, "value": value}
            )

        # 1. Organization ID (Tenant)
        org_id = getattr(request.state, "organization_id", None)
        is_superuser = getattr(request.state, "is_superuser", False)

        if is_superuser:
            await set_conf("app.current_organization_id", "0")
        elif org_id:
            await set_conf("app.current_organization_id", str(org_id))
        else:
            await set_conf("app.current_organization_id", "-1")

        # 2. User ID (Owner)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
             await set_conf("app.current_user_id", str(user_id))
        else:
             await set_conf("app.current_user_id", "-1")

        # 3. User Roles (RBAC)
        roles = getattr(request.state, "roles", [])
        if roles:
            # Join roles into a comma-separated string
            roles_str = ",".join(str(r) for r in roles)
            await set_conf("app.current_user_roles", roles_str)
        else:
            await set_conf("app.current_user_roles", "")

        # 4. Permissions (Capabilities)
        permissions = getattr(request.state, "permissions", [])
        if permissions:
            perms_str = ",".join(str(p) for p in permissions)
            await set_conf("app.current_user_permissions", perms_str)
        else:
             await set_conf("app.current_user_permissions", "")


# Singleton dependency instance
get_rbac_db = RBACDatabaseDependency()
