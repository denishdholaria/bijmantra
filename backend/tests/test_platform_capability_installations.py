from types import SimpleNamespace

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import OrganizationCapabilityInstallation
from app.platform.capability_access import evaluate_capability_access
from app.platform.capability_installations import (
    UnknownCapability,
    build_persisted_capability_access_context,
    build_persisted_capability_access_context_if_present,
    disable_capability_for_organization,
    get_capability_installation,
    install_capability_for_organization,
    list_capability_installations,
    list_enabled_capability_installations,
)
from app.platform.dominions import resolve_capability_manifest


KNOWLEDGE_GRAPH_CAPABILITY_ID = "intelligence_fabric.knowledge_graph"
RESEARCH_ASSET_CAPABILITY_ID = "scientific_publishing_fair_exchange.research_asset_core"


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
    organization_id: int = 7,
    permissions: tuple[str, ...] | None = ("intelligence.knowledge_graph.read",),
    data_scopes: tuple[str, ...] | None = ("organization", "asset", "evidence"),
) -> SimpleNamespace:
    payload = {
        "id": 42,
        "organization_id": organization_id,
        "roles": ("knowledge_curator",),
    }
    if permissions is not None:
        payload["permissions"] = permissions
    if data_scopes is not None:
        payload["data_scopes"] = data_scopes
    return SimpleNamespace(**payload)


class _ActorWithLazyRoleError:
    id = 42
    organization_id = 7

    @property
    def permissions(self) -> tuple[str, ...]:
        raise SQLAlchemyError("relationship is not eagerly loaded")

    @property
    def roles(self) -> tuple[str, ...]:
        raise SQLAlchemyError("relationship is not eagerly loaded")


@pytest.mark.asyncio
async def test_install_capability_persists_manifest_permissions_and_scopes(
    async_db_session: AsyncSession,
) -> None:
    installed = await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
        actor_user_id=42,
    )

    assert installed.enabled is True
    assert installed.lifecycle_state == "installed"
    assert installed.capability_id == KNOWLEDGE_GRAPH_CAPABILITY_ID
    assert installed.granted_permissions == [
        "intelligence.knowledge_graph.read",
        "intelligence.knowledge_graph.write",
    ]
    assert installed.data_scopes == ["organization", "asset", "evidence", "provenance"]
    assert installed.installed_by_user_id == 42

    fetched = await get_capability_installation(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
    )
    assert fetched is not None
    assert fetched.id == installed.id


@pytest.mark.asyncio
async def test_disable_capability_removes_it_from_enabled_access_context(
    async_db_session: AsyncSession,
) -> None:
    await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
    )

    disabled = await disable_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
        actor_user_id=42,
    )

    assert disabled.enabled is False
    assert disabled.lifecycle_state == "disabled"
    assert disabled.disabled_by_user_id == 42
    assert disabled.disabled_at is not None

    enabled = await list_enabled_capability_installations(async_db_session, organization_id=7)
    assert enabled == []

    context = await build_persisted_capability_access_context(
        async_db_session,
        _actor(),
    )
    assert context.installed_capabilities == ()


@pytest.mark.asyncio
async def test_list_capability_installations_includes_disabled_rows(
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

    all_installations = await list_capability_installations(async_db_session, organization_id=7)
    enabled_installations = await list_enabled_capability_installations(
        async_db_session,
        organization_id=7,
    )

    assert [installation.capability_id for installation in all_installations] == [
        KNOWLEDGE_GRAPH_CAPABILITY_ID,
    ]
    assert all_installations[0].enabled is False
    assert enabled_installations == []


@pytest.mark.asyncio
async def test_persisted_context_intersects_user_permissions_with_org_installation(
    async_db_session: AsyncSession,
) -> None:
    await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
        granted_permissions=("intelligence.knowledge_graph.read",),
        data_scopes=("organization", "asset", "evidence"),
    )

    context = await build_persisted_capability_access_context(
        async_db_session,
        _actor(
            permissions=(
                "intelligence.knowledge_graph.read",
                "intelligence.knowledge_graph.write",
            ),
            data_scopes=("organization", "asset", "evidence", "provenance"),
        ),
    )

    assert context.installed_capabilities == (KNOWLEDGE_GRAPH_CAPABILITY_ID,)
    assert context.granted_permissions == ("intelligence.knowledge_graph.read",)
    assert context.data_scopes == ("organization", "asset", "evidence")

    manifest = resolve_capability_manifest(KNOWLEDGE_GRAPH_CAPABILITY_ID)
    assert manifest is not None
    read_decision = evaluate_capability_access(
        manifest,
        context,
        required_permission="intelligence.knowledge_graph.read",
        required_data_scopes=("organization", "evidence"),
    )
    write_decision = evaluate_capability_access(
        manifest,
        context,
        required_permission="intelligence.knowledge_graph.write",
    )

    assert read_decision.allowed is True
    assert write_decision.allowed is False
    assert write_decision.reason == "missing_permission"


