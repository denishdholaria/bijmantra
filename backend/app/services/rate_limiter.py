"""
Rate Limiter Service

Production-ready rate limiting using Redis with in-memory fallback.
Fixes M2 (login rate limiting) and M3 (in-memory rate limiting not production-ready).

Uses sliding window algorithm for accurate rate limiting.
"""

import time
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from app.core.redis import redis_client, _fallback

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Rate limit types with different thresholds."""
    LOGIN = "login"  # Strict: 5 attempts per 15 minutes
    API_GENERAL = "api_general"  # Standard: 100 requests per minute
    API_WRITE = "api_write"  # Moderate: 30 requests per minute
    API_SEARCH = "api_search"  # Relaxed: 60 requests per minute
    PASSWORD_RESET = "password_reset"  # Very strict: 3 per hour


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit type."""
    max_requests: int
    window_seconds: int
    block_duration_seconds: int = 0  # How long to block after limit exceeded


# Rate limit configurations
RATE_LIMITS: Dict[RateLimitType, RateLimitConfig] = {
    RateLimitType.LOGIN: RateLimitConfig(
        max_requests=5,
        window_seconds=900,  # 15 minutes
        block_duration_seconds=1800,  # 30 minute block after exceeded
    ),
    RateLimitType.API_GENERAL: RateLimitConfig(
        max_requests=100,
        window_seconds=60,
        block_duration_seconds=60,
    ),
    RateLimitType.API_WRITE: RateLimitConfig(
        max_requests=30,
        window_seconds=60,
        block_duration_seconds=120,
    ),
    RateLimitType.API_SEARCH: RateLimitConfig(
        max_requests=60,
        window_seconds=60,
        block_duration_seconds=60,
    ),
    RateLimitType.PASSWORD_RESET: RateLimitConfig(
        max_requests=3,
        window_seconds=3600,  # 1 hour
        block_duration_seconds=3600,
    ),
}


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None  # Seconds until retry allowed


