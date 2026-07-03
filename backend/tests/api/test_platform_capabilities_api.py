from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.bijmantra.system.capabilities import (
    CapabilityBootstrapRequest,
    CapabilityInstallRequest,
    bootstrap_first_wave_capabilities,
    disable_capability,
    get_capability_state,
    get_current_user_capability_context,
    install_capability,
    list_capability_manifests,
    list_organization_capability_installations,
)
from app.api.bijmantra.system.router import system_router
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.core import User
from app.models.platform import OrganizationCapabilityInstallation
from tests.conftest import AsyncTestingSessionLocal


CAPABILITY_ID = "scientific_publishing_fair_exchange.research_asset_core"


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


def _admin_user(*, organization_id: int = 7) -> SimpleNamespace:
    return SimpleNamespace(id=42, organization_id=organization_id, is_superuser=True)


def _regular_user(
    *,
    organization_id: int = 7,
    roles: tuple[str, ...] = (),
    permissions: tuple[str, ...] | None = None,
    data_scopes: tuple[str, ...] | None = None,
) -> SimpleNamespace:
    payload = {
        "id": 43,
        "organization_id": organization_id,
        "is_superuser": False,
        "roles": roles,
    }
    if permissions is not None:
        payload["permissions"] = permissions
    if data_scopes is not None:
        payload["data_scopes"] = data_scopes
    return SimpleNamespace(**payload)


@asynccontextmanager
async def _http_client_for_user(user: User) -> AsyncIterator[AsyncClient]:
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "organization_id": user.organization_id,
            "is_superuser": user.is_superuser,
        },
        expires_delta=timedelta(minutes=30),
    )

    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_capability_management_routes_are_mounted_on_system_router() -> None:
    route_paths = {getattr(route, "path", "") for route in system_router.routes}

    assert "/system/capabilities/manifest" in route_paths
    assert "/system/capabilities/installations" in route_paths
    assert "/system/capabilities/bootstrap" in route_paths
    assert "/system/capabilities/{capability_id}" in route_paths
    assert "/platform/capabilities/me" in route_paths


