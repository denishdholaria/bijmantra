"""FastAPI adapters for the ResearchAsset capability."""

from app.domains.knowledge.capabilities.research_asset_core.adapters.api.fair_metadata import (
    router as fair_metadata_router,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters.api.federated_assets import (
    router as federated_assets_router,
)


__all__ = [
    "fair_metadata_router",
    "federated_assets_router",
]
