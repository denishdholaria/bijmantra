from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.adapters.api.knowledge_graph import (
    create_knowledge_graph_edge,
    list_knowledge_graph_edges,
)
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgeCreate,
)
from app.platform.capability_installations import (
    disable_capability_for_organization,
    install_capability_for_organization,
)


KNOWLEDGE_GRAPH_CAPABILITY_ID = "intelligence_fabric.knowledge_graph"


def _actor(
    *,
    installed_capabilities: tuple[str, ...] = (KNOWLEDGE_GRAPH_CAPABILITY_ID,),
    permissions: tuple[str, ...] = (
        "intelligence.knowledge_graph.read",
        "intelligence.knowledge_graph.write",
    ),
    data_scopes: tuple[str, ...] = ("organization", "asset", "evidence", "provenance"),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=42,
        organization_id=7,
        installed_capabilities=installed_capabilities,
        permissions=permissions,
        data_scopes=data_scopes,
        roles=("knowledge_curator",),
    )


def _edge_payload() -> KnowledgeGraphEdgeCreate:
    return KnowledgeGraphEdgeCreate(
        source_asset_type="germplasm",
        source_asset_id="IR64",
        relationship_type="has_trait",
        target_asset_type="observation_variable",
        target_asset_id="CO:0000001",
        evidence_refs=[{"entity_id": "trial:TRIAL-1"}],
    )


@pytest.mark.asyncio
async def test_knowledge_graph_api_rejects_uninstalled_capability_before_data_access() -> None:
    with pytest.raises(HTTPException) as error:
        await list_knowledge_graph_edges(
            source_asset_type=None,
            source_asset_id=None,
            target_asset_type=None,
            target_asset_id=None,
            relationship_type=None,
            limit=20,
            offset=0,
            db=object(),
            current_user=_actor(installed_capabilities=()),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "capability_not_installed"
    assert error.value.detail["capabilityId"] == KNOWLEDGE_GRAPH_CAPABILITY_ID


@pytest.mark.asyncio
async def test_knowledge_graph_api_rejects_missing_permission_before_data_access() -> None:
    with pytest.raises(HTTPException) as error:
        await create_knowledge_graph_edge(
            payload=_edge_payload(),
            db=object(),
            current_user=_actor(permissions=("intelligence.knowledge_graph.read",)),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "missing_permission"
    assert error.value.detail["missingPermissions"] == ["intelligence.knowledge_graph.write"]


@pytest.mark.asyncio
async def test_knowledge_graph_api_rejects_missing_data_scope_before_data_access() -> None:
    with pytest.raises(HTTPException) as error:
        await create_knowledge_graph_edge(
            payload=_edge_payload(),
            db=object(),
            current_user=_actor(data_scopes=("organization", "asset")),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "missing_data_scope"
    assert error.value.detail["missingDataScopes"] == ["evidence", "provenance"]


@pytest.mark.asyncio
async def test_knowledge_graph_api_uses_disabled_persisted_install_state(
    async_db_session: AsyncSession,
) -> None:
    await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
    )
    await disable_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
    )

    with pytest.raises(HTTPException) as error:
        await list_knowledge_graph_edges(
            source_asset_type=None,
            source_asset_id=None,
            target_asset_type=None,
            target_asset_id=None,
            relationship_type=None,
            limit=20,
            offset=0,
            db=async_db_session,
            current_user=_actor(),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "capability_not_installed"


@pytest.mark.asyncio
async def test_knowledge_graph_api_uses_persisted_data_scope_grants(
    async_db_session: AsyncSession,
) -> None:
    await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
        data_scopes=("organization", "asset"),
    )

    with pytest.raises(HTTPException) as error:
        await create_knowledge_graph_edge(
            payload=_edge_payload(),
            db=async_db_session,
            current_user=_actor(),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "missing_data_scope"
    assert error.value.detail["missingDataScopes"] == ["evidence", "provenance"]
