"""Minimal WebPush subscription registry for PWA notifications.

ADR-002: Subscriptions are now stored in Redis (restart-safe,
multi-instance-safe) instead of a process-local dictionary.
Falls back to local dict when Redis is unavailable (development only).
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pwa/notifications", tags=["PWA Notifications"])


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict[str, str]


class PushMessageRequest(BaseModel):
    title: str
    body: str
    data: dict[str, Any] = {}


# ADR-002: Redis-backed subscription storage
_REDIS_KEY = "pwa:subscriptions"
_REDIS_TTL = 604800  # 7 days
_local_fallback: dict[str, dict] = {}  # dev-only fallback


def _local_fallback_enabled() -> bool:
    return settings.ENVIRONMENT != "production"


def _storage_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="Redis-backed PWA notification storage is unavailable")


async def _redis_available():
    """Return (redis_client, True) if Redis is usable, else (None, False)."""
    try:
        from app.core.redis import redis_client
        if redis_client.is_available:
            return redis_client, True
    except Exception:
        pass
    return None, False


@router.post("/subscribe")
async def subscribe(payload: PushSubscriptionRequest):
    client, available = await _redis_available()
    if available:
        await client.hset(_REDIS_KEY, payload.endpoint, payload.model_dump_json(), ttl_seconds=_REDIS_TTL)
        all_keys = await client.hgetall(_REDIS_KEY)
        count = len(all_keys)
    elif _local_fallback_enabled():
        logger.warning("Redis unavailable for PWA subscription storage; using local fallback")
        _local_fallback[payload.endpoint] = payload.model_dump()
        count = len(_local_fallback)
    else:
        raise _storage_unavailable()
    return {"status": "subscribed", "count": count}


@router.get("/subscriptions")
async def list_subscriptions():
    client, available = await _redis_available()
    if available:
        all_subs = await client.hgetall(_REDIS_KEY)
        return {"count": len(all_subs), "subscriptions": list(all_subs.keys())}
    if not _local_fallback_enabled():
        raise _storage_unavailable()
    return {"count": len(_local_fallback), "subscriptions": list(_local_fallback.keys())}


@router.post("/dispatch")
async def dispatch_notification(message: PushMessageRequest):
    """
    Placeholder dispatch endpoint for NotificationService integration.
    Real WebPush delivery (VAPID/pywebpush) can be wired behind this contract.
    """
    client, available = await _redis_available()
    if available:
        all_subs = await client.hgetall(_REDIS_KEY)
        target_count = len(all_subs)
    elif _local_fallback_enabled():
        logger.warning("Redis unavailable for PWA dispatch targeting; using local fallback")
        target_count = len(_local_fallback)
    else:
        raise _storage_unavailable()

    return {
        "status": "queued",
        "targets": target_count,
        "message": {"title": message.title, "body": message.body, "data": message.data},
    }
