from pathlib import Path

from tests.utils.capability_boundary import assert_no_forbidden_imports, python_files


LEGACY_RESEARCH_ASSET_MODULES = (
    "app.api.bijmantra.data.fair_metadata",
    "app.api.bijmantra.data.federated_assets",
    "app.schemas.fair_metadata",
    "app.schemas.federated_assets",
    "app.services.fair_metadata_service",
    "app.services.federated_asset_registry_service",
)


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _capability_root() -> Path:
    return _backend_root() / "app/domains/knowledge/capabilities/research_asset_core"


def _assert_no_forbidden_imports(paths: list[Path], forbidden_prefixes: tuple[str, ...]) -> None:
    assert_no_forbidden_imports(
        paths,
        forbidden_prefixes,
        repo_root=_backend_root(),
        boundary_name="ResearchAsset",
    )


def test_research_asset_capability_never_imports_legacy_shims() -> None:
    _assert_no_forbidden_imports(
        python_files(_capability_root()),
        LEGACY_RESEARCH_ASSET_MODULES,
    )


def test_production_code_does_not_depend_on_legacy_research_asset_shims() -> None:
    backend_root = _backend_root()
    allowed_shim_paths = {
        backend_root / "app/api/bijmantra/data/fair_metadata.py",
        backend_root / "app/api/bijmantra/data/federated_assets.py",
        backend_root / "app/schemas/fair_metadata.py",
        backend_root / "app/schemas/federated_assets.py",
        backend_root / "app/services/fair_metadata_service.py",
        backend_root / "app/services/federated_asset_registry_service.py",
    }
    production_paths = [
        path
        for path in python_files(backend_root / "app")
        if path not in allowed_shim_paths
    ]

    _assert_no_forbidden_imports(production_paths, LEGACY_RESEARCH_ASSET_MODULES)


def test_inward_layers_do_not_import_infrastructure() -> None:
    inward_paths = (
        python_files(_capability_root() / "domain")
        + python_files(_capability_root() / "ports")
        + python_files(_capability_root() / "schemas")
    )

    _assert_no_forbidden_imports(
        inward_paths,
        (
            "app.api",
            "app.middleware",
            "app.models",
            "app.services",
            "sqlalchemy",
            "fastapi",
        ),
    )


def test_application_layer_does_not_import_legacy_or_http_surfaces() -> None:
    _assert_no_forbidden_imports(
        python_files(_capability_root() / "application"),
        (
            *LEGACY_RESEARCH_ASSET_MODULES,
            "app.api",
            "app.domains.knowledge.capabilities.research_asset_core.adapters",
            "app.middleware",
            "app.models",
            "fastapi",
            "sqlalchemy",
        ),
    )


def test_adapter_layers_do_not_import_legacy_research_asset_shims() -> None:
    _assert_no_forbidden_imports(
        python_files(_capability_root() / "adapters"),
        LEGACY_RESEARCH_ASSET_MODULES,
    )
