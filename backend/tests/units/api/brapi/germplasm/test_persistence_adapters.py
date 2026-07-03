import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.germplasm.capabilities.accession_passport.adapters.brapi_germplasm import (
    SqlAlchemyBrAPIGermplasmReadAdapter,
    SqlAlchemyBrAPIGermplasmWriteAdapter,
    brapi_germplasm_record_from_model,
)
from app.domains.germplasm.capabilities.accession_passport.ports import (
    BrAPIGermplasmCreateCommand,
    BrAPIGermplasmDeleteCommand,
    BrAPIGermplasmListQuery,
    BrAPIGermplasmMCPDQuery,
    BrAPIGermplasmMutationData,
    BrAPIGermplasmPedigreeQuery,
    BrAPIGermplasmPedigreeRelation,
    BrAPIGermplasmProgenyQuery,
    BrAPIGermplasmProgenyRecord,
    BrAPIGermplasmReadRepository,
    BrAPIGermplasmRecord,
    BrAPIGermplasmUpdateCommand,
    BrAPIGermplasmWriteRepository,
)
from app.models.germplasm import Germplasm as GermplasmModel


def test_brapi_germplasm_record_adapter_maps_orm_model_to_port_record():
    model = GermplasmModel(
        id=1,
        germplasm_db_id="g1",
        germplasm_name="IR64",
        germplasm_pui="pui:g1",
        default_display_name="IR64 display",
        accession_number="ACC-1",
        species="sativa",
        genus="Oryza",
        subtaxa="indica",
        common_crop_name="rice",
        institute_code="IRRI",
        institute_name="International Rice Research Institute",
        biological_status_of_accession_code="500",
        country_of_origin_code="PHL",
        synonyms=["IR-64", "IR 64"],
        pedigree="P1/P2",
        seed_source="seed-source",
        seed_source_description="seed-source-description",
        additional_info={"origin": "test"},
        external_references=[{"referenceID": "ref-1"}],
    )

    record = brapi_germplasm_record_from_model(model)

    assert isinstance(record, BrAPIGermplasmRecord)
    assert record.germplasm_db_id == "g1"
    assert record.germplasm_name == "IR64"
    assert record.synonyms == ("IR-64", "IR 64")
    assert record.additional_info == {"origin": "test"}

def test_brapi_germplasm_read_adapter_satisfies_repository_port():
    adapter = SqlAlchemyBrAPIGermplasmReadAdapter(AsyncMock())

    assert isinstance(adapter, BrAPIGermplasmReadRepository)

def test_brapi_germplasm_write_adapter_satisfies_repository_port():
    adapter = SqlAlchemyBrAPIGermplasmWriteAdapter(AsyncMock())

    assert isinstance(adapter, BrAPIGermplasmWriteRepository)

@pytest.mark.asyncio
async def test_brapi_germplasm_read_adapter_lists_with_filters_and_pagination():
    model = GermplasmModel(
        id=1,
        germplasm_db_id="g1",
        germplasm_name="IR64",
        synonyms=[],
        additional_info={},
        external_references=[],
    )
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    data_result = MagicMock()
    data_result.scalars().all.return_value = [model]
    db = AsyncMock()
    db.execute.side_effect = [count_result, data_result]
    adapter = SqlAlchemyBrAPIGermplasmReadAdapter(db)

    result = await adapter.list_germplasm(
        BrAPIGermplasmListQuery(
            page=2,
            page_size=5,
            organization_id=3,
            germplasm_name="IR",
            common_crop_name="rice",
            species="sativa",
            genus="Oryza",
        )
    )

    assert result.total == 1
    assert result.records[0].germplasm_db_id == "g1"
    count_query = str(db.execute.call_args_list[0].args[0])
    data_query = str(db.execute.call_args_list[1].args[0])
    for column_name in (
        "organization_id",
        "germplasm_name",
        "common_crop_name",
        "species",
        "genus",
    ):
        assert column_name in count_query
        assert column_name in data_query
    assert "LIMIT" in data_query.upper()
    assert "OFFSET" in data_query.upper()

