"""ResearchAsset commands, queries, DTOs, and event schemas."""

from app.domains.knowledge.capabilities.research_asset_core.schemas.fair_metadata import (
    SUPPORTED_FAIR_ASSET_TYPES,
    FAIRAssetMetadataResponse,
    FAIRAssetMetadataUpsert,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.fair_promotion import (
    FairPromotionCommand,
    FederatedAssetPromotionSource,
    FederatedConnectorReference,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.federated_assets import (
    SUPPORTED_FEDERATED_ASSET_KINDS,
    SUPPORTED_FEDERATED_CONNECTOR_TYPES,
    FederatedAssetAuditEventResponse,
    FederatedAssetConnectorCreate,
    FederatedAssetConnectorResponse,
    FederatedAssetDryRunRequest,
    FederatedAssetFairPromotionRequest,
    FederatedAssetRecordResponse,
    FederatedAssetRegistrationCreate,
    FederatedAssetSyncReceiptResponse,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.registration import (
    FederatedAssetRegistrationCommand,
    FederatedAssetRegistrationPlan,
)


__all__ = [
    "FAIRAssetMetadataResponse",
    "FAIRAssetMetadataUpsert",
    "FairPromotionCommand",
    "FederatedAssetAuditEventResponse",
    "FederatedAssetConnectorCreate",
    "FederatedAssetConnectorResponse",
    "FederatedAssetDryRunRequest",
    "FederatedAssetFairPromotionRequest",
    "FederatedAssetPromotionSource",
    "FederatedAssetRecordResponse",
    "FederatedConnectorReference",
    "FederatedAssetRegistrationCommand",
    "FederatedAssetRegistrationCreate",
    "FederatedAssetRegistrationPlan",
    "FederatedAssetSyncReceiptResponse",
    "SUPPORTED_FAIR_ASSET_TYPES",
    "SUPPORTED_FEDERATED_ASSET_KINDS",
    "SUPPORTED_FEDERATED_CONNECTOR_TYPES",
]
