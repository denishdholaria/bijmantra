from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.core.services.infra.uav_orthomosaic_stitcher_webhook import (
    UAVWebhookPayload,
    uav_stitcher_service,
)

router = APIRouter()


@router.post("/webhooks/uav-stitcher", status_code=200)
async def handle_uav_webhook(
    payload: UAVWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle incoming webhook from UAV stitching service.
    """
    # TODO: Add HMAC signature verification or secret token check to ensure the request is from a trusted source.
    await uav_stitcher_service.process_webhook(payload, db)
    return {"status": "received"}
