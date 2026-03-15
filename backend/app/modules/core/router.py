"""
Core Domain API Router

Handles authentication, authorization, audit, and system management endpoints.
Consolidates core infrastructure endpoints under /api/v2/core namespace.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, get_client_ip
from app.crud.core import user as user_crud
from app.models.core import User as UserModel
from app.schemas.core import User, UserCreate
from app.modules.core.services.rate_limiter_service import RateLimitType, rate_limiter
from app.modules.core.services.authorization_service import has_permission

from datetime import UTC, datetime, timedelta
from pydantic import BaseModel


router = APIRouter(prefix="/core", tags=["Core Domain"])


# ============================================
# SCHEMAS
# ============================================

class Token(BaseModel):
    """Token response with user and organization info"""
    access_token: str
    token_type: str = "bearer"
    user: dict | None = None


class PermissionCheck(BaseModel):
    """Permission check request"""
    permission_code: str


class PermissionResponse(BaseModel):
    """Permission check response"""
    has_permission: bool


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

# Note: Login endpoint is kept at /api/auth/login for backward compatibility
# This router provides additional core domain endpoints


@router.get("/health")
async def health_check():
    """
    Health check endpoint for core domain services
    """
    return {
        "status": "healthy",
        "domain": "core",
        "services": ["authorization", "audit", "event_bus", "rate_limiter", "job_service"]
    }


# ============================================
# AUTHORIZATION ENDPOINTS
# ============================================

@router.post("/permissions/check", response_model=PermissionResponse)
async def check_permission(
    permission_check: PermissionCheck,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Check if the current user has a specific permission
    
    Args:
        permission_check: Permission code to check
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        PermissionResponse with has_permission boolean
    """
    has_perm = await has_permission(db, current_user.id, permission_check.permission_code)
    return PermissionResponse(has_permission=has_perm)


@router.get("/permissions/me")
async def get_my_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all permissions for the current user
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of permission codes the user has
    """
    # This is a placeholder - would need to implement get_user_permissions in authorization_service
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "permissions": []  # TODO: Implement get_user_permissions
    }


# ============================================
# USER MANAGEMENT ENDPOINTS
# ============================================

@router.get("/users/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user


# ============================================
# RATE LIMITING ENDPOINTS
# ============================================

@router.get("/rate-limits/status")
async def get_rate_limit_status(
    request: Request,
    limit_type: str = "api"
):
    """
    Check rate limit status for the current client
    
    Args:
        request: HTTP request
        limit_type: Type of rate limit to check (api, login, export)
        
    Returns:
        Rate limit status information
    """
    client_ip = get_client_ip(request)
    
    # Map string to enum
    rate_type_map = {
        "api": RateLimitType.API,
        "login": RateLimitType.LOGIN,
        "export": RateLimitType.EXPORT
    }
    
    rate_type = rate_type_map.get(limit_type, RateLimitType.API)
    rate_check = await rate_limiter.check(rate_type, client_ip)
    
    return {
        "allowed": rate_check.allowed,
        "remaining": rate_check.remaining,
        "limit": rate_check.limit,
        "retry_after": rate_check.retry_after,
        "reset_at": rate_check.reset_at.isoformat() if rate_check.reset_at else None
    }
