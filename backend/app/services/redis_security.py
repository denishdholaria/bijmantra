"""
Redis-backed Security Storage

Provides distributed, persistent storage for:
- Blocked IPs and users
- Rate limiting counters
- Session tracking
- Threat intelligence cache

Falls back to in-memory storage if Redis is unavailable.
"""

import json
import asyncio
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Using in-memory storage.")


class RedisSecurityStore:
    """
    Redis-backed security storage with in-memory fallback.
    
    Keys used:
    - {prefix}blocked:ip:{ip} - Blocked IP with expiry
    - {prefix}blocked:user:{user_id} - Blocked user with expiry
    - {prefix}rate:{key} - Rate limit counter
    - {prefix}reputation:{ip} - IP reputation score
    - {prefix}events:{date} - Security events for date
    """
    
    def __init__(self, redis_url: Optional[str] = None, prefix: str = "bijmantra:security:"):
        self.prefix = prefix
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._connected = False
        
        # In-memory fallback
        self._memory_blocked_ips: Dict[str, datetime] = {}
        self._memory_blocked_users: Dict[str, datetime] = {}
        self._memory_rate_limits: Dict[str, Dict] = {}
        self._memory_reputation: Dict[str, float] = {}
    
    async def connect(self) -> bool:
        """Connect to Redis."""
        if not REDIS_AVAILABLE or not self.redis_url:
            logger.info("Redis not configured. Using in-memory storage.")
            return False
        
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis for security storage")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._connected = False

    # ==================== Blocking ====================
    
    async def block_ip(self, ip: str, duration_seconds: int, reason: str = "") -> bool:
        """Block an IP address."""
        expiry = datetime.now(UTC) + timedelta(seconds=duration_seconds)
        
        if self._connected and self._redis:
            try:
                key = f"{self.prefix}blocked:ip:{ip}"
                await self._redis.setex(key, duration_seconds, json.dumps({
                    "blocked_at": datetime.now(UTC).isoformat(),
                    "expires_at": expiry.isoformat(),
                    "reason": reason
                }))
                return True
            except Exception as e:
                logger.error(f"Redis block_ip error: {e}")
        
        # Fallback to memory
        self._memory_blocked_ips[ip] = expiry
        return True
    
    async def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address."""
        if self._connected and self._redis:
            try:
                key = f"{self.prefix}blocked:ip:{ip}"
                result = await self._redis.delete(key)
                return result > 0
            except Exception as e:
                logger.error(f"Redis unblock_ip error: {e}")
        
        if ip in self._memory_blocked_ips:
            del self._memory_blocked_ips[ip]
            return True
        return False
    
    async def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked."""
        if self._connected and self._redis:
            try:
                key = f"{self.prefix}blocked:ip:{ip}"
                return await self._redis.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis is_ip_blocked error: {e}")
        
        # Fallback to memory
        if ip in self._memory_blocked_ips:
            if datetime.now(UTC) > self._memory_blocked_ips[ip]:
                del self._memory_blocked_ips[ip]
                return False
            return True
        return False
    
    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get all blocked IPs."""
        results = []
        now = datetime.now(UTC)
        
        if self._connected and self._redis:
            try:
                pattern = f"{self.prefix}blocked:ip:*"
                keys = await self._redis.keys(pattern)
                for key in keys:
                    ip = key.replace(f"{self.prefix}blocked:ip:", "")
                    ttl = await self._redis.ttl(key)
                    if ttl > 0:
                        results.append({
                            "ip": ip,
                            "remaining_seconds": ttl,
                            "expires_at": (now + timedelta(seconds=ttl)).isoformat()
                        })
                return results
            except Exception as e:
                logger.error(f"Redis get_blocked_ips error: {e}")
        
        # Fallback to memory
        for ip, expiry in list(self._memory_blocked_ips.items()):
            if expiry > now:
                results.append({
                    "ip": ip,
                    "remaining_seconds": int((expiry - now).total_seconds()),
                    "expires_at": expiry.isoformat()
                })
            else:
                del self._memory_blocked_ips[ip]
        return results
    
    async def block_user(self, user_id: str, duration_seconds: int, reason: str = "") -> bool:
        """Block a user."""
        expiry = datetime.now(UTC) + timedelta(seconds=duration_seconds)
        
        if self._connected and self._redis:
            try:
                key = f"{self.prefix}blocked:user:{user_id}"
                await self._redis.setex(key, duration_seconds, json.dumps({
                    "blocked_at": datetime.now(UTC).isoformat(),
                    "expires_at": expiry.isoformat(),
                    "reason": reason
                }))
                return True
            except Exception as e:
                logger.error(f"Redis block_user error: {e}")
        
        self._memory_blocked_users[user_id] = expiry
        return True
    
    async def is_user_blocked(self, user_id: str) -> bool:
        """Check if a user is blocked."""
        if self._connected and self._redis:
            try:
                key = f"{self.prefix}blocked:user:{user_id}"
                return await self._redis.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis is_user_blocked error: {e}")
        
        if user_id in self._memory_blocked_users:
            if datetime.now(UTC) > self._memory_blocked_users[user_id]:
                del self._memory_blocked_users[user_id]
                return False
            return True
        return False

    # ==================== Rate Limiting ====================
    
    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> Dict[str, Any]:
        """
        Check and increment rate limit counter.
        Returns: {"allowed": bool, "current": int, "limit": int, "reset_in": int}
        """
        full_key = f"{self.prefix}rate:{key}"
        now = datetime.now(UTC)
        
        if self._connected and self._redis:
            try:
                pipe = self._redis.pipeline()
                pipe.incr(full_key)
                pipe.ttl(full_key)
                results = await pipe.execute()
                
                current = results[0]
                ttl = results[1]
                
                # Set expiry if new key
                if ttl == -1:
                    await self._redis.expire(full_key, window_seconds)
                    ttl = window_seconds
                
                return {
                    "allowed": current <= limit,
                    "current": current,
                    "limit": limit,
                    "reset_in": max(0, ttl)
                }
            except Exception as e:
                logger.error(f"Redis rate_limit error: {e}")
        
        # Fallback to memory (simplified)
        if full_key not in self._memory_rate_limits:
            self._memory_rate_limits[full_key] = {
                "count": 0,
                "reset_at": now + timedelta(seconds=window_seconds)
            }
        
        entry = self._memory_rate_limits[full_key]
        if now > entry["reset_at"]:
            entry["count"] = 0
            entry["reset_at"] = now + timedelta(seconds=window_seconds)
        
        entry["count"] += 1
        reset_in = int((entry["reset_at"] - now).total_seconds())
        
        return {
            "allowed": entry["count"] <= limit,
            "current": entry["count"],
            "limit": limit,
            "reset_in": max(0, reset_in)
        }
    
    # ==================== IP Reputation ====================
    
    async def set_ip_reputation(self, ip: str, score: float):
        """Set IP reputation score (0-100, higher = more suspicious)."""
        if self._connected and self._redis:
            try:
                key = f"{self.prefix}reputation:{ip}"
                await self._redis.set(key, str(score))
                await self._redis.expire(key, 86400 * 7)  # 7 days
                return
            except Exception as e:
                logger.error(f"Redis set_reputation error: {e}")
        
        self._memory_reputation[ip] = score
    
    async def get_ip_reputation(self, ip: str) -> float:
        """Get IP reputation score."""
        if self._connected and self._redis:
            try:
                key = f"{self.prefix}reputation:{ip}"
                score = await self._redis.get(key)
                return float(score) if score else 0.0
            except Exception as e:
                logger.error(f"Redis get_reputation error: {e}")
        
        return self._memory_reputation.get(ip, 0.0)
    
    async def increment_ip_reputation(self, ip: str, amount: float = 10.0) -> float:
        """Increment IP reputation score (make more suspicious)."""
        current = await self.get_ip_reputation(ip)
        new_score = min(100.0, current + amount)
        await self.set_ip_reputation(ip, new_score)
        return new_score
    
    # ==================== Statistics ====================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get security storage statistics."""
        blocked_ips = await self.get_blocked_ips()
        
        return {
            "storage_type": "redis" if self._connected else "memory",
            "connected": self._connected,
            "blocked_ips": len(blocked_ips),
            "blocked_users": len(self._memory_blocked_users),
            "rate_limit_keys": len(self._memory_rate_limits),
            "reputation_entries": len(self._memory_reputation),
        }


# Global instance
redis_security = RedisSecurityStore()


async def init_redis_security(redis_url: Optional[str] = None):
    """Initialize Redis security storage."""
    if redis_url:
        redis_security.redis_url = redis_url
    await redis_security.connect()
    return redis_security
