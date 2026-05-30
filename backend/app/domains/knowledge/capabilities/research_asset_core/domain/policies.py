"""Pure ResearchAsset validation, identifier, and normalization policies."""

import hashlib
import json
from typing import Any


SUPPORTED_FAIR_ASSET_TYPES = (
    "observation_variable",
    "germplasm",
    "trial",
    "study",
    "federated_asset",
)

SUPPORTED_FEDERATED_CONNECTOR_TYPES = (
    "brapi_server",
    "crop_ontology",
    "public_dataset",
    "object_storage",
    "fairgrounds_catalog",
)

SUPPORTED_FEDERATED_ASSET_KINDS = (
    "dataset",
    "api",
    "ai_model",
    "pipeline",
    "visualization",
    "notebook",
    "object_storage_artifact",
    "ontology",
)

FAIR_ASSET_TYPE_ALIASES = {
    "observation-variable": "observation_variable",
    "observationvariable": "observation_variable",
    "variable": "observation_variable",
    "variables": "observation_variable",
    "trait": "observation_variable",
    "traits": "observation_variable",
    "federated-asset": "federated_asset",
    "federatedasset": "federated_asset",
    "registry_asset": "federated_asset",
    "registry-asset": "federated_asset",
}

FEDERATED_AUDIT_ACTIONS = (
    "federated_connector_upsert",
    "federated_connector_dry_run",
    "federated_asset_register",
    "federated_asset_promote_fair",
)


class UnsupportedFederatedConnectorType(ValueError):
    """Raised when connector type is outside the approved manifest set."""


class UnsupportedFederatedAssetKind(ValueError):
    """Raised when asset kind is outside the approved metadata registry set."""


class UnknownFairAssetType(ValueError):
    """Raised when an asset type is outside the first FAIR metadata wave."""


class InvalidFairPersistentIdentifier(ValueError):
    """Raised when a persistent identifier violates BijMantra PID policy."""


def canonical_json(data: Any) -> str:
    """Return canonical JSON for deterministic digests."""

    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def sha256_digest(data: Any) -> str:
    """Return a deterministic SHA-256 digest for JSON-compatible data."""

    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def first_nonempty(*values: Any) -> str | None:
    """Return the first non-empty string value from a preference list."""

    for value in values:
        if value is None:
            continue
        normalized = str(value).strip()
        if normalized:
            return normalized
    return None


def normalize_connector_key(connector_key: str) -> str:
    """Normalize a tenant connector key for stable lookup."""

    return connector_key.strip().lower().replace(" ", "-")


def normalize_connector_type(connector_type: str) -> str:
    """Normalize a connector type token."""

    return connector_type.strip().lower().replace("-", "_")


def require_supported_connector_type(connector_type: str) -> str:
    """Return a normalized connector type or raise for unsupported connectors."""

    normalized = normalize_connector_type(connector_type)
    if normalized not in SUPPORTED_FEDERATED_CONNECTOR_TYPES:
        supported = ", ".join(SUPPORTED_FEDERATED_CONNECTOR_TYPES)
        raise UnsupportedFederatedConnectorType(
            f"Unsupported federated connector type '{connector_type}'. Use: {supported}"
        )
    return normalized


def normalize_federated_asset_kind(asset_kind: str) -> str:
    """Normalize a federated asset kind token."""

    return asset_kind.strip().lower().replace("-", "_")


def require_supported_federated_asset_kind(asset_kind: str) -> str:
    """Return a normalized asset kind or raise for unsupported registry assets."""

    normalized = normalize_federated_asset_kind(asset_kind)
    if normalized not in SUPPORTED_FEDERATED_ASSET_KINDS:
        supported = ", ".join(SUPPORTED_FEDERATED_ASSET_KINDS)
        raise UnsupportedFederatedAssetKind(
            f"Unsupported federated asset kind '{asset_kind}'. Use: {supported}"
        )
    return normalized


def normalize_fair_asset_type(asset_type: str) -> str:
    """Normalize a FAIR asset type, including legacy UI/API aliases."""

    normalized = asset_type.strip().lower().replace(" ", "_")
    return FAIR_ASSET_TYPE_ALIASES.get(normalized, normalized)


def require_supported_fair_asset_type(asset_type: str) -> str:
    """Return a normalized FAIR asset type or raise for unsupported assets."""

    normalized = normalize_fair_asset_type(asset_type)
    if normalized not in SUPPORTED_FAIR_ASSET_TYPES:
        supported = ", ".join(SUPPORTED_FAIR_ASSET_TYPES)
        raise UnknownFairAssetType(f"Unsupported FAIR asset type '{asset_type}'. Use: {supported}")
    return normalized


def resolve_persistent_identifier(
    persistent_identifier: str | None,
    *,
    asset_type: str,
    asset_db_id: str,
) -> str:
    """Resolve or validate a durable FAIR persistent identifier."""

    if persistent_identifier is None or persistent_identifier.strip() == "":
        return f"bijmantra:{asset_type}:{asset_db_id}"

    normalized = persistent_identifier.strip()
    if normalized.isdigit():
        raise InvalidFairPersistentIdentifier(
            "Integer database primary keys are not valid FAIR persistent identifiers"
        )
    return normalized


def registry_asset_id(connector_key: str, external_asset_id: str) -> str:
    """Return BijMantra's deterministic federated registry id."""

    digest = sha256_digest(
        {
            "connectorKey": connector_key,
            "externalAssetId": external_asset_id,
        }
    )
    return f"fedasset-{digest[:16]}"


def extract_candidate_identity(candidate_asset: dict[str, Any]) -> tuple[str | None, str | None]:
    """Extract external id and kind from a loose candidate asset manifest."""

    external_id = first_nonempty(
        candidate_asset.get("externalAssetId"),
        candidate_asset.get("external_asset_id"),
        candidate_asset.get("id"),
    )
    asset_kind = first_nonempty(
        candidate_asset.get("assetKind"),
        candidate_asset.get("asset_kind"),
        candidate_asset.get("kind"),
    )
    return external_id, asset_kind
