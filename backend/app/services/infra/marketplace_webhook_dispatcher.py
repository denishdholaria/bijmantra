"""
Marketplace Webhook Dispatcher
Handles incoming webhooks from the marketplace, verifies signatures, and dispatches events.
"""
import hashlib
import hmac
import json
import logging
import os
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel

from app.services.event_bus import event_bus, EventType, EventBus

logger = logging.getLogger(__name__)

class WebhookPayload(BaseModel):
    event_type: str
    data: dict[str, Any]
    timestamp: str | None = None

class MarketplaceWebhookDispatcher:
    def __init__(self, secret: str | None = None, event_bus_instance: EventBus | None = None):
        self.secret = secret or os.getenv("MARKETPLACE_WEBHOOK_SECRET", "default_secret_for_dev")
        self.event_bus = event_bus_instance or event_bus

    def verify_signature(self, payload_body: bytes, signature: str) -> bool:
        """
        Verify the HMAC SHA256 signature of the webhook payload.
        """
        if not signature:
            logger.warning("Missing webhook signature")
            return False

        try:
            expected_signature = hmac.new(
                key=self.secret.encode(),
                msg=payload_body,
                digestmod=hashlib.sha256
            ).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating signature: {e}")
            return False

        if not hmac.compare_digest(expected_signature, signature):
            logger.warning(f"Invalid webhook signature. Expected: {expected_signature}, Got: {signature}")
            return False

        return True

    async def dispatch(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Dispatch the webhook event to the internal EventBus.
        """
        logger.info(f"Dispatching marketplace event: {event_type}")

        # Mapping external event types to internal EventType if needed
        # For now, use CUSTOM or specific integration events

        internal_event_type = EventType.CUSTOM

        # Map common events
        if event_type == "integration.connected":
            internal_event_type = EventType.INTEGRATION_CONNECTED
        elif event_type == "integration.sync_completed":
            internal_event_type = EventType.INTEGRATION_SYNC_COMPLETED
        elif event_type == "integration.error":
            internal_event_type = EventType.INTEGRATION_ERROR

        try:
            await self.event_bus.publish(
                event_type=internal_event_type,
                data={"original_type": event_type, **data},
                source="marketplace_webhook"
            )
            logger.info(f"Successfully dispatched event {event_type} as {internal_event_type}")
        except Exception as e:
            logger.error(f"Failed to dispatch event {event_type}: {e}")
            raise

dispatcher = MarketplaceWebhookDispatcher()
