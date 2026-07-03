"""DTOs for federated ResearchAsset registration planning."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FederatedAssetRegistrationCommand:
    """Operator-reviewed metadata for explicit federated asset registration."""

    connector_key: str
    external_asset_id: str
    asset_kind: str
    title: str
    source_uri: str | None = None
    source_digest: str | None = None
    license: str | None = None
    data_standard: str | None = None
    standards_mappings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FederatedAssetRegistrationPlan:
    """Deterministic identity and digest plan for a federated asset row."""

    registry_asset_id: str
    external_asset_id: str
    asset_kind: str
    source_digest: str