@pytest.mark.asyncio
async def test_brapi_germplasm_read_adapter_get_uses_tenant_scope_when_supplied():
    model = GermplasmModel(
        id=1,
        germplasm_db_id="g1",
        germplasm_name="IR64",
        synonyms=[],
        additional_info={},
        external_references=[],
    )
    data_result = MagicMock()
    data_result.scalar_one_or_none.return_value = model
    db = AsyncMock()
    db.execute.return_value = data_result
    adapter = SqlAlchemyBrAPIGermplasmReadAdapter(db)

    record = await adapter.get_germplasm(germplasm_db_id="g1", organization_id=3)

    assert record is not None
    assert record.germplasm_db_id == "g1"
    query = str(db.execute.call_args.args[0])
    assert "germplasm_db_id" in query
    assert "organization_id" in query

@pytest.mark.asyncio
async def test_brapi_germplasm_read_adapter_gets_pedigree_with_siblings():
    parent_1 = SimpleNamespace(germplasm_db_id="p1", germplasm_name="Parent 1")
    parent_2 = SimpleNamespace(germplasm_db_id="p2", germplasm_name="Parent 2")
    cross = SimpleNamespace(
        crossing_year=2026,
        crossing_project=SimpleNamespace(crossing_project_db_id="cp1"),
        parent1=parent_1,
        parent2=parent_2,
        parent1_type=None,
        parent2_type=None,
    )
    germplasm = SimpleNamespace(
        id=10,
        germplasm_db_id="g1",
        germplasm_name="IR64",
        organization_id=3,
        cross=cross,
        cross_id=20,
        pedigree=None,
        breeding_method_db_id="bm1",
    )
    sibling = SimpleNamespace(germplasm_db_id="s1", germplasm_name="Sibling 1")
    germplasm_result = MagicMock()
    germplasm_result.scalar_one_or_none.return_value = germplasm
    sibling_result = MagicMock()
    sibling_result.scalars().all.return_value = [sibling]
    db = AsyncMock()
    db.execute.side_effect = [germplasm_result, sibling_result]
    adapter = SqlAlchemyBrAPIGermplasmReadAdapter(db)

    record = await adapter.get_pedigree(
        BrAPIGermplasmPedigreeQuery(
            germplasm_db_id="g1",
            organization_id=3,
            notation="purdy",
            include_siblings=True,
        )
    )

    assert record is not None
    assert record.pedigree == "Parent 1/Parent 2"
    assert record.crossing_project_db_id == "cp1"
    assert record.crossing_year == 2026
    assert record.breeding_method_db_id == "bm1"
    assert record.parents == (
        BrAPIGermplasmPedigreeRelation("p1", "Parent 1", "FEMALE"),
        BrAPIGermplasmPedigreeRelation("p2", "Parent 2", "MALE"),
    )
    assert record.siblings == (BrAPIGermplasmPedigreeRelation("s1", "Sibling 1"),)
    germplasm_query = str(db.execute.call_args_list[0].args[0])
    sibling_query = str(db.execute.call_args_list[1].args[0])
    assert "germplasm_db_id" in germplasm_query
    assert "organization_id" in germplasm_query
    assert "cross_id" in sibling_query
    assert "organization_id" in sibling_query

