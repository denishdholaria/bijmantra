import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Organization, Program, Study, Trial
from app.models.fair_metadata import FairAssetMetadata
from app.models.germplasm import Germplasm
from app.models.phenotyping import ObservationVariable
from app.schemas.fair_metadata import FAIRAssetMetadataUpsert
from app.services.fair_metadata_service import (
    FairAssetMetadataService,
    FairAssetNotFound,
    InvalidFairPersistentIdentifier,
)


@pytest.fixture(autouse=True)
async def create_fair_metadata_tables(async_db_session: AsyncSession):
    engine = async_db_session.bind
    tables = [
        ObservationVariable.__table__,
        Germplasm.__table__,
        Program.__table__,
        Trial.__table__,
        Study.__table__,
        FairAssetMetadata.__table__,
    ]
    async with engine.begin() as conn:
        for table in tables:
            await conn.run_sync(lambda sync_conn, table=table: table.create(sync_conn, checkfirst=True))
    yield


def _suffix() -> str:
    return uuid.uuid4().hex[:8]


async def _seed_first_wave_assets(db: AsyncSession, organization_id: int) -> dict[str, str]:
    suffix = _suffix()
    variable = ObservationVariable(
        organization_id=organization_id,
        observation_variable_db_id=f"var-fair-{suffix}",
        observation_variable_name="Grain Yield",
    )
    germplasm = Germplasm(
        organization_id=organization_id,
        germplasm_db_id=f"germ-fair-{suffix}",
        germplasm_name="IR64",
    )
    program = Program(
        organization_id=organization_id,
        program_db_id=f"prog-fair-{suffix}",
        program_name="FAIR Program",
    )
    db.add_all([variable, germplasm, program])
    await db.flush()

    trial = Trial(
        organization_id=organization_id,
        program_id=program.id,
        trial_db_id=f"trial-fair-{suffix}",
        trial_name="FAIR Yield Trial",
    )
    db.add(trial)
    await db.flush()

    study = Study(
        organization_id=organization_id,
        trial_id=trial.id,
        study_db_id=f"study-fair-{suffix}",
        study_name="FAIR Yield Study",
    )
    db.add(study)
    await db.flush()

    return {
        "observation_variable": variable.observation_variable_db_id,
        "germplasm": germplasm.germplasm_db_id,
        "trial": trial.trial_db_id,
        "study": study.study_db_id,
    }


async def _create_other_org(db: AsyncSession) -> Organization:
    org = Organization(name=f"Other FAIR Org {_suffix()}")
    db.add(org)
    await db.flush()
    return org


@pytest.mark.asyncio
async def test_upsert_generates_internal_pid_and_persists_fair_fields(
    async_db_session: AsyncSession,
    test_user,
):
    service = FairAssetMetadataService()
    assets = await _seed_first_wave_assets(async_db_session, test_user.organization_id)

    metadata = await service.upsert_asset_metadata(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="observation_variable",
        asset_db_id=assets["observation_variable"],
        payload=FAIRAssetMetadataUpsert(
            keywords=["yield", "rice"],
            access_rights="restricted",
            license="CC-BY-4.0",
            data_standard="BrAPI v2.1",
            ontology_terms=["CO_320:0000001"],
            provenance={"source": "curated"},
            confidence=0.92,
            data_source="BijMantra trait curation",
            contributors=[{"name": "BijMantra"}],
            funding_acknowledgements=["Internal FAIR foundation"],
            external_references=[{"referenceId": "doi:10.123/example"}],
            evidence_refs=[
                {
                    "source_type": "database",
                    "entity_id": assets["observation_variable"],
                    "query_or_method": "fair_metadata_service.upsert_asset_metadata",
                }
            ],
        ),
    )

    assert metadata.persistent_identifier == (
        f"bijmantra:observation_variable:{assets['observation_variable']}"
    )
    assert metadata.organization_id == test_user.organization_id
    assert metadata.title == "Grain Yield"
    assert metadata.keywords == ["yield", "rice"]
    assert metadata.ontology_terms == ["CO_320:0000001"]
    assert metadata.evidence_refs[0]["source_type"] == "database"


@pytest.mark.asyncio
async def test_upsert_rejects_integer_only_persistent_identifier(
    async_db_session: AsyncSession,
    test_user,
):
    service = FairAssetMetadataService()
    assets = await _seed_first_wave_assets(async_db_session, test_user.organization_id)

    with pytest.raises(InvalidFairPersistentIdentifier):
        await service.upsert_asset_metadata(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type="germplasm",
            asset_db_id=assets["germplasm"],
            payload=FAIRAssetMetadataUpsert(persistent_identifier="12345"),
        )


@pytest.mark.asyncio
async def test_service_does_not_attach_metadata_across_organizations(
    async_db_session: AsyncSession,
    test_user,
):
    service = FairAssetMetadataService()
    assets = await _seed_first_wave_assets(async_db_session, test_user.organization_id)
    other_org = await _create_other_org(async_db_session)

    await service.upsert_asset_metadata(
        async_db_session,
        organization_id=test_user.organization_id,
        asset_type="germplasm",
        asset_db_id=assets["germplasm"],
        payload=FAIRAssetMetadataUpsert(license="CC0-1.0"),
    )

    assert (
        await service.get_asset_metadata(
            async_db_session,
            organization_id=other_org.id,
            asset_type="germplasm",
            asset_db_id=assets["germplasm"],
        )
        is None
    )
    with pytest.raises(FairAssetNotFound):
        await service.upsert_asset_metadata(
            async_db_session,
            organization_id=other_org.id,
            asset_type="germplasm",
            asset_db_id=assets["germplasm"],
            payload=FAIRAssetMetadataUpsert(license="CC-BY-4.0"),
        )


@pytest.mark.asyncio
async def test_service_supports_first_wave_fair_asset_types(
    async_db_session: AsyncSession,
    test_user,
):
    service = FairAssetMetadataService()
    assets = await _seed_first_wave_assets(async_db_session, test_user.organization_id)

    for asset_type, asset_db_id in assets.items():
        metadata = await service.upsert_asset_metadata(
            async_db_session,
            organization_id=test_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            payload=FAIRAssetMetadataUpsert(data_standard="BrAPI v2.1"),
        )

        assert metadata.asset_type == asset_type
        assert metadata.asset_db_id == asset_db_id
        assert metadata.persistent_identifier == f"bijmantra:{asset_type}:{asset_db_id}"