@pytest.mark.asyncio
async def test_persisted_context_uses_install_grants_when_actor_roles_are_not_loaded(
    async_db_session: AsyncSession,
) -> None:
    await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
        granted_permissions=("intelligence.knowledge_graph.read",),
        data_scopes=("organization", "asset"),
    )

    context = await build_persisted_capability_access_context(
        async_db_session,
        _ActorWithLazyRoleError(),
    )

    assert context.installed_capabilities == (KNOWLEDGE_GRAPH_CAPABILITY_ID,)
    assert context.granted_permissions == ("intelligence.knowledge_graph.read",)
    assert context.data_scopes == ("organization", "asset")
    assert context.roles == ()


@pytest.mark.asyncio
async def test_install_capability_preserves_explicit_empty_grants(
    async_db_session: AsyncSession,
) -> None:
    await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
        granted_permissions=(),
        data_scopes=(),
    )

    context = await build_persisted_capability_access_context(
        async_db_session,
        _actor(permissions=None, data_scopes=None),
    )

    assert context.installed_capabilities == (KNOWLEDGE_GRAPH_CAPABILITY_ID,)
    assert context.granted_permissions == ()
    assert context.data_scopes == ()

    manifest = resolve_capability_manifest(KNOWLEDGE_GRAPH_CAPABILITY_ID)
    assert manifest is not None
    decision = evaluate_capability_access(
        manifest,
        context,
        required_permission="intelligence.knowledge_graph.read",
    )

    assert decision.allowed is False
    assert decision.reason == "missing_permission"


@pytest.mark.asyncio
async def test_persisted_context_if_present_distinguishes_missing_from_disabled_row(
    async_db_session: AsyncSession,
) -> None:
    missing_context = await build_persisted_capability_access_context_if_present(
        async_db_session,
        _actor(permissions=None, data_scopes=None),
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
    )
    assert missing_context is None

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

    disabled_context = await build_persisted_capability_access_context_if_present(
        async_db_session,
        _actor(permissions=None, data_scopes=None),
        capability_id=KNOWLEDGE_GRAPH_CAPABILITY_ID,
    )

    assert disabled_context is not None
    assert disabled_context.installed_capabilities == ()
    assert disabled_context.granted_permissions == ()
    assert disabled_context.data_scopes == ()


@pytest.mark.asyncio
async def test_persisted_context_is_tenant_scoped(
    async_db_session: AsyncSession,
) -> None:
    await install_capability_for_organization(
        async_db_session,
        organization_id=8,
        capability_id=RESEARCH_ASSET_CAPABILITY_ID,
    )

    context = await build_persisted_capability_access_context(
        async_db_session,
        _actor(organization_id=7, permissions=None, data_scopes=None),
    )

    assert context.organization_id == 7
    assert context.installed_capabilities == ()
    assert context.granted_permissions == ()
    assert context.data_scopes == ()


@pytest.mark.asyncio
async def test_install_capability_rejects_unknown_manifest(
    async_db_session: AsyncSession,
) -> None:
    with pytest.raises(UnknownCapability):
        await install_capability_for_organization(
            async_db_session,
            organization_id=7,
            capability_id="unknown.capability",
        )
