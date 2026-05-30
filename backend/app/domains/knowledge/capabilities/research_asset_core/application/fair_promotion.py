"""Application helpers for explicit federated-asset FAIR promotion."""

from datetime import UTC, datetime
from typing import Any

from app.domains.knowledge.capabilities.research_asset_core.domain.policies import (
    first_nonempty,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.fair_promotion import (
    FairPromotionCommand,
    FederatedAssetPromotionSource,
    FederatedConnectorReference,
)


def build_fair_promotion_payload(
    *,
    asset: FederatedAssetPromotionSource,
    connector: FederatedConnectorReference | None,
    command: FairPromotionCommand,
    promoted_at: datetime | None = None,
) -> dict[str, Any]:
    """Build FAIR metadata fields for an explicit federated asset promotion."""

    connector_key = connector.connector_key if connector else None
    connector_name = connector.display_name if connector else None
    promotion_time = promoted_at or datetime.now(UTC)
    source_reference = {
        "referenceType": "federated_asset",
        "registryAssetId": asset.registry_asset_id,
        "externalAssetId": asset.external_asset_id,
        "connectorKey": connector_key,
        "sourceUri": asset.source_uri,
        "sourceDigest": asset.source_digest,
    }
    provenance = {
        "promotion": {
            "workflow": "federated_asset_fair_promotion.v1",
            "promotedAt": promotion_time.isoformat(),
        },
        "federatedAsset": {
            "registryAssetId": asset.registry_asset_id,
            "externalAssetId": asset.external_asset_id,
            "assetKind": asset.asset_kind,
            "connectorKey": connector_key,
        },
    }
    if asset.provenance:
        provenance["sourceProvenance"] = dict(asset.provenance)
    if command.provenance:
        provenance["operatorProvenance"] = dict(command.provenance)

    fair_payload: dict[str, Any] = {
        "title": first_nonempty(command.title, asset.title),
        "description": command.description if command.description is not None else asset.description,
        "license": first_nonempty(command.license, asset.license),
        "data_standard": first_nonempty(command.data_standard, asset.data_standard),
        "data_source": first_nonempty(command.data_source, connector_name, connector_key),
        "provenance": provenance,
        "external_references": [
            source_reference,
            *list(command.external_references),
        ],
    }
    if "persistent_identifier" in command.fields_set:
        fair_payload["persistent_identifier"] = command.persistent_identifier
    if "access_rights" in command.fields_set:
        fair_payload["access_rights"] = command.access_rights
    if "confidence" in command.fields_set:
        fair_payload["confidence"] = command.confidence

    for field in (
        "keywords",
        "ontology_terms",
        "contributors",
        "funding_acknowledgements",
        "evidence_refs",
    ):
        if field in command.fields_set:
            fair_payload[field] = list(getattr(command, field))

    return fair_payload
