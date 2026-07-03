"""FastAPI access guard for ResearchAsset capability APIs."""

from __future__ import annotations

from typing import Any

from app.platform.capability_guards import require_platform_capability_api_access


RESEARCH_ASSET_CAPABILITY_ID = "scientific_publishing_fair_exchange.research_asset_core"


async def require_research_asset_api_access(
    actor: Any,
    *,
    db: Any | None = None,
    required_permission: str,
    required_data_scopes: tuple[str, ...] = ("organization",),
) -> None:
    """Reject API access when ResearchAsset capability policy denies it."""

    await require_platform_capability_api_access(
        RESEARCH_ASSET_CAPABILITY_ID,
        actor,
        db=db,
        required_permission=required_permission,
        required_data_scopes=required_data_scopes,
        missing_manifest_detail="ResearchAsset capability manifest missing",
    )
