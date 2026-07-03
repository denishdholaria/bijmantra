import pytest

from app.domains.knowledge.capabilities.research_asset_core.domain.policies import (
    FEDERATED_ASSET_PROMOTE_FAIR_ACTION,
    FEDERATED_ASSET_REGISTER_ACTION,
    InvalidFairPersistentIdentifier,
    FEDERATED_AUDIT_ACTIONS,
    FEDERATED_CONNECTOR_DRY_RUN_ACTION,
    FEDERATED_CONNECTOR_UPSERT_ACTION,
    UnsupportedFederatedAssetKind,
    UnsupportedFederatedConnectorType,
    UnknownFairAssetType,
    extract_candidate_identity,
    first_nonempty,
    registry_asset_id,
    require_supported_connector_type,
    require_supported_fair_asset_type,
    require_supported_federated_asset_kind,
    resolve_persistent_identifier,
    sha256_digest,
)


def test_research_asset_policy_normalizes_supported_terms() -> None:
    assert require_supported_connector_type("fairgrounds-catalog") == "fairgrounds_catalog"
    assert require_supported_federated_asset_kind("ai-model") == "ai_model"
    assert require_supported_fair_asset_type("observation-variable") == "observation_variable"
    assert require_supported_fair_asset_type("registry-asset") == "federated_asset"


def test_research_asset_policy_declares_canonical_audit_actions() -> None:
    assert FEDERATED_AUDIT_ACTIONS == (
        FEDERATED_CONNECTOR_UPSERT_ACTION,
        FEDERATED_CONNECTOR_DRY_RUN_ACTION,
        FEDERATED_ASSET_REGISTER_ACTION,
        FEDERATED_ASSET_PROMOTE_FAIR_ACTION,
    )


def test_research_asset_policy_rejects_unsupported_terms() -> None:
    with pytest.raises(UnsupportedFederatedConnectorType):
        require_supported_connector_type("spreadsheet_scraper")
    with pytest.raises(UnsupportedFederatedAssetKind):
        require_supported_federated_asset_kind("raw_report")
    with pytest.raises(UnknownFairAssetType):
        require_supported_fair_asset_type("invoice")


def test_research_asset_policy_keeps_identifiers_deterministic() -> None:
    digest_a = sha256_digest({"b": 2, "a": 1})
    digest_b = sha256_digest({"a": 1, "b": 2})

    assert digest_a == digest_b
    assert registry_asset_id("irri-brapi", "dataset:rice-yield-2026") == registry_asset_id(
        "irri-brapi",
        "dataset:rice-yield-2026",
    )
    assert registry_asset_id("irri-brapi", "dataset:rice-yield-2026").startswith("fedasset-")


def test_research_asset_policy_resolves_fair_persistent_identifiers() -> None:
    assert (
        resolve_persistent_identifier(
            None,
            asset_type="germplasm",
            asset_db_id="IR64",
        )
        == "bijmantra:germplasm:IR64"
    )
    assert (
        resolve_persistent_identifier(
            " doi:10.123/example ",
            asset_type="germplasm",
            asset_db_id="IR64",
        )
        == "doi:10.123/example"
    )
    with pytest.raises(InvalidFairPersistentIdentifier):
        resolve_persistent_identifier("12345", asset_type="germplasm", asset_db_id="IR64")


def test_research_asset_policy_extracts_candidate_identity_aliases() -> None:
    assert first_nonempty(None, " ", "dataset") == "dataset"
    assert extract_candidate_identity({"external_asset_id": "abc", "kind": "dataset"}) == (
        "abc",
        "dataset",
    )
    assert extract_candidate_identity({"externalAssetId": "xyz", "assetKind": "api"}) == (
        "xyz",
        "api",
    )
