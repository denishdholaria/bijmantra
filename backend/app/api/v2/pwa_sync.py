"""PWA sync endpoints for offline draft ingestion."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/pwa/drafts", tags=["PWA Sync"])


class DraftSyncRequest(BaseModel):
    drafts: list[dict[str, Any]]


@router.post("/sync")
async def sync_drafts(payload: DraftSyncRequest):
    """Accept offline drafts pushed by the PWA sync manager."""
    return {
        "accepted": len(payload.drafts),
        "status": "queued",
    }
