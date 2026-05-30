from datetime import UTC, datetime

from app.domains.knowledge.capabilities.research_asset_core.application.fair_promotion import (
    build_fair_promotion_payload,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.fair_promotion import (
    FairPromotionCommand,
    FederatedAssetPromotionSource,
    FederatedConnectorReference,
)


def test_fair_promotion_payload_preserves_source_and_operator_provenance() -> None:
    payload = build_fair_promotion_payload(
        asset=FederatedAssetPromotionSource(
            registry_asset_id="fedasset-abc",
            external_asset_id="dataset:rice-yield",
            asset_kind="dataset",
            title="Rice Yield Dataset",
            description="Reviewed trial metadata.",
            source_uri="https://example.org/rice-yield",
            source_digest="sha256:abc",
            license="CC-BY-4.0",
            data_standard="BrAPI v2.1",
            provenance={"registered_from": "operator-reviewed dry run"},
        ),
        connector=FederatedConnectorReference(
            connector_key="irri-brapi",
            display_name="IRRI BrAPI Catalog",
        ),
        command=FairPromotionCommand(
            fields_set=frozenset({"keywords", "confidence", "provenance"}),
            keywords=("rice", "yield"),
            confidence=0.91,
            provenance={"reviewed_by": "data-steward"},
        ),
        promoted_at=datetime(2026, 5, 28, 12, 0, tzinfo=UTC),
    )

    assert payload["title"] == "Rice Yield Dataset"
    assert payload["license"] == "CC-BY-4.0"
    assert payload["data_standard"] == "BrAPI v2.1"
    assert payload["data_source"] == "IRRI BrAPI Catalog"
    assert payload["keywords"] == ["rice", "yield"]
    assert payload["confidence"] == 0.91
    assert payload["external_references"][0]["registryAssetId"] == "fedasset-abc"
    assert payload["external_references"][0]["connectorKey"] == "irri-brapi"
    assert payload["provenance"]["promotion"]["workflow"] == "federated_asset_fair_promotion.v1"
    assert payload["provenance"]["promotion"]["promotedAt"] == "2026-05-28T12:00:00+00:00"
    assert payload["provenance"]["sourceProvenance"] == {
        "registered_from": "operator-reviewed dry run"
    }
    assert payload["provenance"]["operatorProvenance"] == {"reviewed_by": "data-steward"}


def test_fair_promotion_payload_respects_explicit_null_pid_field() -> None:
    payload = build_fair_promotion_payload(
        asset=FederatedAssetPromotionSource(
            registry_asset_id="fedasset-abc",
            external_asset_id="dataset:rice-yield",
            asset_kind="dataset",
            title="Rice Yield Dataset",
        ),
        connector=None,
        command=FairPromotionCommand(
            fields_set=frozenset({"persistent_identifier", "access_rights"}),
            persistent_identifier=None,
            access_rights="restricted",
        ),
        promoted_at=datetime(2026, 5, 28, 12, 0, tzinfo=UTC),
    )

    assert "persistent_identifier" in payload
    assert payload["persistent_identifier"] is None
    assert payload["access_rights"] == "restricted"
