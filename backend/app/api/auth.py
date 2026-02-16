"""
Authentication endpoints
Login, register, token management
"""

from typing import Optional
import re
import secrets
from datetime import datetime, timezone
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.core import user as user_crud
from app.schemas.core import User, UserCreate
from app.api.deps import get_current_user
from app.models.core import User as UserModel, Organization
from app.services.rate_limiter import rate_limiter, RateLimitType

router = APIRouter()


class Token(BaseModel):
    """Token response with user and organization info"""
    access_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None


class TokenData(BaseModel):
    """Token data"""
    user_id: Optional[int] = None



_FAILED_LOGIN_ATTEMPTS: dict[str, dict] = {}
_PASSWORD_ROTATION_DAYS = 90


def _is_strong_password(password: str) -> bool:
    return (
        len(password) >= 10
        and bool(re.search(r"[A-Z]", password))
        and bool(re.search(r"[a-z]", password))
        and bool(re.search(r"[0-9]", password))
        and bool(re.search(r"[^A-Za-z0-9]", password))
    )


def _is_locked(email: str) -> bool:
    record = _FAILED_LOGIN_ATTEMPTS.get(email)
    if not record:
        return False
    until = record.get("locked_until")
    return bool(until and datetime.now(timezone.utc) < until)


def _record_failed_login(email: str) -> None:
    rec = _FAILED_LOGIN_ATTEMPTS.setdefault(email, {"count": 0, "locked_until": None})
    rec["count"] += 1
    if rec["count"] >= 5:
        rec["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=15)


def _clear_failed_login(email: str) -> None:
    if email in _FAILED_LOGIN_ATTEMPTS:
        del _FAILED_LOGIN_ATTEMPTS[email]

def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check X-Forwarded-For header (set by reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP (original client)
        return forwarded.split(",")[0].strip()

    # Check X-Real-IP header (set by some proxies)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login.
    
    Rate limited: 5 attempts per 15 minutes per IP.
    
    Returns token along with user and organization info so frontend can:
    1. Determine if user is in Demo Organization
    2. Set appropriate UI state
    3. Filter data accordingly
    """
    # Rate limit check (M2 fix)
    client_ip = _get_client_ip(request)
    rate_check = await rate_limiter.check(RateLimitType.LOGIN, client_ip)

    if not rate_check.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {rate_check.retry_after} seconds.",
            headers={
                "Retry-After": str(rate_check.retry_after),
                "X-RateLimit-Limit": "5",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": rate_check.reset_at.isoformat(),
            },
        )
    
    if _is_locked(form_data.username):
        raise HTTPException(status_code=423, detail="Account temporarily locked due to failed login attempts")

    user = await user_crud.authenticate(
        db,
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        _record_failed_login(form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer",
                "X-RateLimit-Remaining": str(rate_check.remaining),
            },
        )
    
    _clear_failed_login(form_data.username)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Fetch organization info
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    organization = org_result.scalar_one_or_none()

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    # Determine if this is a demo user
    is_demo = (
        user.email == "demo@bijmantra.org" or
        (organization and organization.name == "Demo Organization")
    )

    # Get user roles
    user_roles = []
    user_permissions = []
    if user.is_superuser:
        user_roles = ["superuser"]
        # Superusers have all permissions - import from permissions module
        from app.core.permissions import Permission
        user_permissions = [p.value for p in Permission]
    else:
        # Get roles from user_roles relationship
        user_roles = user.roles if hasattr(user, 'roles') else []
        user_permissions = user.permissions if hasattr(user, 'permissions') else []

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": user.organization_id,
            "organization_name": organization.name if organization else None,
            "is_demo": is_demo,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "roles": user_roles,
            "permissions": user_permissions,
        }
    }


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    """
    # Check if user already exists
    existing_user = await user_crud.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if not _is_strong_password(user_in.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password policy violation")

    # Create user
    user = await user_crud.create(db, obj_in=user_in)
    await db.commit()

    return user


@router.get("/me", response_model=User)
async def get_me(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current authenticated user
    """
    return current_user


@router.post("/reset-rate-limit")
async def reset_rate_limit(
    request: Request,
    target_ip: Optional[str] = None,
):
    """
    Reset rate limit for the requesting IP or a specific IP.
    
    SECURITY: Only available in development/test mode (DEBUG=True).
    This endpoint is used by E2E tests to reset rate limits between test runs.
    
    Args:
        target_ip: Optional IP to reset. If not provided, resets for requesting IP.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rate limit reset is only available in development mode"
        )

    client_ip = _get_client_ip(request)
    ip_to_reset = target_ip if target_ip else client_ip

    await rate_limiter.reset(RateLimitType.LOGIN, ip_to_reset)

    return {
        "status": "ok",
        "message": f"Rate limit reset for {ip_to_reset}",
        "ip": ip_to_reset,
        "requested_by": client_ip,
    }


@router.post("/reset-all-rate-limits")
async def reset_all_rate_limits(
    request: Request,
):
    """
    Reset ALL rate limits (clears the entire in-memory store).
    
    SECURITY: Only available in development/test mode (DEBUG=True).
    Use with caution - this clears rate limits for all users.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rate limit reset is only available in development mode"
        )

    # Clear all in-memory rate limit data
    rate_limiter._in_memory_store.clear()
    rate_limiter._blocked.clear()

    client_ip = _get_client_ip(request)

    return {
        "status": "ok",
        "message": "All rate limits cleared",
        "requested_by": client_ip,
    }


@router.post("/2fa/otp")
async def generate_otp_stub(current_user: UserModel = Depends(get_current_user)):
    """2FA support stub: returns OTP challenge metadata."""
    otp = secrets.token_hex(3).upper()
    return {"challenge": "otp", "otp_preview": otp[:2] + "****", "ttl_seconds": 300}
