"""
Redis Client for Ephemeral Data Storage

Used for:
- Background job status tracking (compute jobs, exports)
- Search result caching
- Rate limiting
- Session management
- Real-time presence

All data stored with TTL (Time To Live) - auto-expires.
"""

import json
import logging
from typing import Optional, Any, Dict, List
from datetime import timedelta
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client wrapper with connection pooling.
    
    Features:
    - Connection pooling for performance
    - Automatic JSON serialization
    - TTL support for all operations
    - Graceful fallback when Redis unavailable
    """

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._available: bool = False

    async def connect(self) -> bool:
        """Initialize Redis connection pool."""
        try:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                decode_responses=True
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            self._available = True
            logger.info(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            return True

        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory fallback: {e}")
            self._available = False
            return False

    async def disconnect(self):
        """Close Redis connection pool."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._available = False
        logger.info("Redis disconnected")

    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self._available

    # ============================================
    # BASIC OPERATIONS
    # ============================================

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600
    ) -> bool:
        """
        Set a value with TTL.
        
        Args:
            key: Redis key
            value: Any JSON-serializable value
            ttl_seconds: Time to live in seconds (default 1 hour)
        """
        if not self._available:
            return False

        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            await self._client.setex(key, ttl_seconds, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value by key.
        
        Returns:
            Deserialized value or None if not found/expired
        """
        if not self._available:
            return None

        try:
            value = await self._client.get(key)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete a key."""
        if not self._available:
            return False

        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._available:
            return False

        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get remaining TTL for a key in seconds."""
        if not self._available:
            return -1

        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -1

    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Update TTL for an existing key."""
        if not self._available:
            return False

        try:
            return await self._client.expire(key, ttl_seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False

    # ============================================
    # HASH OPERATIONS (for structured data)
    # ============================================

    async def hset(
        self,
        key: str,
        field: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """Set a hash field."""
        if not self._available:
            return False

        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            await self._client.hset(key, field, serialized)
            if ttl_seconds:
                await self._client.expire(key, ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis HSET error: {e}")
            return False

    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get a hash field."""
        if not self._available:
            return None

        try:
            value = await self._client.hget(key, field)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis HGET error: {e}")
            return None

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields."""
        if not self._available:
            return {}

        try:
            data = await self._client.hgetall(key)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except json.JSONDecodeError:
                    result[k] = v
            return result
        except Exception as e:
            logger.error(f"Redis HGETALL error: {e}")
            return {}

    async def hdel(self, key: str, field: str) -> bool:
        """Delete a hash field."""
        if not self._available:
            return False

        try:
            await self._client.hdel(key, field)
            return True
        except Exception as e:
            logger.error(f"Redis HDEL error: {e}")
            return False

    # ============================================
    # LIST OPERATIONS (for queues)
    # ============================================

    async def lpush(self, key: str, value: Any) -> bool:
        """Push to left of list (newest first)."""
        if not self._available:
            return False

        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value
            await self._client.lpush(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis LPUSH error: {e}")
            return False

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get list range."""
        if not self._available:
            return []

        try:
            items = await self._client.lrange(key, start, end)
            result = []
            for item in items:
                try:
                    result.append(json.loads(item))
                except json.JSONDecodeError:
                    result.append(item)
            return result
        except Exception as e:
            logger.error(f"Redis LRANGE error: {e}")
            return []

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range."""
        if not self._available:
            return False

        try:
            await self._client.ltrim(key, start, end)
            return True
        except Exception as e:
            logger.error(f"Redis LTRIM error: {e}")
            return False

    # ============================================
    # PATTERN OPERATIONS
    # ============================================

    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        if not self._available:
            return []

        try:
            return await self._client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self._available:
            return 0

        try:
            keys = await self._client.keys(pattern)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE_PATTERN error: {e}")
            return 0

    # ============================================
    # ATOMIC OPERATIONS
    # ============================================

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        if not self._available:
            return 0

        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 0

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement a counter."""
        if not self._available:
            return 0

        try:
            return await self._client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Redis DECR error: {e}")
            return 0


# ============================================
# SINGLETON INSTANCE
# ============================================

redis_client = RedisClient()


# ============================================
# IN-MEMORY FALLBACK (when Redis unavailable)
# ============================================

class InMemoryFallback:
    """
    In-memory fallback when Redis is unavailable.
    
    WARNING: This is NOT production-ready!
    - Data lost on restart
    - Not shared across instances
    - No automatic expiration
    
    Use only for development/testing.
    """

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        """Check if key is expired."""
        import time
        if key in self._expiry:
            if time.time() > self._expiry[key]:
                del self._store[key]
                del self._expiry[key]
                return True
        return False

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        import time
        self._store[key] = value
        self._expiry[key] = time.time() + ttl_seconds
        return True

    def get(self, key: str) -> Optional[Any]:
        if self._is_expired(key):
            return None
        return self._store.get(key)

    def delete(self, key: str) -> bool:
        self._store.pop(key, None)
        self._expiry.pop(key, None)
        return True

    def exists(self, key: str) -> bool:
        if self._is_expired(key):
            return False
        return key in self._store

    def keys(self, pattern: str) -> List[str]:
        import fnmatch
        # Clean expired keys first
        for key in list(self._store.keys()):
            self._is_expired(key)
        return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]


# Fallback instance
_fallback = InMemoryFallback()


# ============================================
# HELPER FUNCTIONS
# ============================================

async def get_redis() -> RedisClient:
    """Get Redis client (for dependency injection)."""
    return redis_client


def get_fallback() -> InMemoryFallback:
    """Get in-memory fallback."""
    return _fallback
