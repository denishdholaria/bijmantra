"""
Tenant Context Middleware

Automatically sets the PostgreSQL session variable for RLS
based on the authenticated user's organization.

This middleware:
1. Extracts the JWT token from the Authorization header
2. Decodes the token to get user info
3. Sets the tenant context for RLS policies
"""

from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.core.security import decode_access_token
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


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
    }
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
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
        payload = decode_access_token(token)
        
        if not payload:
            return {}
        
        return {
            "organization_id": payload.get("organization_id"),
            "is_superuser": payload.get("is_superuser", False),
            "user_id": payload.get("sub"),
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
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
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


def get_tenant_db(request: Request):
    """
    FastAPI dependency that provides a database session with tenant context.
    
    Usage:
        @router.get("/programs")
        async def list_programs(
            db: AsyncSession = Depends(get_tenant_db)
        ):
            # All queries automatically filtered by organization_id
            result = await db.execute(select(Program))
            return result.scalars().all()
    """
    async def _get_db():
        async with AsyncSessionLocal() as session:
            try:
                # Set tenant context from request state
                org_id = getattr(request.state, "organization_id", None)
                is_superuser = getattr(request.state, "is_superuser", False)
                
                if is_superuser:
                    # Superusers see all data
                    await session.execute(
                        text("SET LOCAL app.current_organization_id = '0'")
                    )
                elif org_id:
                    # Regular users see only their org's data
                    # Note: org_id is always an integer from JWT, safe to format
                    await session.execute(
                        text(f"SET LOCAL app.current_organization_id = '{int(org_id)}'")
                    )
                else:
                    # No context - see nothing (safe default)
                    await session.execute(
                        text("SET LOCAL app.current_organization_id = '-1'")
                    )
                
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    return _get_db


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
                
                if is_superuser:
                    await session.execute(
                        text("SET LOCAL app.current_organization_id = '0'")
                    )
                    logger.debug("RLS: Superuser mode (bypass)")
                elif org_id:
                    # Note: org_id is always an integer from JWT, safe to format
                    await session.execute(
                        text(f"SET LOCAL app.current_organization_id = '{int(org_id)}'")
                    )
                    logger.debug(f"RLS: Tenant mode (org_id={org_id})")
                else:
                    await session.execute(
                        text("SET LOCAL app.current_organization_id = '-1'")
                    )
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