class RateLimiter:
    """
    Production-ready rate limiter using Redis.
    
    Features:
    - Sliding window algorithm for accuracy
    - Redis-backed for multi-instance support
    - In-memory fallback for development
    - Configurable limits per endpoint type
    - Automatic cleanup of expired entries
    """
    
    def __init__(self):
        self._in_memory_store: Dict[str, list] = {}
        self._blocked: Dict[str, float] = {}
    
    def _get_key(self, limit_type: RateLimitType, identifier: str) -> str:
        """Generate Redis key for rate limit tracking."""
        return f"ratelimit:{limit_type.value}:{identifier}"
    
    def _get_block_key(self, limit_type: RateLimitType, identifier: str) -> str:
        """Generate Redis key for block tracking."""
        return f"ratelimit:blocked:{limit_type.value}:{identifier}"
    
    async def check(
        self,
        limit_type: RateLimitType,
        identifier: str,
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.
        
        Args:
            limit_type: Type of rate limit to apply
            identifier: Unique identifier (IP, user_id, etc.)
        
        Returns:
            RateLimitResult with allowed status and metadata
        """
        config = RATE_LIMITS[limit_type]
        now = time.time()
        window_start = now - config.window_seconds
        
        # Check if blocked
        if await self._is_blocked(limit_type, identifier):
            block_key = self._get_block_key(limit_type, identifier)
            if redis_client.is_available:
                ttl = await redis_client.ttl(block_key)
            else:
                ttl = int(self._blocked.get(f"{limit_type.value}:{identifier}", 0) - now)
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=datetime.fromtimestamp(now + max(ttl, 0), tz=timezone.utc),
                retry_after=max(ttl, 0),
            )
        
        # Use Redis if available, otherwise in-memory
        if redis_client.is_available:
            result = await self._check_redis(limit_type, identifier, config, now, window_start)
        else:
            result = self._check_memory(limit_type, identifier, config, now, window_start)
        
        # If limit exceeded, apply block
        if not result.allowed and config.block_duration_seconds > 0:
            await self._apply_block(limit_type, identifier, config.block_duration_seconds)
        
        return result
    
    async def _check_redis(
        self,
        limit_type: RateLimitType,
        identifier: str,
        config: RateLimitConfig,
        now: float,
        window_start: float,
    ) -> RateLimitResult:
        """Check rate limit using Redis sorted set (sliding window)."""
        key = self._get_key(limit_type, identifier)
        
        try:
            # Use Redis sorted set for sliding window
            # Score = timestamp, Member = unique request ID
            
            # Remove old entries outside window
            await redis_client._client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            count = await redis_client._client.zcard(key)
            
            if count >= config.max_requests:
                # Get oldest entry to calculate reset time
                oldest = await redis_client._client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = oldest[0][1] + config.window_seconds
                else:
                    reset_time = now + config.window_seconds
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=datetime.fromtimestamp(reset_time, tz=timezone.utc),
                    retry_after=int(reset_time - now),
                )
            
            # Add current request
            request_id = f"{now}:{identifier}"
            await redis_client._client.zadd(key, {request_id: now})
            
            # Set TTL on the key
            await redis_client._client.expire(key, config.window_seconds + 60)
            
            remaining = config.max_requests - count - 1
            reset_at = datetime.fromtimestamp(now + config.window_seconds, tz=timezone.utc)
            
            return RateLimitResult(
                allowed=True,
                remaining=remaining,
                reset_at=reset_at,
            )
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fail open - allow request but log error
            return RateLimitResult(
                allowed=True,
                remaining=config.max_requests,
                reset_at=datetime.fromtimestamp(now + config.window_seconds, tz=timezone.utc),
            )
    
    def _check_memory(
        self,
        limit_type: RateLimitType,
        identifier: str,
        config: RateLimitConfig,
        now: float,
        window_start: float,
    ) -> RateLimitResult:
        """Check rate limit using in-memory storage (development fallback)."""
        key = f"{limit_type.value}:{identifier}"
        
        # Initialize if needed
        if key not in self._in_memory_store:
            self._in_memory_store[key] = []
        
        # Remove old entries
        self._in_memory_store[key] = [
            ts for ts in self._in_memory_store[key] if ts > window_start
        ]
        
        count = len(self._in_memory_store[key])
        
        if count >= config.max_requests:
            # Calculate reset time from oldest entry
            if self._in_memory_store[key]:
                reset_time = self._in_memory_store[key][0] + config.window_seconds
            else:
                reset_time = now + config.window_seconds
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=datetime.fromtimestamp(reset_time, tz=timezone.utc),
                retry_after=int(reset_time - now),
            )
        
        # Add current request
        self._in_memory_store[key].append(now)
        
        remaining = config.max_requests - count - 1
        reset_at = datetime.fromtimestamp(now + config.window_seconds, tz=timezone.utc)
        
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=reset_at,
        )
    
    async def _is_blocked(self, limit_type: RateLimitType, identifier: str) -> bool:
        """Check if identifier is currently blocked."""
        if redis_client.is_available:
            block_key = self._get_block_key(limit_type, identifier)
            return await redis_client.exists(block_key)
        else:
            key = f"{limit_type.value}:{identifier}"
            if key in self._blocked:
                if time.time() > self._blocked[key]:
                    del self._blocked[key]
                    return False
                return True
            return False
    
    async def _apply_block(
        self,
        limit_type: RateLimitType,
        identifier: str,
        duration_seconds: int,
    ) -> None:
        """Apply a temporary block."""
        if redis_client.is_available:
            block_key = self._get_block_key(limit_type, identifier)
            await redis_client.set(block_key, "blocked", ttl_seconds=duration_seconds)
            logger.warning(f"Rate limit block applied: {limit_type.value} for {identifier}")
        else:
            key = f"{limit_type.value}:{identifier}"
            self._blocked[key] = time.time() + duration_seconds
            logger.warning(f"Rate limit block applied (in-memory): {limit_type.value} for {identifier}")
    
    async def reset(self, limit_type: RateLimitType, identifier: str) -> bool:
        """Reset rate limit for an identifier (admin function)."""
        key = self._get_key(limit_type, identifier)
        block_key = self._get_block_key(limit_type, identifier)
        
        if redis_client.is_available:
            await redis_client.delete(key)
            await redis_client.delete(block_key)
        else:
            mem_key = f"{limit_type.value}:{identifier}"
            self._in_memory_store.pop(mem_key, None)
            self._blocked.pop(mem_key, None)
        
        return True
    
    async def get_status(self, limit_type: RateLimitType, identifier: str) -> Dict:
        """Get current rate limit status for an identifier."""
        config = RATE_LIMITS[limit_type]
        key = self._get_key(limit_type, identifier)
        now = time.time()
        window_start = now - config.window_seconds
        
        if redis_client.is_available:
            # Clean old entries
            await redis_client._client.zremrangebyscore(key, 0, window_start)
            count = await redis_client._client.zcard(key)
        else:
            mem_key = f"{limit_type.value}:{identifier}"
            if mem_key in self._in_memory_store:
                self._in_memory_store[mem_key] = [
                    ts for ts in self._in_memory_store[mem_key] if ts > window_start
                ]
                count = len(self._in_memory_store[mem_key])
            else:
                count = 0
        
        is_blocked = await self._is_blocked(limit_type, identifier)
        
        return {
            "limit_type": limit_type.value,
            "identifier": identifier,
            "max_requests": config.max_requests,
            "window_seconds": config.window_seconds,
            "current_count": count,
            "remaining": max(0, config.max_requests - count),
            "is_blocked": is_blocked,
            "using_redis": redis_client.is_available,
        }


# Singleton instance
rate_limiter = RateLimiter()


# Dependency for FastAPI
async def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance for dependency injection."""
    return rate_limiter
