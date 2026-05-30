"""Persistence ports for the federated ResearchAsset core."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol, runtime_checkable

from app.domains.knowledge.capabilities.research_asset_core.ports.records import (
    FairAssetMetadataRecord,
    FairAssetMetadataWrite,
    FairAssetTargetRecord,
    FederatedAssetRegistryRecord,
    FederatedAssetRegistryWrite,
    FederatedConnectorRecord,
    FederatedConnectorWrite,
    FederatedSyncReceiptRecord,
    FederatedSyncReceiptWrite,
    ResearchAssetAuditEventRecord,
)


@runtime_checkable
class FairAssetMetadataRepository(Protocol):
    """Port for tenant-scoped FAIR metadata persistence."""

    async def get_target_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetTargetRecord | None:
        """Return the tenant-owned source asset that FAIR metadata describes."""

    async def get_metadata(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetMetadataRecord | None:
        """Return FAIR metadata for a tenant asset when present."""

    async def get_metadata_by_id(
        self,
        *,
        organization_id: int,
        fair_metadata_id: int,
    ) -> FairAssetMetadataRecord | None:
        """Return FAIR metadata by persistence id within a tenant."""

    async def list_metadata(
        self,
        *,
        organization_id: int,
        asset_type: str | None,
        limit: int,
        offset: int,
    ) -> list[FairAssetMetadataRecord]:
        """Return tenant-scoped FAIR metadata rows."""

    async def save_metadata(
        self,
        metadata: FairAssetMetadataWrite,
    ) -> FairAssetMetadataRecord:
        """Persist a FAIR metadata write intent and return the saved record."""


@runtime_checkable
class FederatedAssetRegistryRepository(Protocol):
    """Port for federated connector, asset, and sync-receipt persistence."""

    async def get_connector_by_key(
        self,
        *,
        organization_id: int,
        connector_key: str,
    ) -> FederatedConnectorRecord | None:
        """Return a tenant connector by canonical key."""

    async def get_connector_by_id(
        self,
        *,
        organization_id: int,
        connector_id: int,
    ) -> FederatedConnectorRecord | None:
        """Return a connector by persistence id within a tenant."""

    async def list_connectors(
        self,
        *,
        organization_id: int,
    ) -> list[FederatedConnectorRecord]:
        """Return all tenant connectors."""

    async def get_asset_by_external_id(
        self,
        *,
        organization_id: int,
        connector_id: int,
        external_asset_id: str,
    ) -> FederatedAssetRegistryRecord | None:
        """Return a registered federated asset by connector and external id."""

    async def get_asset_by_registry_id(
        self,
        *,
        organization_id: int,
        registry_asset_id: str,
    ) -> FederatedAssetRegistryRecord | None:
        """Return a registered federated asset by BijMantra registry id."""

    async def list_assets(
        self,
        *,
        organization_id: int,
        connector_id: int | None,
        asset_kind: str | None,
        limit: int,
        offset: int,
    ) -> list[FederatedAssetRegistryRecord]:
        """Return tenant-scoped federated asset rows."""

    async def list_sync_receipts(
        self,
        *,
        organization_id: int,
        connector_id: int | None,
        limit: int,
        offset: int,
    ) -> list[FederatedSyncReceiptRecord]:
        """Return tenant-scoped connector sync receipts."""

    async def get_fair_metadata_by_id(
        self,
        *,
        organization_id: int,
        fair_metadata_id: int,
    ) -> FairAssetMetadataRecord | None:
        """Return FAIR metadata by persistence id within a tenant."""

    async def save_connector(
        self,
        connector: FederatedConnectorWrite,
    ) -> FederatedConnectorRecord:
        """Persist a connector write intent and return the saved record."""

    async def save_asset(
        self,
        asset: FederatedAssetRegistryWrite,
    ) -> FederatedAssetRegistryRecord:
        """Persist a federated asset write intent and return the saved record."""

    async def create_sync_receipt(
        self,
        receipt: FederatedSyncReceiptWrite,
    ) -> FederatedSyncReceiptRecord:
        """Persist a dry-run sync receipt and return the saved record."""

    async def set_asset_fair_metadata(
        self,
        *,
        organization_id: int,
        registry_asset_id: str,
        fair_metadata_id: int,
    ) -> FederatedAssetRegistryRecord | None:
        """Link a federated registry asset to FAIR metadata."""


@runtime_checkable
class ResearchAssetAuditLedger(Protocol):
    """Port for immutable ResearchAsset audit events."""

    async def write_event(
        self,
        *,
        organization_id: int,
        actor_user_id: int | None,
        action: str,
        target_type: str,
        target_id: str | None,
        changes: dict[str, Any],
    ) -> None:
        """Append one audit event."""

    async def list_events(
        self,
        *,
        organization_id: int,
        actions: Iterable[str],
        target_type: str | None,
        target_id: str | None,
        limit: int,
        offset: int,
    ) -> list[ResearchAssetAuditEventRecord]:
        """Return audit events for the ResearchAsset spine."""
