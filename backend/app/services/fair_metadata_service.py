"""Compatibility shim for the ResearchAsset FAIR metadata application facade.

New code should import from
``app.domains.knowledge.capabilities.research_asset_core.application``.
This module remains to preserve existing API routes and older service imports.
"""

from app.domains.knowledge.capabilities.research_asset_core.adapters import (
    build_fair_metadata_repository,
)
from app.domains.knowledge.capabilities.research_asset_core.application import (
    FairAssetMetadataApplicationService,
    FairAssetNotFound,
    InvalidFairPersistentIdentifier,
    UnknownFairAssetType,
)


class FairAssetMetadataService(FairAssetMetadataApplicationService):
    """Backward-compatible name for the FAIR metadata application service."""

    def __init__(self) -> None:
        super().__init__(repository_factory=build_fair_metadata_repository)


__all__ = [
    "FairAssetMetadataService",
    "FairAssetNotFound",
    "InvalidFairPersistentIdentifier",
    "UnknownFairAssetType",
]
