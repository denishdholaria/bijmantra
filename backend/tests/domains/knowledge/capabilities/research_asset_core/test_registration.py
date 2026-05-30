import pytest

from app.domains.knowledge.capabilities.research_asset_core.application.registration import (
    build_federated_asset_registration_plan,
)
from app.domains.knowledge.capabilities.research_asset_core.domain.policies import (
    UnsupportedFederatedAssetKind,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.registration import (
    FederatedAssetRegistrationCommand,
)


def _command(**overrides):
    values = {
        "connector_key": "irri-brapi",
        "external_asset_id": " dataset:rice-yield-2026 ",
        "asset_kind": "dataset",
        "title": "Rice Yield Trial Metadata 2026",
        "source_uri": "https://example.org/datasets/rice-yield-2026",
        "license": "CC-BY-4.0",
        "data_standard": "BrAPI v2.1",
        "standards_mappings": {"brapi": "v2.1"},
        "metadata": {"crop": "rice"},
        "provenance": {"registered_from": "operator-reviewed dry run"},
    }
    values.update(overrides)
    return FederatedAssetRegistrationCommand(**values)


def test_registration_plan_normalizes_identity_and_builds_digest() -> None:
    plan = build_federated_asset_registration_plan(_command())
    duplicate = build_federated_asset_registration_plan(_command())

    assert plan.external_asset_id == "dataset:rice-yield-2026"
    assert plan.asset_kind == "dataset"
    assert plan.registry_asset_id.startswith("fedasset-")
    assert plan.registry_asset_id == duplicate.registry_asset_id
    assert plan.source_digest == duplicate.source_digest


def test_registration_plan_preserves_operator_supplied_digest() -> None:
    plan = build_federated_asset_registration_plan(_command(source_digest="sha256:operator"))

    assert plan.source_digest == "sha256:operator"


def test_registration_plan_rejects_unsupported_asset_kind() -> None:
    with pytest.raises(UnsupportedFederatedAssetKind):
        build_federated_asset_registration_plan(_command(asset_kind="raw-report"))