@pytest.mark.asyncio
async def test_brapi_germplasm_read_adapter_gets_progeny_with_tenant_scope_and_pagination():
    germplasm = SimpleNamespace(
        id=10,
        germplasm_db_id="g1",
        germplasm_name="IR64",
    )
    cross = SimpleNamespace(id=20, parent1_db_id=10, parent2_db_id=11, parent1_type="FEMALE")
    progeny = SimpleNamespace(
        germplasm_db_id="c1",
        germplasm_name="Child 1",
        cross_id=20,
    )
    germplasm_result = MagicMock()
    germplasm_result.scalar_one_or_none.return_value = germplasm
    crosses_result = MagicMock()
    crosses_result.scalars().all.return_value = [cross]
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    progeny_result = MagicMock()
    progeny_result.scalars().all.return_value = [progeny]
    db = AsyncMock()
    db.execute.side_effect = [
        germplasm_result,
        crosses_result,
        count_result,
        progeny_result,
    ]
    adapter = SqlAlchemyBrAPIGermplasmReadAdapter(db)

    result = await adapter.get_progeny(
        BrAPIGermplasmProgenyQuery(
            germplasm_db_id="g1",
            page=2,
            page_size=5,
            organization_id=3,
        )
    )

    assert result is not None
    assert result.total == 1
    assert result.progeny == (
        BrAPIGermplasmProgenyRecord(
            germplasm_db_id="c1",
            germplasm_name="Child 1",
            parent_type="FEMALE",
        ),
    )
    germplasm_query = str(db.execute.call_args_list[0].args[0])
    count_query = str(db.execute.call_args_list[2].args[0])
    data_query = str(db.execute.call_args_list[3].args[0])
    assert "organization_id" in germplasm_query
    assert "organization_id" in count_query
    assert "organization_id" in data_query
    assert "LIMIT" in data_query.upper()
    assert "OFFSET" in data_query.upper()

@pytest.mark.asyncio
async def test_brapi_germplasm_read_adapter_gets_empty_progeny_when_no_crosses_exist():
    germplasm = SimpleNamespace(
        id=10,
        germplasm_db_id="g1",
        germplasm_name="IR64",
    )
    germplasm_result = MagicMock()
    germplasm_result.scalar_one_or_none.return_value = germplasm
    crosses_result = MagicMock()
    crosses_result.scalars().all.return_value = []
    db = AsyncMock()
    db.execute.side_effect = [germplasm_result, crosses_result]
    adapter = SqlAlchemyBrAPIGermplasmReadAdapter(db)

    result = await adapter.get_progeny(
        BrAPIGermplasmProgenyQuery(
            germplasm_db_id="g1",
            page=0,
            page_size=20,
            organization_id=3,
        )
    )

    assert result is not None
    assert result.total == 0
    assert result.progeny == ()

@pytest.mark.asyncio
async def test_brapi_germplasm_read_adapter_gets_mcpd_record_with_tenant_scope():
    germplasm = SimpleNamespace(
        germplasm_db_id="g1",
        germplasm_name="IR64",
        accession_number="ACC-1",
        acquisition_date="2026-01-01",
        acquisition_source_code="10",
        pedigree="P1/P2",
        biological_status_of_accession_code="500",
        collection_date="2026-01-02",
        collection_site="Los Banos",
        common_crop_name="rice",
        country_of_origin_code="PHL",
        genus="Oryza",
        germplasm_pui="pui:g1",
        institute_code="IRRI",
        species="sativa",
        species_authority="L.",
        storage_types=["10"],
        subtaxa="indica",
        subtaxa_authority="authority",
    )
    db_result = MagicMock()
    db_result.scalar_one_or_none.return_value = germplasm
    db = AsyncMock()
    db.execute.return_value = db_result
    adapter = SqlAlchemyBrAPIGermplasmReadAdapter(db)

    record = await adapter.get_mcpd(
        BrAPIGermplasmMCPDQuery(
            germplasm_db_id="g1",
            organization_id=3,
        )
    )

    assert record is not None
    assert record.germplasm_db_id == "g1"
    assert record.accession_names == ("IR64",)
    assert record.storage_type_codes == ("10",)
    query = str(db.execute.call_args.args[0])
    assert "germplasm_db_id" in query
    assert "organization_id" in query

