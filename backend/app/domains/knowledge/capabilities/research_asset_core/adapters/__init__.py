"""ResearchAsset adapters for persistence, APIs, and external exchange."""

from app.domains.knowledge.capabilities.research_asset_core.adapters.composition import (
    build_fair_metadata_application_service,
    build_fair_metadata_repository,
    build_federated_asset_registry_application_service,
    build_federated_asset_registry_repository,
    build_research_asset_audit_ledger,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters.sqlalchemy_repositories import (
    DEFAULT_FAIR_ASSET_BINDINGS,
    AssetBinding,
    SqlAlchemyFairAssetMetadataRepository,
    SqlAlchemyFederatedAssetRegistryRepository,
    SqlAlchemyResearchAssetAuditLedger,
)


__all__ = [
    "AssetBinding",
    "DEFAULT_FAIR_ASSET_BINDINGS",
    "SqlAlchemyFairAssetMetadataRepository",
    "SqlAlchemyFederatedAssetRegistryRepository",
    "SqlAlchemyResearchAssetAuditLedger",
    "build_fair_metadata_application_service",
    "build_fair_metadata_repository",
    "build_federated_asset_registry_application_service",
    "build_federated_asset_registry_repository",
    "build_research_asset_audit_ledger",
]
