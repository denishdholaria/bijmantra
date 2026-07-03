from pathlib import Path

from fastapi.routing import APIRoute

from app.api.bijmantra.data import fair_metadata as legacy_fair_metadata_api
from app.api.bijmantra.data import federated_assets as legacy_federated_assets_api
from app.domains.knowledge.capabilities.research_asset_core.adapters.api import (
    fair_metadata as research_asset_fair_metadata_api,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters.api import (
    federated_assets as research_asset_federated_assets_api,
)


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _route_inventory(router) -> list[tuple[str, tuple[str, ...]]]:
    return sorted(
        (
            route.path_format,
            tuple(sorted(method for method in route.methods or set() if method != "HEAD")),
        )
        for route in router.routes
        if isinstance(route, APIRoute)
    )


def test_legacy_research_asset_api_modules_are_router_shims() -> None:
    assert legacy_fair_metadata_api.router is research_asset_fair_metadata_api.router
    assert legacy_federated_assets_api.router is research_asset_federated_assets_api.router


def test_research_asset_api_route_inventory_remains_stable() -> None:
    assert _route_inventory(research_asset_fair_metadata_api.router) == [
        ("/fair-metadata", ("GET",)),
        ("/fair-metadata/{asset_type}/{asset_db_id}", ("GET",)),
        ("/fair-metadata/{asset_type}/{asset_db_id}", ("PUT",)),
    ]
    assert _route_inventory(research_asset_federated_assets_api.router) == [
        ("/federated-assets/audit-events", ("GET",)),
        ("/federated-assets/connectors", ("GET",)),
        ("/federated-assets/connectors", ("POST",)),
        ("/federated-assets/connectors/{connector_key}/dry-run", ("POST",)),
        ("/federated-assets/receipts", ("GET",)),
        ("/federated-assets/registry", ("GET",)),
        ("/federated-assets/registry", ("POST",)),
        ("/federated-assets/registry/{registry_asset_id}/promote-fair", ("POST",)),
    ]


def test_legacy_research_asset_api_modules_do_not_own_http_logic() -> None:
    backend_root = _backend_root()
    legacy_paths = [
        backend_root / "app/api/bijmantra/data/fair_metadata.py",
        backend_root / "app/api/bijmantra/data/federated_assets.py",
    ]
    forbidden_fragments = [
        "APIRouter",
        "HTTPException",
        "Depends",
        "get_current_user",
        "get_tenant_db",
        "app.services",
        "@router.",
        "async def ",
        "response_model",
    ]

    for legacy_path in legacy_paths:
        source = legacy_path.read_text()
        assert "research_asset_core.adapters.api" in source
        for fragment in forbidden_fragments:
            assert fragment not in source, (
                f"{legacy_path.relative_to(backend_root)} should be a ResearchAsset "
                f"API adapter shim, but contains {fragment!r}"
            )


def test_research_asset_api_adapters_do_not_import_legacy_services() -> None:
    backend_root = _backend_root()
    adapter_paths = [
        backend_root
        / "app/domains/knowledge/capabilities/research_asset_core/adapters/api/fair_metadata.py",
        backend_root
        / "app/domains/knowledge/capabilities/research_asset_core/adapters/api/federated_assets.py",
    ]

    for adapter_path in adapter_paths:
        source = adapter_path.read_text()
        assert "from app.services" not in source
        assert "research_asset_core.application" in source
