"""Minimal WebPush subscription registry for PWA notifications."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List

router = APIRouter(prefix="/pwa/notifications", tags=["PWA Notifications"])


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: Dict[str, str]


class PushMessageRequest(BaseModel):
    title: str
    body: str
    data: Dict[str, Any] = {}


_SUBSCRIPTIONS: Dict[str, PushSubscriptionRequest] = {}


@router.post('/subscribe')
async def subscribe(payload: PushSubscriptionRequest):
    _SUBSCRIPTIONS[payload.endpoint] = payload
    return {"status": "subscribed", "count": len(_SUBSCRIPTIONS)}


@router.get('/subscriptions')
async def list_subscriptions():
    return {"count": len(_SUBSCRIPTIONS), "subscriptions": list(_SUBSCRIPTIONS.keys())}


@router.post('/dispatch')
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
