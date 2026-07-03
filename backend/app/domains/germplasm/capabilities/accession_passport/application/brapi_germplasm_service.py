"""BrAPI germplasm use-case facade owned by Accession Passport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.germplasm.capabilities.accession_passport.ports import (
    BrAPIGermplasmCreateCommand,
    BrAPIGermplasmDeleteCommand,
    BrAPIGermplasmListQuery,
    BrAPIGermplasmMCPDQuery,
    BrAPIGermplasmPedigreeQuery,
    BrAPIGermplasmProgenyQuery,
    BrAPIGermplasmReadRepository,
    BrAPIGermplasmUpdateCommand,
    BrAPIGermplasmWriteRepository,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import (
    GermplasmBase,
    brapi_germplasm_mcpd_to_payload,
    brapi_germplasm_pedigree_to_payload,
    brapi_germplasm_progeny_to_payload,
    brapi_germplasm_record_to_payload,
    brapi_germplasm_request_to_mutation_data,
)


@dataclass(frozen=True)
class BrAPIGermplasmOperationResult:
    """BrAPI-ready application result without FastAPI or persistence concerns."""

    data: Any
    page: int = 0
    page_size: int = 20
    total: int = 0
    message: str = "Request successful"


@dataclass(frozen=True)
class BrAPIGermplasmApplicationService:
    """Application facade for BrAPI germplasm use cases."""

    read_repository: BrAPIGermplasmReadRepository
    write_repository: BrAPIGermplasmWriteRepository

    async def list_germplasm_for_request(
        self,
        *,
        page: int,
        page_size: int,
        organization_id: int | None = None,
        germplasm_name: str | None = None,
        common_crop_name: str | None = None,
        species: str | None = None,
        genus: str | None = None,
    ) -> BrAPIGermplasmOperationResult:
        return await self.list_germplasm(
            BrAPIGermplasmListQuery(
                page=page,
                page_size=page_size,
                organization_id=organization_id,
                germplasm_name=germplasm_name,
                common_crop_name=common_crop_name,
                species=species,
                genus=genus,
            )
        )

    async def list_germplasm(
        self,
        query: BrAPIGermplasmListQuery,
    ) -> BrAPIGermplasmOperationResult:
        result = await self.read_repository.list_germplasm(query)

        return BrAPIGermplasmOperationResult(
            data=[
                brapi_germplasm_record_to_payload(record)
                for record in result.records
            ],
            page=query.page,
            page_size=query.page_size,
            total=result.total,
        )

    async def get_germplasm_for_request(
        self,
        *,
        germplasm_db_id: str,
        organization_id: int | None = None,
    ) -> BrAPIGermplasmOperationResult | None:
        return await self.get_germplasm(
            germplasm_db_id=germplasm_db_id,
            organization_id=organization_id,
        )

    async def get_germplasm(
        self,
        *,
        germplasm_db_id: str,
        organization_id: int | None = None,
    ) -> BrAPIGermplasmOperationResult | None:
        record = await self.read_repository.get_germplasm(
            germplasm_db_id=germplasm_db_id,
            organization_id=organization_id,
        )
        if record is None:
            return None

        return BrAPIGermplasmOperationResult(
            data=brapi_germplasm_record_to_payload(record),
            total=1,
        )

    async def get_pedigree_for_request(
        self,
        *,
        germplasm_db_id: str,
        organization_id: int | None = None,
        notation: str | None = None,
        include_siblings: bool = False,
    ) -> BrAPIGermplasmOperationResult | None:
        return await self.get_pedigree(
            BrAPIGermplasmPedigreeQuery(
                germplasm_db_id=germplasm_db_id,
                organization_id=organization_id,
                notation=notation,
                include_siblings=include_siblings,
            )
        )

    async def get_pedigree(
        self,
        query: BrAPIGermplasmPedigreeQuery,
    ) -> BrAPIGermplasmOperationResult | None:
        record = await self.read_repository.get_pedigree(query)
        if record is None:
            return None

        return BrAPIGermplasmOperationResult(
            data=brapi_germplasm_pedigree_to_payload(record),
            total=1,
        )

    async def get_progeny_for_request(
        self,
        *,
        germplasm_db_id: str,
        page: int,
        page_size: int,
        organization_id: int | None = None,
    ) -> BrAPIGermplasmOperationResult | None:
        return await self.get_progeny(
            BrAPIGermplasmProgenyQuery(
                germplasm_db_id=germplasm_db_id,
                page=page,
                page_size=page_size,
                organization_id=organization_id,
            )
        )

    async def get_progeny(
        self,
        query: BrAPIGermplasmProgenyQuery,
    ) -> BrAPIGermplasmOperationResult | None:
        result = await self.read_repository.get_progeny(query)
        if result is None:
            return None

        return BrAPIGermplasmOperationResult(
            data=brapi_germplasm_progeny_to_payload(result),
            page=query.page,
            page_size=query.page_size,
            total=result.total,
        )

    async def get_mcpd_for_request(
        self,
        *,
        germplasm_db_id: str,
        organization_id: int | None = None,
    ) -> BrAPIGermplasmOperationResult | None:
        return await self.get_mcpd(
            BrAPIGermplasmMCPDQuery(
                germplasm_db_id=germplasm_db_id,
                organization_id=organization_id,
            )
        )

    async def get_mcpd(
        self,
        query: BrAPIGermplasmMCPDQuery,
    ) -> BrAPIGermplasmOperationResult | None:
        record = await self.read_repository.get_mcpd(query)
        if record is None:
            return None

        return BrAPIGermplasmOperationResult(
            data=brapi_germplasm_mcpd_to_payload(record),
            total=1,
        )

    async def create_germplasm_from_payload(
        self,
        *,
        organization_id: int,
        actor_id: int | None,
        germplasm: GermplasmBase,
    ) -> BrAPIGermplasmOperationResult:
        return await self.create_germplasm(
            BrAPIGermplasmCreateCommand(
                organization_id=organization_id,
                actor_id=actor_id,
                data=brapi_germplasm_request_to_mutation_data(germplasm),
            )
        )

    async def create_germplasm(
        self,
        command: BrAPIGermplasmCreateCommand,
    ) -> BrAPIGermplasmOperationResult:
        record = await self.write_repository.create_germplasm(command)

        return BrAPIGermplasmOperationResult(
            data=brapi_germplasm_record_to_payload(record),
            total=1,
            message="Germplasm created successfully",
        )

    async def update_germplasm_from_payload(
        self,
        *,
        germplasm_db_id: str,
        organization_id: int,
        actor_id: int | None,
        germplasm: GermplasmBase,
    ) -> BrAPIGermplasmOperationResult | None:
        return await self.update_germplasm(
            BrAPIGermplasmUpdateCommand(
                germplasm_db_id=germplasm_db_id,
                organization_id=organization_id,
                actor_id=actor_id,
                data=brapi_germplasm_request_to_mutation_data(germplasm),
            )
        )

    async def update_germplasm(
        self,
        command: BrAPIGermplasmUpdateCommand,
    ) -> BrAPIGermplasmOperationResult | None:
        record = await self.write_repository.update_germplasm(command)
        if record is None:
            return None

        return BrAPIGermplasmOperationResult(
            data=brapi_germplasm_record_to_payload(record),
            total=1,
            message="Germplasm updated successfully",
        )

    async def delete_germplasm_for_request(
        self,
        *,
        germplasm_db_id: str,
        organization_id: int,
        actor_id: int | None,
    ) -> BrAPIGermplasmOperationResult | None:
        return await self.delete_germplasm(
            BrAPIGermplasmDeleteCommand(
                germplasm_db_id=germplasm_db_id,
                organization_id=organization_id,
                actor_id=actor_id,
            )
        )

    async def delete_germplasm(
        self,
        command: BrAPIGermplasmDeleteCommand,
    ) -> BrAPIGermplasmOperationResult | None:
        deleted = await self.write_repository.delete_germplasm(command)
        if not deleted:
            return None

        return BrAPIGermplasmOperationResult(
            data=None,
            total=0,
            message="Germplasm deleted successfully",
        )
