"""Minimal WebPush subscription registry for PWA notifications."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/pwa/notifications", tags=["PWA Notifications"])


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict[str, str]


class PushMessageRequest(BaseModel):
    title: str
    body: str
    data: dict[str, Any] = {}


_SUBSCRIPTIONS: dict[str, PushSubscriptionRequest] = {}


@router.post("/subscribe")
async def subscribe(payload: PushSubscriptionRequest):
    _SUBSCRIPTIONS[payload.endpoint] = payload
    return {"status": "subscribed", "count": len(_SUBSCRIPTIONS)}


@router.get("/subscriptions")
async def list_subscriptions():
    return {"count": len(_SUBSCRIPTIONS), "subscriptions": list(_SUBSCRIPTIONS.keys())}


@router.post("/dispatch")
async def dispatch_notification(message: PushMessageRequest):
    """
    Placeholder dispatch endpoint for NotificationService integration.
    Real WebPush delivery (VAPID/pywebpush) can be wired behind this contract.
    """
    return {
        "status": "queued",
        "targets": len(_SUBSCRIPTIONS),
        "message": {"title": message.title, "body": message.body, "data": message.data},
    }
