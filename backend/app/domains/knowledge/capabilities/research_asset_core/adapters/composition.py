"""Infrastructure composition for ResearchAsset application facades."""

from typing import Any

from app.domains.knowledge.capabilities.research_asset_core.adapters.sqlalchemy_repositories import (
    SqlAlchemyFairAssetMetadataRepository,
    SqlAlchemyFederatedAssetRegistryRepository,
    SqlAlchemyResearchAssetAuditLedger,
)
from app.domains.knowledge.capabilities.research_asset_core.application.fair_metadata_service import (
    FairAssetMetadataApplicationService,
)
from app.domains.knowledge.capabilities.research_asset_core.application.federated_registry_service import (
    FederatedAssetRegistryApplicationService,
)
from app.domains.knowledge.capabilities.research_asset_core.ports import (
    FairAssetMetadataRepository,
    FederatedAssetRegistryRepository,
    ResearchAssetAuditLedger,
)


def build_fair_metadata_repository(db: Any) -> FairAssetMetadataRepository:
    return SqlAlchemyFairAssetMetadataRepository(db)


def build_federated_asset_registry_repository(db: Any) -> FederatedAssetRegistryRepository:
    return SqlAlchemyFederatedAssetRegistryRepository(db)


def build_research_asset_audit_ledger(db: Any) -> ResearchAssetAuditLedger:
    return SqlAlchemyResearchAssetAuditLedger(db)


def build_fair_metadata_application_service() -> FairAssetMetadataApplicationService:
    return FairAssetMetadataApplicationService(
        repository_factory=build_fair_metadata_repository,
    )


def build_federated_asset_registry_application_service() -> FederatedAssetRegistryApplicationService:
    return FederatedAssetRegistryApplicationService(
        fair_metadata_service=build_fair_metadata_application_service(),
        registry_repository_factory=build_federated_asset_registry_repository,
        audit_ledger_factory=build_research_asset_audit_ledger,
    )
