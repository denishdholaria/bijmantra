"""Pydantic contracts for ResearchAsset FAIR metadata."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domains.knowledge.capabilities.research_asset_core.domain import (
    policies as research_asset_policies,
)


SUPPORTED_FAIR_ASSET_TYPES = research_asset_policies.SUPPORTED_FAIR_ASSET_TYPES


class FAIRAssetMetadataUpsert(BaseModel):
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


class FAIRAssetMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    asset_type: str
    asset_db_id: str
    persistent_identifier: str
    title: str
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    access_rights: str | None = None
    license: str | None = None
    data_standard: str | None = None
    ontology_terms: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    data_source: str | None = None
    contributors: list[dict[str, Any]] = Field(default_factory=list)
    funding_acknowledgements: list[str] = Field(default_factory=list)
    external_references: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    schema_version: str
    created_at: datetime
    updated_at: datetime
