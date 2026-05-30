"""Compatibility shim for ResearchAsset federated asset contracts."""

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


__all__ = [
    "SUPPORTED_FEDERATED_ASSET_KINDS",
    "SUPPORTED_FEDERATED_CONNECTOR_TYPES",
    "FederatedAssetAuditEventResponse",
    "FederatedAssetConnectorCreate",
    "FederatedAssetConnectorResponse",
    "FederatedAssetDryRunRequest",
    "FederatedAssetFairPromotionRequest",
    "FederatedAssetRecordResponse",
    "FederatedAssetRegistrationCreate",
    "FederatedAssetSyncReceiptResponse",
]