@pytest.mark.asyncio
async def test_manifest_endpoint_requires_superuser() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await list_capability_manifests(current_user=_regular_user())

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_installation_listing_endpoint_requires_superuser(
    async_db_session: AsyncSession,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await list_organization_capability_installations(
            organization_id=None,
            db=async_db_session,
            current_user=_regular_user(),
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_manifest_endpoint_lists_registered_capabilities() -> None:
    response = await list_capability_manifests(current_user=_admin_user())

    data = response.model_dump()
    capability_ids = {capability["id"] for capability in data["capabilities"]}

    assert "intelligence_fabric.knowledge_graph" in capability_ids
    assert CAPABILITY_ID in capability_ids


@pytest.mark.asyncio
async def test_install_endpoint_persists_tenant_capability_state(
    async_db_session: AsyncSession,
) -> None:
    current_user = _admin_user()

    response = await install_capability(
        CAPABILITY_ID,
        CapabilityInstallRequest(
            granted_permissions=["research_assets.read"],
            data_scopes=["organization", "asset"],
            settings={"mode": "pilot"},
        ),
        db=async_db_session,
        current_user=current_user,
    )

    data = response.model_dump()
    assert data["manifest"]["id"] == CAPABILITY_ID
    assert data["installation"] == {
        "capability_id": CAPABILITY_ID,
        "organization_id": current_user.organization_id,
        "enabled": True,
        "lifecycle_state": "installed",
        "granted_permissions": ["research_assets.read"],
        "data_scopes": ["organization", "asset"],
        "settings": {"mode": "pilot"},
        "installed_by_user_id": current_user.id,
        "disabled_by_user_id": None,
        "disabled_at": None,
    }

    list_response = await list_organization_capability_installations(
        organization_id=None,
        db=async_db_session,
        current_user=current_user,
    )
    assert list_response.installations[0].capability_id == CAPABILITY_ID


@pytest.mark.asyncio
async def test_current_user_capability_context_does_not_require_superuser(
    async_db_session: AsyncSession,
) -> None:
    current_user = _regular_user(roles=("data_steward",))
    await install_capability(
        CAPABILITY_ID,
        CapabilityInstallRequest(),
        db=async_db_session,
        current_user=_admin_user(organization_id=current_user.organization_id),
    )
    await install_capability(
        "intelligence_fabric.knowledge_graph",
        CapabilityInstallRequest(),
        db=async_db_session,
        current_user=_admin_user(organization_id=current_user.organization_id),
    )
    await disable_capability(
        "intelligence_fabric.knowledge_graph",
        payload=None,
        organization_id=None,
        db=async_db_session,
        current_user=_admin_user(organization_id=current_user.organization_id),
    )

    response = await get_current_user_capability_context(
        db=async_db_session,
        current_user=current_user,
    )

    data = response.model_dump()
    assert data["current_organization"] == {"id": current_user.organization_id}
    assert data["organization_id"] == current_user.organization_id
    assert data["user_id"] == current_user.id
    assert data["installed_capability_ids"] == [
        "intelligence_fabric.knowledge_graph",
        CAPABILITY_ID,
    ]
    assert data["enabled_capability_ids"] == [CAPABILITY_ID]
    assert data["granted_permissions"] == [
        "research_assets.read",
        "research_assets.register",
        "research_assets.promote_fair",
    ]
    assert data["data_scopes"] == [
        "organization",
        "asset",
        "provenance",
        "license",
        "identifier",
        "connector",
        "evidence",
    ]
    assert data["roles"] == ["data_steward"]

    decisions = {decision["capability_id"]: decision for decision in data["capability_decisions"]}
    assert decisions[CAPABILITY_ID] == {
        "capability_id": CAPABILITY_ID,
        "allowed": True,
        "reason": "allowed",
        "missing_permissions": [],
        "missing_data_scopes": [],
    }
    assert decisions["intelligence_fabric.knowledge_graph"]["allowed"] is False
    assert decisions["intelligence_fabric.knowledge_graph"]["reason"] == "capability_not_installed"


@pytest.mark.asyncio
async def test_current_user_capability_context_http_smoke_for_normal_user(
    async_db_session: AsyncSession,
    test_user: User,
) -> None:
    await install_capability(
        CAPABILITY_ID,
        CapabilityInstallRequest(
            granted_permissions=["research_assets.read"],
            data_scopes=["organization", "asset"],
        ),
        db=async_db_session,
        current_user=_admin_user(organization_id=test_user.organization_id),
    )
    await async_db_session.commit()

    async with _http_client_for_user(test_user) as client:
        response = await client.get("/api/v2/platform/capabilities/me")

    assert response.status_code == 200
    data = response.json()
    for field in [
        "current_organization",
        "organization_id",
        "user_id",
        "installed_capability_ids",
        "enabled_capability_ids",
        "granted_permissions",
        "data_scopes",
        "roles",
        "capability_decisions",
    ]:
        assert field in data

    assert data["current_organization"] == {"id": test_user.organization_id}
    assert data["organization_id"] == test_user.organization_id
    assert data["user_id"] == test_user.id
    assert data["installed_capability_ids"] == [CAPABILITY_ID]
    assert data["enabled_capability_ids"] == [CAPABILITY_ID]
    assert data["granted_permissions"] == ["research_assets.read"]
    assert data["data_scopes"] == ["organization", "asset"]
    assert isinstance(data["roles"], list)
    assert {
        "capability_id": CAPABILITY_ID,
        "allowed": False,
        "reason": "missing_permission",
        "missing_permissions": [
            "research_assets.register",
            "research_assets.promote_fair",
        ],
        "missing_data_scopes": [],
    } in data["capability_decisions"]


@pytest.mark.asyncio
async def test_admin_installation_listing_http_remains_superuser_only(
    test_user: User,
    test_superuser: User,
) -> None:
    async with _http_client_for_user(test_user) as client:
        regular_response = await client.get("/api/v2/system/capabilities/installations")
    assert regular_response.status_code == 403

    async with _http_client_for_user(test_superuser) as client:
        admin_response = await client.get("/api/v2/system/capabilities/installations")

    assert admin_response.status_code == 200
    data = admin_response.json()
    assert data["organization_id"] == test_superuser.organization_id
    assert "installations" in data


@pytest.mark.asyncio
async def test_get_capability_state_is_tenant_scoped(
    async_db_session: AsyncSession,
) -> None:
    current_user = _admin_user()
    other_organization_id = current_user.organization_id + 1000
    await install_capability(
        CAPABILITY_ID,
        CapabilityInstallRequest(organization_id=other_organization_id),
        db=async_db_session,
        current_user=current_user,
    )

    current_org_response = await get_capability_state(
        CAPABILITY_ID,
        organization_id=None,
        db=async_db_session,
        current_user=current_user,
    )
    other_org_response = await get_capability_state(
        CAPABILITY_ID,
        organization_id=other_organization_id,
        db=async_db_session,
        current_user=current_user,
    )

    assert current_org_response.installation is None
    assert other_org_response.installation is not None
    assert other_org_response.installation.organization_id == other_organization_id


@pytest.mark.asyncio
async def test_bootstrap_endpoint_installs_first_wave_capabilities(
    async_db_session: AsyncSession,
) -> None:
    current_user = _admin_user()

    response = await bootstrap_first_wave_capabilities(
        CapabilityBootstrapRequest(),
        db=async_db_session,
        current_user=current_user,
    )

    assert response.organization_id == current_user.organization_id
    assert response.default_capability_ids == (
        "intelligence_fabric.knowledge_graph",
        CAPABILITY_ID,
    )
    assert [receipt.action for receipt in response.receipts] == ["installed", "installed"]

    repeat_response = await bootstrap_first_wave_capabilities(
        CapabilityBootstrapRequest(),
        db=async_db_session,
        current_user=current_user,
    )
    assert {receipt.action for receipt in repeat_response.receipts} == {"already_installed"}


@pytest.mark.asyncio
async def test_bootstrap_endpoint_rejects_unknown_capability(
    async_db_session: AsyncSession,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await bootstrap_first_wave_capabilities(
            CapabilityBootstrapRequest(capability_ids=["unknown.capability"]),
            db=async_db_session,
            current_user=_admin_user(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Unknown capability 'unknown.capability'"


@pytest.mark.asyncio
async def test_disable_endpoint_preserves_installation_row(async_db_session: AsyncSession) -> None:
    current_user = _admin_user()
    await install_capability(
        CAPABILITY_ID,
        CapabilityInstallRequest(),
        db=async_db_session,
        current_user=current_user,
    )

    response = await disable_capability(
        CAPABILITY_ID,
        payload=None,
        organization_id=None,
        db=async_db_session,
        current_user=current_user,
    )

    assert response.installation is not None
    assert response.installation.enabled is False
    assert response.installation.lifecycle_state == "disabled"
    assert response.installation.disabled_by_user_id == current_user.id
    assert response.installation.disabled_at is not None


@pytest.mark.asyncio
async def test_install_endpoint_rejects_unknown_permissions_and_scopes(
    async_db_session: AsyncSession,
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await install_capability(
            CAPABILITY_ID,
            CapabilityInstallRequest(
                granted_permissions=["research_assets.read", "research_assets.delete_everything"],
                data_scopes=["organization"],
            ),
            db=async_db_session,
            current_user=_admin_user(),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["field"] == "granted_permissions"
    assert exc_info.value.detail["unknown"] == ["research_assets.delete_everything"]


@pytest.mark.asyncio
async def test_unknown_capability_returns_not_found(async_db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_capability_state(
            "unknown.capability",
            organization_id=None,
            db=async_db_session,
            current_user=_admin_user(),
        )

    assert exc_info.value.status_code == 404
