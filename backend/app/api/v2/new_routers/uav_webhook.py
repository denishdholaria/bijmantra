from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.modules.core.services.infra.uav_orthomosaic_stitcher_webhook import (
    UAVWebhookPayload,
    uav_stitcher_service,
)


router = APIRouter()


@router.post("/webhooks/uav-stitcher", status_code=200)
async def handle_uav_webhook(
    payload: UAVWebhookPayload,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle incoming webhook from UAV stitching service.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ")[1]
    # Check against the application's secret key for inter-service trust
    if token != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook token"
        )

    await uav_stitcher_service.process_webhook(payload, db)
    return {"status": "received"}
