"""PWA sync endpoints for offline draft ingestion."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.core import User


router = APIRouter(prefix="/pwa/drafts", tags=["PWA Sync"])


class DraftSyncRequest(BaseModel):
    drafts: list[dict[str, Any]]


def _draft_organization_id(draft: dict[str, Any]) -> int | None:
    for key in ("organization_id", "organizationId", "organizationDbId"):
        value = draft.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid draft organization identifier in {key}",
            ) from None
    return None


def _validate_draft_tenant(payload: DraftSyncRequest, current_user: User) -> None:
    for draft in payload.drafts:
        organization_id = _draft_organization_id(draft)
        if organization_id is not None and organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Draft organization does not match authenticated user organization",
            )


@router.post("/sync")
async def sync_drafts(
    payload: DraftSyncRequest,
    current_user: User = Depends(get_current_user),
):
    """Accept offline drafts pushed by the PWA sync manager."""
    _validate_draft_tenant(payload, current_user)

    if not payload.drafts:
        return {
            "accepted": 0,
            "status": "no_content",
            "organization_id": current_user.organization_id,
        }

    return {
        "accepted": len(payload.drafts),
        "status": "queued",
        "organization_id": current_user.organization_id,
    }
