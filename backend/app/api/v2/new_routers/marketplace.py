from fastapi import APIRouter, Depends, Header, Request, HTTPException
from typing import Annotated, Any

from app.services.infra.marketplace_webhook_dispatcher import dispatcher, MarketplaceWebhookDispatcher, WebhookPayload

router = APIRouter(prefix="/marketplace", tags=["Marketplace Integration"])

async def verify_signature(
    request: Request,
    x_marketplace_signature: Annotated[str | None, Header(alias="X-Marketplace-Signature")] = None,
    webhook_dispatcher: MarketplaceWebhookDispatcher = Depends(lambda: dispatcher)
) -> bytes:
    """
    Verify the webhook signature and return the raw body bytes.
    """
    if not x_marketplace_signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    try:
        body = await request.body()
    except Exception:
        raise HTTPException(status_code=400, detail="Error reading request body")

    if not webhook_dispatcher.verify_signature(body, x_marketplace_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return body

@router.post("/webhook", status_code=200)
async def handle_webhook(
    request: Request,
    body_bytes: bytes = Depends(verify_signature),
    webhook_dispatcher: MarketplaceWebhookDispatcher = Depends(lambda: dispatcher)
):
    """
    Handle incoming webhook events.
    """
    try:
        # We parse manually because we already consumed the body bytes for signature verification.
        # Although request.json() would work if cached, using json.loads(body_bytes) is safer and explicit.
        import json
        payload_data = json.loads(body_bytes)
        payload = WebhookPayload(**payload_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload schema: {str(e)}")

    if not payload.event_type:
        raise HTTPException(status_code=400, detail="Missing event_type")

    await webhook_dispatcher.dispatch(payload.event_type, payload.data)

    return {"status": "success", "event_id": payload.data.get("id")}
