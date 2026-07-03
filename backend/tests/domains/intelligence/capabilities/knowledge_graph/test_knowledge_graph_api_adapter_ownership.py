from pathlib import Path

from fastapi.routing import APIRoute

from app.api.bijmantra.data import knowledge_graph as legacy_knowledge_graph_api
from app.domains.intelligence.capabilities.knowledge_graph.adapters.api import (
    knowledge_graph as capability_knowledge_graph_api,
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


def test_legacy_knowledge_graph_api_module_is_router_shim() -> None:
    assert legacy_knowledge_graph_api.router is capability_knowledge_graph_api.router


def test_knowledge_graph_api_route_inventory_remains_stable() -> None:
    assert _route_inventory(capability_knowledge_graph_api.router) == [
        ("/knowledge-graph/edges", ("GET",)),
        ("/knowledge-graph/edges", ("POST",)),
        ("/knowledge-graph/evidence-pack", ("GET",)),
        ("/knowledge-graph/evidence-search", ("GET",)),
        ("/knowledge-graph/explorer-snapshot", ("GET",)),
        ("/knowledge-graph/facets", ("GET",)),
        ("/knowledge-graph/neighborhood", ("GET",)),
        ("/knowledge-graph/ranked-candidates", ("GET",)),
        ("/knowledge-graph/reevu-dry-run-preview", ("GET",)),
        ("/knowledge-graph/retrieval-candidates", ("GET",)),
        ("/knowledge-graph/retrieval-diagnostics", ("GET",)),
    ]


def test_legacy_knowledge_graph_api_module_does_not_own_http_logic() -> None:
    backend_root = _backend_root()
    legacy_path = backend_root / "app/api/bijmantra/data/knowledge_graph.py"
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

    source = legacy_path.read_text()
    assert "knowledge_graph.adapters.api.knowledge_graph" in source
    for fragment in forbidden_fragments:
        assert fragment not in source, (
            f"{legacy_path.relative_to(backend_root)} should be a Knowledge Graph "
            f"API adapter shim, but contains {fragment!r}"
        )


def test_knowledge_graph_api_adapter_does_not_import_legacy_services() -> None:
    backend_root = _backend_root()
    adapter_path = (
        backend_root
        / "app/domains/intelligence/capabilities/knowledge_graph/adapters/api/knowledge_graph.py"
    )

    source = adapter_path.read_text()
    assert "from app.services" not in source
    assert "capabilities.knowledge_graph.application" in source
