from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.brapi.v2.germplasm import GermplasmCreate
from app.domains.germplasm.capabilities.accession_passport.application import (
    BrAPIGermplasmApplicationService,
    BrAPIGermplasmOperationResult,
)
from app.domains.germplasm.capabilities.accession_passport.ports import (
    BrAPIGermplasmCreateCommand,
    BrAPIGermplasmDeleteCommand,
    BrAPIGermplasmListQuery,
    BrAPIGermplasmMutationData,
    BrAPIGermplasmRecord,
    BrAPIGermplasmUpdateCommand,
)


@pytest.mark.asyncio
async def test_brapi_germplasm_application_service_delegates_through_ports():
    read_repository = AsyncMock()
    write_repository = AsyncMock()
    listed_record = BrAPIGermplasmRecord("g1", "IR64")
    list_result = SimpleNamespace(records=(listed_record,), total=1)
    created_record = BrAPIGermplasmRecord("g1", "IR64")
    read_repository.list_germplasm.return_value = list_result
    write_repository.create_germplasm.return_value = created_record
    service = BrAPIGermplasmApplicationService(
        read_repository=read_repository,
        write_repository=write_repository,
    )
    list_query = BrAPIGermplasmListQuery(page=0, page_size=20, organization_id=3)
    create_command = BrAPIGermplasmCreateCommand(
        organization_id=3,
        actor_id=7,
        data=BrAPIGermplasmMutationData(germplasm_name="IR64"),
    )

    listed = await service.list_germplasm(list_query)
    created = await service.create_germplasm(create_command)

    assert isinstance(listed, BrAPIGermplasmOperationResult)
    assert listed.data == [
        {
            "germplasmDbId": "g1",
            "germplasmName": "IR64",
            "germplasmPUI": None,
            "defaultDisplayName": "IR64",
            "accessionNumber": None,
            "species": None,
            "genus": None,
            "subtaxa": None,
            "commonCropName": None,
            "instituteCode": None,
            "instituteName": None,
            "biologicalStatusOfAccessionCode": None,
            "countryOfOriginCode": None,
            "synonyms": [],
            "pedigree": None,
            "seedSource": None,
            "seedSourceDescription": None,
            "additionalInfo": None,
            "externalReferences": None,
        }
    ]
    assert listed.page == 0
    assert listed.page_size == 20
    assert listed.total == 1
    assert created.data["germplasmDbId"] == "g1"
    assert created.total == 1
    assert created.message == "Germplasm created successfully"
    read_repository.list_germplasm.assert_awaited_once_with(list_query)
    write_repository.create_germplasm.assert_awaited_once_with(create_command)

@pytest.mark.asyncio
async def test_brapi_germplasm_application_service_builds_request_commands_and_queries():
    read_repository = AsyncMock()
    write_repository = AsyncMock()
    read_repository.list_germplasm.return_value = SimpleNamespace(
        records=(BrAPIGermplasmRecord("g1", "IR64"),),
        total=1,
    )
    write_repository.create_germplasm.return_value = BrAPIGermplasmRecord("g2", "Swarna")
    write_repository.update_germplasm.return_value = BrAPIGermplasmRecord("g1", "IR64 Updated")
    write_repository.delete_germplasm.return_value = True
    service = BrAPIGermplasmApplicationService(
        read_repository=read_repository,
        write_repository=write_repository,
    )

    await service.list_germplasm_for_request(
        page=2,
        page_size=5,
        organization_id=3,
        germplasm_name="IR",
        common_crop_name="rice",
        species="sativa",
        genus="Oryza",
    )
    await service.create_germplasm_from_payload(
        organization_id=3,
        actor_id=7,
        germplasm=GermplasmCreate(
            germplasmName="Swarna",
            accessionNumber="ACC-2",
            synonyms=["Swarna-1"],
        ),
    )
    await service.update_germplasm_from_payload(
        germplasm_db_id="g1",
        organization_id=3,
        actor_id=7,
        germplasm=GermplasmCreate(germplasmName="IR64 Updated"),
    )
    deleted = await service.delete_germplasm_for_request(
        germplasm_db_id="g1",
        organization_id=3,
        actor_id=7,
    )

    read_repository.list_germplasm.assert_awaited_once_with(
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
    write_repository.create_germplasm.assert_awaited_once_with(
        BrAPIGermplasmCreateCommand(
            organization_id=3,
            actor_id=7,
            data=BrAPIGermplasmMutationData(
                germplasm_name="Swarna",
                accession_number="ACC-2",
                synonyms=("Swarna-1",),
            ),
        )
    )
    write_repository.update_germplasm.assert_awaited_once_with(
        BrAPIGermplasmUpdateCommand(
            germplasm_db_id="g1",
            organization_id=3,
            actor_id=7,
            data=BrAPIGermplasmMutationData(
                germplasm_name="IR64 Updated",
                synonyms=(),
            ),
        )
    )
    write_repository.delete_germplasm.assert_awaited_once_with(
        BrAPIGermplasmDeleteCommand(
            germplasm_db_id="g1",
            organization_id=3,
            actor_id=7,
        )
    )
    assert deleted is not None
    assert deleted.message == "Germplasm deleted successfully"
