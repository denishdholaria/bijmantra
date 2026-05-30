"""Compatibility shim for the ResearchAsset FAIR metadata API adapter."""

from app.domains.knowledge.capabilities.research_asset_core.adapters.api.fair_metadata import (
    router,
)


__all__ = ["router"]
