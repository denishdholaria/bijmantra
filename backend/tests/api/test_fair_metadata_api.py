import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.knowledge.capabilities.research_asset_core.adapters.api.fair_metadata import (
    get_fair_metadata,
    list_fair_metadata,
    upsert_fair_metadata,
)
from app.models.fair_metadata import FairAssetMetadata
from app.models.germplasm import Germplasm
from app.schemas.fair_metadata import FAIRAssetMetadataUpsert


@pytest.fixture(autouse=True)
async def create_fair_metadata_api_tables(async_db_session: AsyncSession):
    engine = async_db_session.bind
    tables = [Germplasm.__table__, FairAssetMetadata.__table__]
    async with engine.begin() as conn:
        for table in tables:
            await conn.run_sync(lambda sync_conn, table=table: table.create(sync_conn, checkfirst=True))
    yield


def _current_user(test_user):
    return SimpleNamespace(organization_id=test_user.organization_id)


@pytest.mark.asyncio
async def test_fair_metadata_api_upsert_get_and_list_shape(
    async_db_session: AsyncSession,
    test_user,
):
    suffix = uuid.uuid4().hex[:8]
    germplasm = Germplasm(
        organization_id=test_user.organization_id,
        germplasm_db_id=f"germ-api-fair-{suffix}",
        germplasm_name="Swarna",
    )
    async_db_session.add(germplasm)
    await async_db_session.flush()

    created = await upsert_fair_metadata(
        asset_type="germplasm",
        asset_db_id=germplasm.germplasm_db_id,
        payload=FAIRAssetMetadataUpsert(
            access_rights="controlled",
            license="CC-BY-4.0",
            data_standard="MCPD",
            keywords=["rice", "accession"],
        ),
        db=async_db_session,
        current_user=_current_user(test_user),
    )

    assert created.asset_type == "germplasm"
    assert created.asset_db_id == germplasm.germplasm_db_id
    assert created.persistent_identifier == f"bijmantra:germplasm:{germplasm.germplasm_db_id}"
    assert created.title == "Swarna"

    fetched = await get_fair_metadata(
        asset_type="germplasm",
        asset_db_id=germplasm.germplasm_db_id,
        db=async_db_session,
        current_user=_current_user(test_user),
    )
    assert fetched.id == created.id
    assert fetched.keywords == ["rice", "accession"]

    listed = await list_fair_metadata(
        asset_type="germplasm",
        limit=20,
        offset=0,
        db=async_db_session,
        current_user=_current_user(test_user),
    )
    assert any(item.id == created.id for item in listed)
