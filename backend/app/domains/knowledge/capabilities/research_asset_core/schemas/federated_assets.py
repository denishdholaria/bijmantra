"""Pydantic contracts for the ResearchAsset federated asset registry."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domains.knowledge.capabilities.research_asset_core.domain import (
    policies as research_asset_policies,
)


SUPPORTED_FEDERATED_CONNECTOR_TYPES = research_asset_policies.SUPPORTED_FEDERATED_CONNECTOR_TYPES
SUPPORTED_FEDERATED_ASSET_KINDS = research_asset_policies.SUPPORTED_FEDERATED_ASSET_KINDS


class FederatedAssetConnectorCreate(BaseModel):
    connector_key: str
    connector_type: str
    display_name: str
    endpoint_url: str | None = None
    description: str | None = None
    enabled: bool = True
    auth_mode: str = "none"
    capabilities: list[str] = Field(default_factory=list)
    standards: list[str] = Field(default_factory=list)
    governance: dict[str, Any] = Field(default_factory=dict)


class FederatedAssetConnectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    connector_key: str
    connector_type: str
    display_name: str
    endpoint_url: str | None = None
    description: str | None = None
    enabled: bool
    auth_mode: str
    capabilities: list[str] = Field(default_factory=list)
    standards: list[str] = Field(default_factory=list)
    governance: dict[str, Any] = Field(default_factory=dict)
    schema_version: str
    created_at: datetime
    updated_at: datetime


class FederatedAssetRegistrationCreate(BaseModel):
    connector_key: str
    external_asset_id: str
    asset_kind: str
    title: str
    description: str | None = None
    source_uri: str | None = None
    source_digest: str | None = None
    license: str | None = None
    data_standard: str | None = None
    standards_mappings: dict[str, Any] = Field(default_factory=dict)
    fair_metadata_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"


class FederatedAssetFairPromotionRequest(BaseModel):
    persistent_identifier: str | None = None
    title: str | None = None
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    access_rights: str | None = None
    license: str | None = None
    data_standard: str | None = None
    ontology_terms: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    data_source: str | None = None
    contributors: list[dict[str, Any]] = Field(default_factory=list)
    funding_acknowledgements: list[str] = Field(default_factory=list)
    external_references: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)


class FederatedAssetAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    user_id: int | None = None
    action: str
    target_type: str
    target_id: str | None = None
    changes: dict[str, Any] | None = None
    method: str
    created_at: datetime


class FederatedAssetRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    standards_mappings: dict[str, Any] = Field(default_factory=dict)
    fair_metadata_id: int | None = None
    asset_metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    status: str
    schema_version: str
    created_at: datetime
    updated_at: datetime


class FederatedAssetDryRunRequest(BaseModel):
    candidate_assets: list[dict[str, Any]] = Field(default_factory=list)
    dry_run_note: str | None = None


class FederatedAssetSyncReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    connector_id: int
    receipt_id: str
    run_mode: str
    status: str
    source_digest: str | None = None
    discovered_asset_count: int
    registered_asset_count: int
    skipped_asset_count: int
    error: dict[str, Any] | None = None
    manifest_snapshot: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime | None = None
    schema_version: str
    created_at: datetime
    updated_at: datetime
