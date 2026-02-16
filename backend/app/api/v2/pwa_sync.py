"""PWA sync endpoints for offline draft ingestion."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List

router = APIRouter(prefix="/pwa/drafts", tags=["PWA Sync"])


class DraftSyncRequest(BaseModel):
    drafts: List[Dict[str, Any]]


@router.post('/sync')
async def sync_drafts(payload: DraftSyncRequest):
    """Accept offline drafts pushed by the PWA sync manager."""
    return {
        "accepted": len(payload.drafts),
        "status": "queued",
    }
