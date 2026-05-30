"""Application planning for explicit federated ResearchAsset registration."""

from app.domains.knowledge.capabilities.research_asset_core.domain.policies import (
    registry_asset_id,
    require_supported_federated_asset_kind,
    sha256_digest,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.registration import (
    FederatedAssetRegistrationCommand,
    FederatedAssetRegistrationPlan,
)


def build_federated_asset_registration_plan(
    command: FederatedAssetRegistrationCommand,
) -> FederatedAssetRegistrationPlan:
    """Build deterministic registry id, normalized kind, and source digest."""

    external_asset_id = command.external_asset_id.strip()
    asset_kind = require_supported_federated_asset_kind(command.asset_kind)
    source_digest = command.source_digest or sha256_digest(
        {
            "connectorKey": command.connector_key,
            "externalAssetId": external_asset_id,
            "assetKind": asset_kind,
            "title": command.title,
            "sourceUri": command.source_uri,
            "license": command.license,
            "dataStandard": command.data_standard,
            "standardsMappings": command.standards_mappings,
            "metadata": command.metadata,
            "provenance": command.provenance,
        }
    )
    return FederatedAssetRegistrationPlan(
        registry_asset_id=registry_asset_id(command.connector_key, external_asset_id),
        external_asset_id=external_asset_id,
        asset_kind=asset_kind,
        source_digest=source_digest,
    )
