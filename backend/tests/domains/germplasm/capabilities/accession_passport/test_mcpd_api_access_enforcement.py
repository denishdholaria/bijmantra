from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.germplasm.capabilities.accession_passport.adapters.api.mcpd import (
    export_accessions_mcpd_csv,
    get_mcpd_template,
    import_accessions_mcpd,
)
from app.platform.capability_installations import (
    disable_capability_for_organization,
    install_capability_for_organization,
)


ACCESSION_PASSPORT_CAPABILITY_ID = "germplasm_global_seed_registry.accession_passport"


def _actor(
    *,
    installed_capabilities: tuple[str, ...] = (ACCESSION_PASSPORT_CAPABILITY_ID,),
    permissions: tuple[str, ...] = (
        "germplasm.read",
        "germplasm.passport.manage",
    ),
    data_scopes: tuple[str, ...] = (
        "organization",
        "collection",
        "accession",
        "material_transfer",
    ),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=42,
        organization_id=7,
        installed_capabilities=installed_capabilities,
        permissions=permissions,
        data_scopes=data_scopes,
        roles=("germplasm_curator",),
    )


@pytest.mark.asyncio
async def test_mcpd_api_rejects_uninstalled_capability_before_data_access() -> None:
    with pytest.raises(HTTPException) as error:
        await export_accessions_mcpd_csv(
            inst_code="BIJ001",
            db=object(),
            current_user=_actor(installed_capabilities=()),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "capability_not_installed"
    assert error.value.detail["capabilityId"] == ACCESSION_PASSPORT_CAPABILITY_ID


@pytest.mark.asyncio
async def test_mcpd_api_rejects_missing_import_permission_before_file_read() -> None:
    class NoAuditDb:
        def add(self, record) -> None:
            raise AssertionError("audit should not be written before access is allowed")

    class UnreadableUpload:
        async def read(self) -> bytes:
            raise AssertionError("file should not be read before access is allowed")

    with pytest.raises(HTTPException) as error:
        await import_accessions_mcpd(
            file=UnreadableUpload(),
            skip_duplicates=True,
            validate_only=False,
            db=NoAuditDb(),
            current_user=_actor(permissions=("germplasm.read",)),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "missing_permission"
    assert error.value.detail["missingPermissions"] == ["germplasm.passport.manage"]


@pytest.mark.asyncio
async def test_mcpd_api_rejects_missing_data_scope_before_reference_payload() -> None:
    with pytest.raises(HTTPException) as error:
        await get_mcpd_template(
            db=object(),
            current_user=_actor(data_scopes=("organization",)),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "missing_data_scope"
    assert error.value.detail["missingDataScopes"] == ["accession"]


@pytest.mark.asyncio
async def test_mcpd_api_uses_disabled_persisted_install_state(
    async_db_session: AsyncSession,
) -> None:
    await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=ACCESSION_PASSPORT_CAPABILITY_ID,
    )
    await disable_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=ACCESSION_PASSPORT_CAPABILITY_ID,
    )

    with pytest.raises(HTTPException) as error:
        await get_mcpd_template(
            db=async_db_session,
            current_user=_actor(),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "capability_not_installed"


@pytest.mark.asyncio
async def test_mcpd_api_uses_persisted_permission_grants_before_file_read(
    async_db_session: AsyncSession,
) -> None:
    class UnreadableUpload:
        async def read(self) -> bytes:
            raise AssertionError("file should not be read before access is allowed")

    await install_capability_for_organization(
        async_db_session,
        organization_id=7,
        capability_id=ACCESSION_PASSPORT_CAPABILITY_ID,
        granted_permissions=("germplasm.read",),
    )

    with pytest.raises(HTTPException) as error:
        await import_accessions_mcpd(
            file=UnreadableUpload(),
            skip_duplicates=True,
            validate_only=False,
            db=async_db_session,
            current_user=_actor(),
        )

    assert error.value.status_code == 403
    assert error.value.detail["reason"] == "missing_permission"
    assert error.value.detail["missingPermissions"] == ["germplasm.passport.manage"]
