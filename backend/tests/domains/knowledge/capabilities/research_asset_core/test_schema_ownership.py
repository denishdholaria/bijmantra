from pathlib import Path

from app.domains.knowledge.capabilities.research_asset_core.schemas import (
    FAIRAssetMetadataUpsert as CapabilityFAIRAssetMetadataUpsert,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas import (
    FederatedAssetConnectorCreate as CapabilityFederatedAssetConnectorCreate,
)
from app.schemas.fair_metadata import FAIRAssetMetadataUpsert as LegacyFAIRAssetMetadataUpsert
from app.schemas.federated_assets import (
    FederatedAssetConnectorCreate as LegacyFederatedAssetConnectorCreate,
)


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[5]


def test_global_research_asset_schema_modules_are_compatibility_shims() -> None:
    assert LegacyFAIRAssetMetadataUpsert is CapabilityFAIRAssetMetadataUpsert
    assert LegacyFederatedAssetConnectorCreate is CapabilityFederatedAssetConnectorCreate


def test_global_research_asset_schema_files_do_not_own_contract_implementations() -> None:
    backend_root = _backend_root()
    shim_paths = [
        backend_root / "app/schemas/fair_metadata.py",
        backend_root / "app/schemas/federated_assets.py",
    ]
    forbidden_fragments = [
        "class ",
        "BaseModel",
        "ConfigDict",
        "Field(",
        "from pydantic",
        "from datetime",
    ]

    for shim_path in shim_paths:
        source = shim_path.read_text()
        assert "research_asset_core.schemas" in source
        for fragment in forbidden_fragments:
            assert fragment not in source, (
                f"{shim_path.relative_to(backend_root)} should re-export ResearchAsset "
                f"contracts instead of owning implementation fragment {fragment!r}"
            )


def test_research_asset_runtime_code_imports_capability_owned_contracts() -> None:
    backend_root = _backend_root()
    capability_paths = [
        backend_root
        / "app/domains/knowledge/capabilities/research_asset_core/application/fair_metadata_service.py",
        backend_root
        / "app/domains/knowledge/capabilities/research_asset_core/application/federated_registry_service.py",
        backend_root
        / "app/domains/knowledge/capabilities/research_asset_core/adapters/api/fair_metadata.py",
        backend_root
        / "app/domains/knowledge/capabilities/research_asset_core/adapters/api/federated_assets.py",
    ]
    forbidden_fragments = [
        "app.schemas.fair_metadata",
        "app.schemas.federated_assets",
    ]

    for capability_path in capability_paths:
        source = capability_path.read_text()
        assert "research_asset_core.schemas" in source
        for fragment in forbidden_fragments:
            assert fragment not in source, (
                f"{capability_path.relative_to(backend_root)} should import ResearchAsset "
                f"contracts from capability schemas instead of {fragment!r}"
            )
