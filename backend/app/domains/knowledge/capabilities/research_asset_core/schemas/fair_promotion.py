"""DTOs for promoting federated assets into FAIR metadata."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FederatedAssetPromotionSource:
    """Metadata-only federated asset snapshot used by promotion use cases."""

    registry_asset_id: str
    external_asset_id: str
    asset_kind: str
    title: str
    description: str | None = None
    source_uri: str | None = None
    source_digest: str | None = None
    license: str | None = None
    data_standard: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FederatedConnectorReference:
    """Connector metadata needed during FAIR promotion."""

    connector_key: str
    display_name: str | None = None


@dataclass(frozen=True)
class FairPromotionCommand:
    """Operator-supplied FAIR promotion fields."""

    fields_set: frozenset[str]
    persistent_identifier: str | None = None
    title: str | None = None
    description: str | None = None
    keywords: tuple[str, ...] = ()
    access_rights: str | None = None
    license: str | None = None
    data_standard: str | None = None
    ontology_terms: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    data_source: str | None = None
    contributors: tuple[dict[str, Any], ...] = ()
    funding_acknowledgements: tuple[str, ...] = ()
    external_references: tuple[dict[str, Any], ...] = ()
    evidence_refs: tuple[dict[str, Any], ...] = ()
