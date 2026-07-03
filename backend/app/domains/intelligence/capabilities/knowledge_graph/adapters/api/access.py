"""FastAPI access guard for Knowledge Graph capability APIs."""

from __future__ import annotations

from typing import Any

from app.platform.capability_guards import require_platform_capability_api_access


KNOWLEDGE_GRAPH_CAPABILITY_ID = "intelligence_fabric.knowledge_graph"


async def require_knowledge_graph_api_access(
    actor: Any,
    *,
    db: Any | None = None,
    required_permission: str,
    required_data_scopes: tuple[str, ...] = ("organization",),
) -> None:
    """Reject API access when Knowledge Graph capability policy denies it."""

    await require_platform_capability_api_access(
        KNOWLEDGE_GRAPH_CAPABILITY_ID,
        actor,
        db=db,
        required_permission=required_permission,
        required_data_scopes=required_data_scopes,
        missing_manifest_detail="Knowledge Graph capability manifest missing",
    )
