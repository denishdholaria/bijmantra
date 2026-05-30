"""Compatibility shim for ResearchAsset FAIR metadata contracts."""

from app.domains.knowledge.capabilities.research_asset_core.schemas.fair_metadata import (
    SUPPORTED_FAIR_ASSET_TYPES,
    FAIRAssetMetadataResponse,
    FAIRAssetMetadataUpsert,
)


__all__ = [
    "FAIRAssetMetadataResponse",
    "FAIRAssetMetadataUpsert",
    "SUPPORTED_FAIR_ASSET_TYPES",
]
