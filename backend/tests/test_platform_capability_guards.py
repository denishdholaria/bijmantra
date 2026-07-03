from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import MissingGreenlet
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import OrganizationCapabilityInstallation
from app.platform.capability_guards import (
    capability_context_from_actor,
    require_platform_capability_api_access,
)
from app.platform.capability_installations import (
    disable_capability_for_organization,
    install_capability_for_organization,
)
from app.platform.dominions import resolve_capability_manifest


KNOWLEDGE_GRAPH_CAPABILITY_ID = "intelligence_fabric.knowledge_graph"


@pytest.fixture(autouse=True)
async def create_capability_installation_table(async_db_session: AsyncSession):
    engine = async_db_session.bind
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: OrganizationCapabilityInstallation.__table__.create(
                sync_conn,
                checkfirst=True,
            )
        )
    yield


def _actor(
    *,
    installed_capabilities: tuple[str, ...] = (KNOWLEDGE_GRAPH_CAPABILITY_ID,),
    permissions: tuple[str, ...] = ("intelligence.knowledge_graph.read",),
    data_scopes: tuple[str, ...] = ("organization", "asset", "evidence"),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=42,
        organization_id=7,
        installed_capabilities=installed_capabilities,
        permissions=permissions,
        data_scopes=data_scopes,
        roles=("knowledge_curator",),
    )


@pytest.mark.asyncio
async def test_platform_capability_guard_rejects_missing_permission() -> None:
    with pytest.raises(HTTPException) as error:
        await require_platform_capability_api_access(
            KNOWLEDGE_GRAPH_CAPABILITY_ID,
            _actor(permissions=("intelligence.knowledge_graph.read",)),
            required_permission="intelligence.knowledge_graph.write",
        )

    assert error.value.status_code == 403
    assert error.value.detail == {
        "reason": "missing_permission",
        "capabilityId": KNOWLEDGE_GRAPH_CAPABILITY_ID,
        "missingPermissions": ["intelligence.knowledge_graph.write"],
        "missingDataScopes": [],
    }


@pytest.mark.asyncio
async def test_platform_capability_guard_treats_persisted_disabled_state_as_authoritative(
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
        await require_platform_capability_api_access(
            KNOWLEDGE_GRAPH_CAPABILITY_ID,
            _actor(),
            db=async_db_session,
            required_permission="intelligence.knowledge_graph.read",
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "capability_not_installed"


def test_capability_context_actor_fallback_uses_manifest_defaults_for_legacy_superuser() -> None:
    manifest = resolve_capability_manifest(KNOWLEDGE_GRAPH_CAPABILITY_ID)
    assert manifest is not None
    actor = SimpleNamespace(id=42, organization_id=7, is_superuser=True)

    context = capability_context_from_actor(actor, manifest=manifest)

    assert context.installed_capabilities == (KNOWLEDGE_GRAPH_CAPABILITY_ID,)
    assert context.granted_permissions == manifest.required_permissions
    assert context.data_scopes == manifest.data_scopes


def test_capability_context_actor_fallback_skips_async_orm_lazy_attributes() -> None:
    manifest = resolve_capability_manifest(KNOWLEDGE_GRAPH_CAPABILITY_ID)
    assert manifest is not None

    class ActorWithLazyAttributes:
        id = 42
        organization_id = 7

        @property
        def organization(self):
            raise MissingGreenlet("organization would lazy-load")

        @property
        def permissions(self):
            raise MissingGreenlet("permissions would lazy-load")

        @property
        def roles(self):
            raise MissingGreenlet("roles would lazy-load")

    context = capability_context_from_actor(ActorWithLazyAttributes(), manifest=manifest)

    assert context.installed_capabilities == (KNOWLEDGE_GRAPH_CAPABILITY_ID,)
    assert context.granted_permissions == manifest.required_permissions
    assert context.data_scopes == manifest.data_scopes
    assert context.roles == ()


@pytest.mark.asyncio
async def test_platform_capability_guard_accepts_mapping_actor_shape() -> None:
    await require_platform_capability_api_access(
        KNOWLEDGE_GRAPH_CAPABILITY_ID,
        {
            "id": 42,
            "organization_id": 7,
            "installed_capabilities": [KNOWLEDGE_GRAPH_CAPABILITY_ID],
            "permissions": ["intelligence.knowledge_graph.read"],
            "data_scopes": ["organization", "asset"],
        },
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization",),
    )
