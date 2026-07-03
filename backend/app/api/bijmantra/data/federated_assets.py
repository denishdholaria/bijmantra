"""Compatibility shim for the ResearchAsset federated assets API adapter."""

from app.domains.knowledge.capabilities.research_asset_core.adapters.api.federated_assets import (
    router,
)


__all__ = ["router"]
