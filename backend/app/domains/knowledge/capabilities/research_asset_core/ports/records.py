"""Application-facing records for ResearchAsset persistence ports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class FairAssetTargetRecord:
    """Tenant-owned source asset that can receive FAIR metadata."""

    asset_type: str
    asset_db_id: str
    title: str


@dataclass(frozen=True)
class FairAssetMetadataRecord:
    """FAIR metadata record exposed by ResearchAsset ports."""

    id: int
    organization_id: int
    asset_type: str
    asset_db_id: str
    persistent_identifier: str
    title: str
    description: str | None
    keywords: list[str] = field(default_factory=list)
    access_rights: str | None = None
    license: str | None = None
    data_standard: str | None = None
    ontology_terms: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    data_source: str | None = None
    contributors: list[dict[str, Any]] = field(default_factory=list)
    funding_acknowledgements: list[str] = field(default_factory=list)
    external_references: list[dict[str, Any]] = field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    schema_version: str = "fair_asset_metadata.v1"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class FairAssetMetadataWrite:
    """Write intent for creating or updating FAIR metadata."""

    organization_id: int
    asset_type: str
    asset_db_id: str
    persistent_identifier: str
    title: str
    description: str | None = None
    keywords: list[str] = field(default_factory=list)
    access_rights: str | None = None
    license: str | None = None
    data_standard: str | None = None
    ontology_terms: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    data_source: str | None = None
    contributors: list[dict[str, Any]] = field(default_factory=list)
    funding_acknowledgements: list[str] = field(default_factory=list)
    external_references: list[dict[str, Any]] = field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    schema_version: str = "fair_asset_metadata.v1"
    metadata_id: int | None = None


@dataclass(frozen=True)
class FederatedConnectorRecord:
    """Federated connector record exposed by ResearchAsset ports."""

    id: int
    organization_id: int
    connector_key: str
    connector_type: str
    display_name: str
    endpoint_url: str | None
    description: str | None
    enabled: bool
    auth_mode: str
    capabilities: list[str] = field(default_factory=list)
    standards: list[str] = field(default_factory=list)
    governance: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "federated_connector.v1"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class FederatedConnectorWrite:
    """Write intent for a federated connector manifest."""

    organization_id: int
    connector_key: str
    connector_type: str
    display_name: str
    endpoint_url: str | None = None
    description: str | None = None
    enabled: bool = True
    auth_mode: str = "none"
    capabilities: list[str] = field(default_factory=list)
    standards: list[str] = field(default_factory=list)
    governance: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "federated_connector.v1"


@dataclass(frozen=True)
class FederatedAssetRegistryRecord:
    """Metadata-only federated asset record exposed by ResearchAsset ports."""

    id: int
    organization_id: int
    connector_id: int
    registry_asset_id: str
    external_asset_id: str
    asset_kind: str
    title: str
    description: str | None = None
    source_uri: str | None = None
    source_digest: str | None = None
    license: str | None = None
    data_standard: str | None = None
    standards_mappings: dict[str, Any] = field(default_factory=dict)
    fair_metadata_id: int | None = None
    asset_metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    schema_version: str = "federated_asset_record.v1"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class FederatedAssetRegistryWrite:
    """Write intent for a metadata-only federated asset record."""

    organization_id: int
    connector_id: int
    registry_asset_id: str
    external_asset_id: str
    asset_kind: str
    title: str
    description: str | None = None
    source_uri: str | None = None
    source_digest: str | None = None
    license: str | None = None
    data_standard: str | None = None
    standards_mappings: dict[str, Any] = field(default_factory=dict)
    fair_metadata_id: int | None = None
    asset_metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    schema_version: str = "federated_asset_record.v1"


@dataclass(frozen=True)
class FederatedSyncReceiptRecord:
    """Dry-run sync receipt exposed by ResearchAsset ports."""

    id: int
    organization_id: int
    connector_id: int
    receipt_id: str
    run_mode: str
    status: str
    source_digest: str | None
    discovered_asset_count: int
    registered_asset_count: int
    skipped_asset_count: int
    error: dict[str, Any] | None
    manifest_snapshot: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    schema_version: str = "federated_sync_receipt.v1"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class FederatedSyncReceiptWrite:
    """Write intent for a dry-run sync receipt."""

    organization_id: int
    connector_id: int
    receipt_id: str
    run_mode: str
    status: str
    source_digest: str | None
    discovered_asset_count: int
    registered_asset_count: int
    skipped_asset_count: int
    error: dict[str, Any] | None
    manifest_snapshot: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    schema_version: str = "federated_sync_receipt.v1"


@dataclass(frozen=True)
class ResearchAssetAuditEventRecord:
    """ResearchAsset audit event exposed by the audit ledger port."""

    id: int
    organization_id: int
    user_id: int | None
    action: str
    target_type: str
    target_id: str | None
    changes: dict[str, Any] | None
    method: str
    created_at: datetime | None = None
