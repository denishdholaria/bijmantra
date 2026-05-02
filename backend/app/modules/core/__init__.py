"""
Core Domain Module

Handles authentication, authorization, tenants, and platform infrastructure.
"""

from app.modules.core.services.rate_limiter_service import (
    RateLimiter,
    RateLimitType,
    rate_limiter,
    get_rate_limiter,
)

# Public interface
__all__ = [
    "RateLimiter",
    "RateLimitType",
    "rate_limiter",
    "get_rate_limiter",
]
