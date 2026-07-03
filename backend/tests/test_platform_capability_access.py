import pytest

from app.platform.capability_access import (
    CapabilityAccessContext,
    CapabilityAccessDenied,
    evaluate_capability_access,
    require_capability_access,
)
from app.platform.dominions import capabilities_for_backend_route, resolve_capability_manifest


def _knowledge_graph_context(
    *,
    installed: bool = True,
    permissions: tuple[str, ...] = ("intelligence.knowledge_graph.read",),
    data_scopes: tuple[str, ...] = ("organization", "asset"),
) -> CapabilityAccessContext:
    installed_capabilities = ("intelligence_fabric.knowledge_graph",) if installed else ()
    return CapabilityAccessContext(
        organization_id=7,
        user_id=42,
        installed_capabilities=installed_capabilities,
        granted_permissions=permissions,
        data_scopes=data_scopes,
        roles=("scientist",),
    )


def test_capability_access_allows_installed_capability_with_permission_and_scope() -> None:
    manifest = resolve_capability_manifest("intelligence_fabric.knowledge_graph")
    assert manifest is not None

    decision = evaluate_capability_access(
        manifest,
        _knowledge_graph_context(),
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization",),
    )

    assert decision.allowed is True
    assert decision.reason == "allowed"


def test_capability_access_rejects_uninstalled_capability() -> None:
    manifest = resolve_capability_manifest("intelligence_fabric.knowledge_graph")
    assert manifest is not None

    decision = evaluate_capability_access(
        manifest,
        _knowledge_graph_context(installed=False),
        required_permission="intelligence.knowledge_graph.read",
    )

    assert decision.allowed is False
    assert decision.reason == "capability_not_installed"


def test_capability_access_rejects_missing_permission() -> None:
    manifest = resolve_capability_manifest("intelligence_fabric.knowledge_graph")
    assert manifest is not None

    decision = evaluate_capability_access(
        manifest,
        _knowledge_graph_context(permissions=()),
        required_permission="intelligence.knowledge_graph.read",
    )

    assert decision.allowed is False
    assert decision.reason == "missing_permission"
    assert decision.missing_permissions == ("intelligence.knowledge_graph.read",)


def test_capability_access_rejects_missing_data_scope() -> None:
    manifest = resolve_capability_manifest("intelligence_fabric.knowledge_graph")
    assert manifest is not None

    decision = evaluate_capability_access(
        manifest,
        _knowledge_graph_context(data_scopes=("organization",)),
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "evidence"),
    )

    assert decision.allowed is False
    assert decision.reason == "missing_data_scope"
    assert decision.missing_data_scopes == ("evidence",)


def test_capability_access_can_start_from_backend_route_resolution() -> None:
    manifest = capabilities_for_backend_route("/api/v2/knowledge-graph/edges")[0]

    decision = require_capability_access(
        manifest,
        _knowledge_graph_context(),
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization",),
    )

    assert decision.allowed is True


def test_require_capability_access_raises_access_denied_with_decision() -> None:
    manifest = resolve_capability_manifest("intelligence_fabric.knowledge_graph")
    assert manifest is not None

    with pytest.raises(CapabilityAccessDenied) as error:
        require_capability_access(
            manifest,
            _knowledge_graph_context(installed=False),
            required_permission="intelligence.knowledge_graph.read",
        )

    assert error.value.decision.reason == "capability_not_installed"
