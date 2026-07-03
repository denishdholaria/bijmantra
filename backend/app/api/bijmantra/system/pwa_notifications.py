"""Minimal WebPush subscription registry for PWA notifications.

ADR-002: Subscriptions are now stored in Redis (restart-safe,
multi-instance-safe) instead of a process-local dictionary.
Falls back to local dict when Redis is unavailable (development only).
"""

import logging
from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.core import User


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pwa/notifications", tags=["PWA Notifications"])


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict[str, str]


class PushMessageRequest(BaseModel):
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)


# ADR-002: Redis-backed subscription storage
_REDIS_KEY_PREFIX = "pwa:subscriptions:org"
_REDIS_TTL = 604800  # 7 days
_local_fallback: dict[
    str, dict[str, dict[str, Any]]
] = {}  # dev-only fallback, keyed by organization


def _local_fallback_enabled() -> bool:
    return settings.ENVIRONMENT != "production"


def _storage_unavailable() -> HTTPException:
    return HTTPException(
        status_code=503, detail="Redis-backed PWA notification storage is unavailable"
    )


async def _redis_available():
    """Return (redis_client, True) if Redis is usable, else (None, False)."""
    try:
        from app.core.redis import redis_client

        if redis_client.is_available:
            return redis_client, True
    except Exception:
        pass
    return None, False


def _org_key(organization_id: int) -> str:
    return f"{_REDIS_KEY_PREFIX}:{organization_id}"


def _subscription_id(endpoint: str) -> str:
    return sha256(endpoint.encode("utf-8")).hexdigest()


def _subscription_field(user_id: int, endpoint: str) -> str:
    return f"user:{user_id}:{_subscription_id(endpoint)}"


def _subscription_record(payload: PushSubscriptionRequest, current_user: User) -> dict[str, Any]:
    return {
        "endpoint": payload.endpoint,
        "keys": payload.keys,
        "user_id": current_user.id,
        "organization_id": current_user.organization_id,
    }


def _records_for_user(
    subscriptions: dict[str, Any],
    current_user: User,
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for field, record in subscriptions.items():
        if not isinstance(record, dict):
            continue
        if (
            record.get("user_id") == current_user.id
            and record.get("organization_id") == current_user.organization_id
        ):
            records[field] = record
    return records


def _require_superuser(current_user: User) -> None:
    if not bool(getattr(current_user, "is_superuser", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe(
    payload: PushSubscriptionRequest,
    current_user: User = Depends(get_current_user),
):
    redis_key = _org_key(current_user.organization_id)
    field = _subscription_field(current_user.id, payload.endpoint)
    record = _subscription_record(payload, current_user)

    client, available = await _redis_available()
    if available:
        await client.hset(redis_key, field, record, ttl_seconds=_REDIS_TTL)
        all_subs = await client.hgetall(redis_key)
        count = len(_records_for_user(all_subs, current_user))
    elif _local_fallback_enabled():
        logger.warning("Redis unavailable for PWA subscription storage; using local fallback")
        org_bucket = _local_fallback.setdefault(redis_key, {})
        org_bucket[field] = record
        count = len(_records_for_user(org_bucket, current_user))
    else:
        raise _storage_unavailable()
    return {
        "status": "subscribed",
        "count": count,
        "subscription_id": _subscription_id(payload.endpoint),
    }


@router.get("/subscriptions")
async def list_subscriptions(current_user: User = Depends(get_current_user)):
    redis_key = _org_key(current_user.organization_id)
    client, available = await _redis_available()
    if available:
        all_subs = await client.hgetall(redis_key)
        user_subs = _records_for_user(all_subs, current_user)
        return {
            "count": len(user_subs),
            "subscriptions": [_subscription_id(item["endpoint"]) for item in user_subs.values()],
        }
    if not _local_fallback_enabled():
        raise _storage_unavailable()
    user_subs = _records_for_user(_local_fallback.get(redis_key, {}), current_user)
    return {
        "count": len(user_subs),
        "subscriptions": [_subscription_id(item["endpoint"]) for item in user_subs.values()],
    }


@router.post("/dispatch")
async def dispatch_notification(
    message: PushMessageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Placeholder dispatch endpoint for NotificationService integration.
    Real WebPush delivery (VAPID/pywebpush) can be wired behind this contract.
    """
    _require_superuser(current_user)

    redis_key = _org_key(current_user.organization_id)
    client, available = await _redis_available()
    if available:
        all_subs = await client.hgetall(redis_key)
        target_count = len(all_subs)
    elif _local_fallback_enabled():
        logger.warning("Redis unavailable for PWA dispatch targeting; using local fallback")
        target_count = len(_local_fallback.get(redis_key, {}))
    else:
        raise _storage_unavailable()

    return {
        "status": "queued",
        "targets": target_count,
        "message": {"title": message.title, "body": message.body, "data": message.data},
    }
