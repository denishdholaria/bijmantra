"""Compatibility shim for the ResearchAsset federated registry facade.

New code should import from
``app.domains.knowledge.capabilities.research_asset_core.application``.
This module remains to preserve existing API routes and older service imports.
"""

from app.domains.knowledge.capabilities.research_asset_core.adapters import (
    build_fair_metadata_application_service,
    build_federated_asset_registry_repository,
    build_research_asset_audit_ledger,
)
from app.domains.knowledge.capabilities.research_asset_core.application import (
    DisabledFederatedConnector,
    FairAssetMetadataApplicationService,
    FederatedAssetNotFound,
    FederatedAssetRegistryApplicationService,
    FederatedConnectorNotFound,
    FederatedFairMetadataNotFound,
    UnsupportedFederatedAssetKind,
    UnsupportedFederatedConnectorType,
)


class FederatedAssetRegistryService(FederatedAssetRegistryApplicationService):
    """Backward-compatible name for the federated registry application service."""

    def __init__(
        self,
        fair_metadata_service: FairAssetMetadataApplicationService | None = None,
    ) -> None:
        super().__init__(
            fair_metadata_service=(
                fair_metadata_service or build_fair_metadata_application_service()
            ),
            registry_repository_factory=build_federated_asset_registry_repository,
            audit_ledger_factory=build_research_asset_audit_ledger,
        )


__all__ = [
    "DisabledFederatedConnector",
    "FederatedAssetNotFound",
    "FederatedAssetRegistryService",
    "FederatedConnectorNotFound",
    "FederatedFairMetadataNotFound",
    "UnsupportedFederatedAssetKind",
    "UnsupportedFederatedConnectorType",
]
