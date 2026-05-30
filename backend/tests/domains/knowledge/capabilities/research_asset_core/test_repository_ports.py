from pathlib import Path
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.knowledge.capabilities.research_asset_core.application import (
    FairAssetMetadataApplicationService,
    FederatedAssetRegistryApplicationService,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters import (
    DEFAULT_FAIR_ASSET_BINDINGS,
    SqlAlchemyFairAssetMetadataRepository,
    SqlAlchemyFederatedAssetRegistryRepository,
    SqlAlchemyResearchAssetAuditLedger,
)
from app.domains.knowledge.capabilities.research_asset_core.ports import (
    FairAssetMetadataRepository,
    FederatedAssetRegistryRepository,
    ResearchAssetAuditLedger,
)
from app.services.fair_metadata_service import FairAssetMetadataService
from app.services.federated_asset_registry_service import FederatedAssetRegistryService


def test_sqlalchemy_adapters_satisfy_research_asset_ports() -> None:
    db = cast(AsyncSession, object())

    assert isinstance(SqlAlchemyFairAssetMetadataRepository(db), FairAssetMetadataRepository)
    assert isinstance(
        SqlAlchemyFederatedAssetRegistryRepository(db),
        FederatedAssetRegistryRepository,
    )
    assert isinstance(SqlAlchemyResearchAssetAuditLedger(db), ResearchAssetAuditLedger)


def test_default_fair_asset_bindings_include_federated_asset_spine() -> None:
    assert set(DEFAULT_FAIR_ASSET_BINDINGS) == {
        "observation_variable",
        "germplasm",
        "trial",
        "study",
        "federated_asset",
    }
    assert DEFAULT_FAIR_ASSET_BINDINGS["federated_asset"].public_id_field == "registry_asset_id"


def test_legacy_service_names_are_compatibility_shims() -> None:
    assert issubclass(FairAssetMetadataService, FairAssetMetadataApplicationService)
    assert issubclass(FederatedAssetRegistryService, FederatedAssetRegistryApplicationService)


def test_legacy_services_do_not_reintroduce_persistence_or_domain_ownership() -> None:
    backend_root = Path(__file__).resolve().parents[5]
    service_paths = [
        backend_root / "app/services/fair_metadata_service.py",
        backend_root / "app/services/federated_asset_registry_service.py",
    ]
    forbidden_fragments = [
        "from sqlalchemy",
        "from app.models",
        "from app.schemas",
        "from app.domains.knowledge.capabilities.research_asset_core.ports",
        "SqlAlchemy",
        "db.execute(",
        "db.add(",
        "db.flush(",
        "db.refresh(",
        "db.get(",
    ]

    for service_path in service_paths:
        service_source = service_path.read_text()
        for fragment in forbidden_fragments:
            assert fragment not in service_source, (
                f"{service_path.relative_to(backend_root)} should use ResearchAsset "
                f"application facades instead of owning implementation fragment {fragment!r}"
            )