@pytest.mark.asyncio
async def test_brapi_germplasm_write_adapter_creates_record_and_audit_entry():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    adapter = SqlAlchemyBrAPIGermplasmWriteAdapter(db)

    with patch(
        "app.domains.germplasm.capabilities.accession_passport.adapters.brapi_germplasm.uuid.uuid4"
    ) as mock_uuid:
        mock_uuid.return_value = uuid.UUID("12345678123456781234567812345678")
        record = await adapter.create_germplasm(
            BrAPIGermplasmCreateCommand(
                organization_id=3,
                actor_id=7,
                data=BrAPIGermplasmMutationData(
                    germplasm_name="IR64",
                    accession_number="ACC-1",
                    synonyms=("IR-64",),
                ),
            )
        )

    created_model = db.add.call_args_list[0].args[0]
    assert isinstance(created_model, GermplasmModel)
    assert created_model.organization_id == 3
    assert created_model.germplasm_db_id == "germplasm_12345678"
    assert created_model.germplasm_name == "IR64"
    assert created_model.accession_number == "ACC-1"
    assert created_model.synonyms == ["IR-64"]
    assert db.add.call_count == 2
    assert db.commit.call_count == 2
    db.refresh.assert_awaited_once_with(created_model)
    assert record.germplasm_db_id == "germplasm_12345678"
    assert record.germplasm_name == "IR64"

@pytest.mark.asyncio
async def test_brapi_germplasm_write_adapter_updates_tenant_scoped_record_and_audit_entry():
    existing = GermplasmModel(
        id=1,
        germplasm_db_id="g1",
        germplasm_name="Old",
        accession_number="OLD",
        synonyms=[],
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute.return_value = result
    adapter = SqlAlchemyBrAPIGermplasmWriteAdapter(db)

    record = await adapter.update_germplasm(
        BrAPIGermplasmUpdateCommand(
            germplasm_db_id="g1",
            organization_id=3,
            actor_id=7,
            data=BrAPIGermplasmMutationData(
                germplasm_name="Updated",
                accession_number="ACC-2",
                synonyms=("IR-64", "IR 64"),
            ),
        )
    )

    assert record is not None
    assert record.germplasm_name == "Updated"
    assert existing.germplasm_name == "Updated"
    assert existing.accession_number == "ACC-2"
    assert existing.synonyms == ["IR-64", "IR 64"]
    query = str(db.execute.call_args.args[0])
    assert "germplasm_db_id" in query
    assert "organization_id" in query
    assert db.add.call_count == 1
    assert db.commit.call_count == 2
    db.refresh.assert_awaited_once_with(existing)

@pytest.mark.asyncio
async def test_brapi_germplasm_write_adapter_returns_none_when_update_target_missing():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute.return_value = result
    adapter = SqlAlchemyBrAPIGermplasmWriteAdapter(db)

    record = await adapter.update_germplasm(
        BrAPIGermplasmUpdateCommand(
            germplasm_db_id="missing",
            organization_id=3,
            actor_id=7,
            data=BrAPIGermplasmMutationData(germplasm_name="Missing"),
        )
    )

    assert record is None
    query = str(db.execute.call_args.args[0])
    assert "germplasm_db_id" in query
    assert "organization_id" in query
    db.refresh.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.add.assert_not_called()

@pytest.mark.asyncio
async def test_brapi_germplasm_write_adapter_deletes_tenant_scoped_record_and_audit_entry():
    existing = GermplasmModel(
        id=1,
        germplasm_db_id="g1",
        germplasm_name="IR64",
        synonyms=[],
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing
    db = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    db.execute.return_value = result
    adapter = SqlAlchemyBrAPIGermplasmWriteAdapter(db)

    deleted = await adapter.delete_germplasm(
        BrAPIGermplasmDeleteCommand(
            germplasm_db_id="g1",
            organization_id=3,
            actor_id=7,
        )
    )

    assert deleted is True
    query = str(db.execute.call_args.args[0])
    assert "germplasm_db_id" in query
    assert "organization_id" in query
    db.delete.assert_awaited_once_with(existing)
    assert db.add.call_count == 1
    assert db.commit.call_count == 2

@pytest.mark.asyncio
async def test_brapi_germplasm_write_adapter_returns_false_when_delete_target_missing():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    db.execute.return_value = result
    adapter = SqlAlchemyBrAPIGermplasmWriteAdapter(db)

    deleted = await adapter.delete_germplasm(
        BrAPIGermplasmDeleteCommand(
            germplasm_db_id="missing",
            organization_id=3,
            actor_id=7,
        )
    )

    assert deleted is False
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
    db.add.assert_not_called()
