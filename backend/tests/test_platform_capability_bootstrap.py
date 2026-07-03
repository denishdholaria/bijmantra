import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import OrganizationCapabilityInstallation
from app.platform.capability_bootstrap import (
    FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS,
    bootstrap_capability_installations,
)
from app.platform.capability_installations import (
    UnknownCapability,
    disable_capability_for_organization,
    list_capability_installations,
)


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


@pytest.mark.asyncio
async def test_bootstrap_installs_missing_first_wave_capabilities(
    async_db_session: AsyncSession,
) -> None:
    receipts = await bootstrap_capability_installations(
        async_db_session,
        organization_id=7,
        actor_user_id=42,
    )

    assert [receipt.capability_id for receipt in receipts] == list(
        FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS
    )
    assert {receipt.action for receipt in receipts} == {"installed"}

    installations = await list_capability_installations(async_db_session, organization_id=7)
    assert [installation.capability_id for installation in installations] == sorted(
        FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS
    )
    assert all(installation.enabled for installation in installations)
    assert all(installation.installed_by_user_id == 42 for installation in installations)


@pytest.mark.asyncio
async def test_bootstrap_is_idempotent_for_existing_enabled_rows(
    async_db_session: AsyncSession,
) -> None:
    await bootstrap_capability_installations(
        async_db_session,
        organization_id=7,
        actor_user_id=42,
    )

    receipts = await bootstrap_capability_installations(
        async_db_session,
        organization_id=7,
        actor_user_id=99,
    )

    assert {receipt.action for receipt in receipts} == {"already_installed"}

    installations = await list_capability_installations(async_db_session, organization_id=7)
    assert all(installation.installed_by_user_id == 42 for installation in installations)


@pytest.mark.asyncio
async def test_bootstrap_does_not_reenable_disabled_rows(
    async_db_session: AsyncSession,
) -> None:
    capability_id = FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS[0]
    await bootstrap_capability_installations(
        async_db_session,
        organization_id=7,
        capability_ids=[capability_id],
    )
    await disable_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=capability_id,
        actor_user_id=42,
    )

    receipts = await bootstrap_capability_installations(
        async_db_session,
        organization_id=7,
        capability_ids=[capability_id],
    )

    assert len(receipts) == 1
    assert receipts[0].action == "skipped_disabled"
    assert receipts[0].enabled is False

    installations = await list_capability_installations(async_db_session, organization_id=7)
    assert installations[0].enabled is False
    assert installations[0].disabled_by_user_id == 42


@pytest.mark.asyncio
async def test_bootstrap_rejects_unknown_capabilities_before_partial_install(
    async_db_session: AsyncSession,
) -> None:
    with pytest.raises(UnknownCapability):
        await bootstrap_capability_installations(
            async_db_session,
            organization_id=7,
            capability_ids=[
                FIRST_WAVE_CAPABILITY_BOOTSTRAP_IDS[0],
                "unknown.capability",
            ],
        )

    assert await list_capability_installations(async_db_session, organization_id=7) == []
