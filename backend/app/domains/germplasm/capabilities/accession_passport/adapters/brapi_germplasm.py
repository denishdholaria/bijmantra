"""SQLAlchemy adapters for BrAPI germplasm read/write access."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.germplasm.capabilities.accession_passport.ports import (
    BrAPIGermplasmCreateCommand,
    BrAPIGermplasmDeleteCommand,
    BrAPIGermplasmListQuery,
    BrAPIGermplasmListResult,
    BrAPIGermplasmMCPDQuery,
    BrAPIGermplasmMCPDRecord,
    BrAPIGermplasmMutationData,
    BrAPIGermplasmPedigreeQuery,
    BrAPIGermplasmPedigreeRecord,
    BrAPIGermplasmPedigreeRelation,
    BrAPIGermplasmProgenyQuery,
    BrAPIGermplasmProgenyRecord,
    BrAPIGermplasmProgenyResult,
    BrAPIGermplasmRecord,
    BrAPIGermplasmUpdateCommand,
)
from app.models.germplasm import Cross
from app.models.germplasm import Germplasm as GermplasmModel
from app.modules.germplasm.services.germplasm_service import GermplasmService


def brapi_germplasm_record_from_model(model: GermplasmModel) -> BrAPIGermplasmRecord:
    """Convert a persistence model into a capability-owned BrAPI record."""

    return BrAPIGermplasmRecord(
        germplasm_db_id=model.germplasm_db_id,
        germplasm_name=model.germplasm_name,
        germplasm_pui=model.germplasm_pui,
        default_display_name=model.default_display_name,
        accession_number=model.accession_number,
        species=model.species,
        genus=model.genus,
        subtaxa=model.subtaxa,
        common_crop_name=model.common_crop_name,
        institute_code=model.institute_code,
        institute_name=model.institute_name,
        biological_status_of_accession_code=model.biological_status_of_accession_code,
        country_of_origin_code=model.country_of_origin_code,
        synonyms=tuple(model.synonyms or ()),
        pedigree=model.pedigree,
        seed_source=model.seed_source,
        seed_source_description=model.seed_source_description,
        additional_info=model.additional_info,
        external_references=model.external_references,
    )


class SqlAlchemyBrAPIGermplasmReadAdapter:
    """Persistence adapter for standard BrAPI germplasm read queries."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        germplasm_model: type[GermplasmModel] = GermplasmModel,
    ) -> None:
        self._db = db
        self._germplasm_model = germplasm_model

    async def list_germplasm(
        self,
        query: BrAPIGermplasmListQuery,
    ) -> BrAPIGermplasmListResult:
        stmt = select(self._germplasm_model)
        count_stmt = select(func.count(self._germplasm_model.id))

        stmt, count_stmt = self._apply_list_filters(stmt, count_stmt, query)

        total_result = await self._db.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.offset(query.page * query.page_size).limit(query.page_size)
        result = await self._db.execute(stmt)

        return BrAPIGermplasmListResult(
            records=tuple(
                brapi_germplasm_record_from_model(germplasm)
                for germplasm in result.scalars().all()
            ),
            total=total,
        )

    async def get_germplasm(
        self,
        *,
        germplasm_db_id: str,
        organization_id: int | None = None,
    ) -> BrAPIGermplasmRecord | None:
        stmt = select(self._germplasm_model).where(
            self._germplasm_model.germplasm_db_id == germplasm_db_id
        )
        if organization_id is not None:
            stmt = stmt.where(self._germplasm_model.organization_id == organization_id)

        result = await self._db.execute(stmt)
        germplasm = result.scalar_one_or_none()
        if germplasm is None:
            return None
        return brapi_germplasm_record_from_model(germplasm)

    async def get_pedigree(
        self,
        query: BrAPIGermplasmPedigreeQuery,
    ) -> BrAPIGermplasmPedigreeRecord | None:
        stmt = self._germplasm_lookup_stmt(query.germplasm_db_id, query.organization_id).options(
            selectinload(self._germplasm_model.cross).selectinload(Cross.parent1),
            selectinload(self._germplasm_model.cross).selectinload(Cross.parent2),
            selectinload(self._germplasm_model.cross).selectinload(Cross.crossing_project),
        )
        result = await self._db.execute(stmt)
        germplasm = result.scalar_one_or_none()
        if germplasm is None:
            return None

        parents: list[BrAPIGermplasmPedigreeRelation] = []
        crossing_project_db_id = None
        crossing_year = None

        if germplasm.cross:
            cross = germplasm.cross
            crossing_year = cross.crossing_year
            if cross.crossing_project:
                crossing_project_db_id = cross.crossing_project.crossing_project_db_id
            if cross.parent1:
                parents.append(
                    BrAPIGermplasmPedigreeRelation(
                        germplasm_db_id=cross.parent1.germplasm_db_id,
                        germplasm_name=cross.parent1.germplasm_name,
                        parent_type=cross.parent1_type or "FEMALE",
                    )
                )
            if cross.parent2:
                parents.append(
                    BrAPIGermplasmPedigreeRelation(
                        germplasm_db_id=cross.parent2.germplasm_db_id,
                        germplasm_name=cross.parent2.germplasm_name,
                        parent_type=cross.parent2_type or "MALE",
                    )
                )

        siblings = await self._pedigree_siblings(germplasm, query)
        pedigree = _pedigree_text(germplasm, parents)

        return BrAPIGermplasmPedigreeRecord(
            germplasm_db_id=query.germplasm_db_id,
            germplasm_name=germplasm.germplasm_name,
            pedigree=pedigree,
            crossing_project_db_id=crossing_project_db_id,
            crossing_year=crossing_year,
            family_code=None,
            breeding_method_db_id=germplasm.breeding_method_db_id,
            breeding_method_name=None,
            parents=tuple(parents),
            siblings=tuple(siblings),
        )

    async def get_progeny(
        self,
        query: BrAPIGermplasmProgenyQuery,
    ) -> BrAPIGermplasmProgenyResult | None:
        result = await self._db.execute(
            self._germplasm_lookup_stmt(query.germplasm_db_id, query.organization_id)
        )
        germplasm = result.scalar_one_or_none()
        if germplasm is None:
            return None

        crosses_result = await self._db.execute(
            select(Cross).where(
                (Cross.parent1_db_id == germplasm.id) | (Cross.parent2_db_id == germplasm.id)
            )
        )
        crosses = crosses_result.scalars().all()
        if not crosses:
            return BrAPIGermplasmProgenyResult(
                germplasm_db_id=query.germplasm_db_id,
                germplasm_name=germplasm.germplasm_name,
                progeny=(),
                total=0,
            )

        cross_roles = {}
        for cross in crosses:
            if cross.parent1_db_id == germplasm.id:
                cross_roles[cross.id] = cross.parent1_type
            elif cross.parent2_db_id == germplasm.id:
                cross_roles[cross.id] = cross.parent2_type

        cross_ids = list(cross_roles)
        progeny_stmt = select(self._germplasm_model).where(
            self._germplasm_model.cross_id.in_(cross_ids)
        )
        count_stmt = select(func.count(self._germplasm_model.id)).where(
            self._germplasm_model.cross_id.in_(cross_ids)
        )
        if query.organization_id is not None:
            progeny_stmt = progeny_stmt.where(
                self._germplasm_model.organization_id == query.organization_id
            )
            count_stmt = count_stmt.where(
                self._germplasm_model.organization_id == query.organization_id
            )

        total_result = await self._db.execute(count_stmt)
        total = total_result.scalar() or 0
        progeny_stmt = progeny_stmt.offset(query.page * query.page_size).limit(query.page_size)
        progeny_result = await self._db.execute(progeny_stmt)

        return BrAPIGermplasmProgenyResult(
            germplasm_db_id=query.germplasm_db_id,
            germplasm_name=germplasm.germplasm_name,
            progeny=tuple(
                BrAPIGermplasmProgenyRecord(
                    germplasm_db_id=progeny.germplasm_db_id,
                    germplasm_name=progeny.germplasm_name,
                    parent_type=cross_roles.get(progeny.cross_id, "UNKNOWN"),
                )
                for progeny in progeny_result.scalars().all()
            ),
            total=total,
        )

    async def get_mcpd(
        self,
        query: BrAPIGermplasmMCPDQuery,
    ) -> BrAPIGermplasmMCPDRecord | None:
        result = await self._db.execute(
            self._germplasm_lookup_stmt(query.germplasm_db_id, query.organization_id)
        )
        germplasm = result.scalar_one_or_none()
        if germplasm is None:
            return None
        return _mcpd_record_from_model(germplasm, query.germplasm_db_id)

    def _apply_list_filters(self, stmt, count_stmt, query: BrAPIGermplasmListQuery):
        if query.organization_id is not None:
            stmt = stmt.where(self._germplasm_model.organization_id == query.organization_id)
            count_stmt = count_stmt.where(
                self._germplasm_model.organization_id == query.organization_id
            )

        if query.germplasm_name:
            stmt = stmt.where(
                self._germplasm_model.germplasm_name.ilike(f"%{query.germplasm_name}%")
            )
            count_stmt = count_stmt.where(
                self._germplasm_model.germplasm_name.ilike(f"%{query.germplasm_name}%")
            )
        if query.common_crop_name:
            stmt = stmt.where(
                self._germplasm_model.common_crop_name.ilike(f"%{query.common_crop_name}%")
            )
            count_stmt = count_stmt.where(
                self._germplasm_model.common_crop_name.ilike(f"%{query.common_crop_name}%")
            )
        if query.species:
            stmt = stmt.where(self._germplasm_model.species.ilike(f"%{query.species}%"))
            count_stmt = count_stmt.where(
                self._germplasm_model.species.ilike(f"%{query.species}%")
            )
        if query.genus:
            stmt = stmt.where(self._germplasm_model.genus.ilike(f"%{query.genus}%"))
            count_stmt = count_stmt.where(
                self._germplasm_model.genus.ilike(f"%{query.genus}%")
            )

        return stmt, count_stmt

    def _germplasm_lookup_stmt(
        self,
        germplasm_db_id: str,
        organization_id: int | None,
    ):
        stmt = select(self._germplasm_model).where(
            self._germplasm_model.germplasm_db_id == germplasm_db_id
        )
        if organization_id is not None:
            stmt = stmt.where(self._germplasm_model.organization_id == organization_id)
        return stmt

    async def _pedigree_siblings(
        self,
        germplasm: GermplasmModel,
        query: BrAPIGermplasmPedigreeQuery,
    ) -> list[BrAPIGermplasmPedigreeRelation]:
        if not query.include_siblings or not germplasm.cross_id:
            return []

        stmt = select(self._germplasm_model).where(
            self._germplasm_model.cross_id == germplasm.cross_id,
            self._germplasm_model.id != germplasm.id,
        )
        if query.organization_id is not None:
            stmt = stmt.where(self._germplasm_model.organization_id == query.organization_id)
        result = await self._db.execute(stmt)
        return [
            BrAPIGermplasmPedigreeRelation(
                germplasm_db_id=sibling.germplasm_db_id,
                germplasm_name=sibling.germplasm_name,
            )
            for sibling in result.scalars().all()
        ]


class SqlAlchemyBrAPIGermplasmWriteAdapter:
    """Persistence adapter for standard BrAPI germplasm mutations."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        germplasm_model: type[GermplasmModel] = GermplasmModel,
    ) -> None:
        self._db = db
        self._germplasm_model = germplasm_model

    async def create_germplasm(
        self,
        command: BrAPIGermplasmCreateCommand,
    ) -> BrAPIGermplasmRecord:
        germplasm_db_id = f"germplasm_{uuid.uuid4().hex[:8]}"
        germplasm = self._germplasm_model(
            organization_id=command.organization_id,
            germplasm_db_id=germplasm_db_id,
            **_model_values_from_mutation_data(command.data),
        )

        self._db.add(germplasm)
        await self._db.commit()
        await self._db.refresh(germplasm)
        await GermplasmService.log_mutation(
            self._db,
            command.organization_id,
            command.actor_id,
            "POST",
            germplasm.germplasm_db_id,
            {"germplasmName": command.data.germplasm_name},
        )
        await self._db.commit()
        return brapi_germplasm_record_from_model(germplasm)

    async def update_germplasm(
        self,
        command: BrAPIGermplasmUpdateCommand,
    ) -> BrAPIGermplasmRecord | None:
        stmt = self._tenant_visible_stmt(command.germplasm_db_id, command.organization_id)
        result = await self._db.execute(stmt)
        germplasm = result.scalar_one_or_none()
        if germplasm is None:
            return None

        for field_name, value in _model_values_from_mutation_data(command.data).items():
            setattr(germplasm, field_name, value)

        await self._db.commit()
        await self._db.refresh(germplasm)
        await GermplasmService.log_mutation(
            self._db,
            command.organization_id,
            command.actor_id,
            "PUT",
            germplasm.germplasm_db_id,
            {"germplasmName": command.data.germplasm_name},
        )
        await self._db.commit()
        return brapi_germplasm_record_from_model(germplasm)

    async def delete_germplasm(
        self,
        command: BrAPIGermplasmDeleteCommand,
    ) -> bool:
        stmt = self._tenant_visible_stmt(command.germplasm_db_id, command.organization_id)
        result = await self._db.execute(stmt)
        germplasm = result.scalar_one_or_none()
        if germplasm is None:
            return False

        target_id = germplasm.germplasm_db_id
        await self._db.delete(germplasm)
        await self._db.commit()
        await GermplasmService.log_mutation(
            self._db,
            command.organization_id,
            command.actor_id,
            "DELETE",
            target_id,
            None,
        )
        await self._db.commit()
        return True

    def _tenant_visible_stmt(
        self,
        germplasm_db_id: str,
        organization_id: int,
    ):
        stmt = select(self._germplasm_model).where(
            self._germplasm_model.germplasm_db_id == germplasm_db_id,
            self._germplasm_model.organization_id == organization_id,
        )
        return stmt


def _model_values_from_mutation_data(data: BrAPIGermplasmMutationData) -> dict[str, object]:
    return {
        "germplasm_name": data.germplasm_name,
        "accession_number": data.accession_number,
        "germplasm_pui": data.germplasm_pui,
        "default_display_name": data.default_display_name,
        "species": data.species,
        "genus": data.genus,
        "subtaxa": data.subtaxa,
        "common_crop_name": data.common_crop_name,
        "institute_code": data.institute_code,
        "institute_name": data.institute_name,
        "biological_status_of_accession_code": data.biological_status_of_accession_code,
        "country_of_origin_code": data.country_of_origin_code,
        "synonyms": list(data.synonyms) if data.synonyms is not None else None,
        "pedigree": data.pedigree,
        "seed_source": data.seed_source,
        "seed_source_description": data.seed_source_description,
    }


def _pedigree_text(
    germplasm: GermplasmModel,
    parents: list[BrAPIGermplasmPedigreeRelation],
) -> str:
    if germplasm.pedigree:
        return germplasm.pedigree
    if parents:
        parent_1 = parents[0].germplasm_name if len(parents) > 0 else "Unknown"
        parent_2 = parents[1].germplasm_name if len(parents) > 1 else "Unknown"
        return f"{parent_1}/{parent_2}"
    return f"{germplasm.germplasm_name}/Unknown"


def _mcpd_record_from_model(
    germplasm: GermplasmModel,
    germplasm_db_id: str,
) -> BrAPIGermplasmMCPDRecord:
    return BrAPIGermplasmMCPDRecord(
        germplasm_db_id=germplasm_db_id,
        accession_number=germplasm.accession_number,
        accession_names=(germplasm.germplasm_name,),
        acquisition_date=germplasm.acquisition_date,
        acquisition_source_code=germplasm.acquisition_source_code,
        alternate_ids=(),
        ancestral_data=germplasm.pedigree,
        biological_status_of_accession_code=germplasm.biological_status_of_accession_code,
        breeding_institutes=(),
        collecting_date=germplasm.collection_date,
        collecting_institutes=(),
        collecting_mission_identifier=None,
        collecting_number=None,
        collecting_site=germplasm.collection_site,
        common_crop_name=germplasm.common_crop_name,
        country_of_origin=germplasm.country_of_origin_code,
        donor_accession_number=None,
        donor_accession_pui=None,
        donor_institute=None,
        genus=germplasm.genus,
        germplasm_pui=germplasm.germplasm_pui,
        institute_code=germplasm.institute_code,
        mls_status=None,
        remarks=None,
        safety_duplicate_institutes=(),
        species=germplasm.species,
        species_authority=germplasm.species_authority,
        storage_type_codes=tuple(germplasm.storage_types or ()),
        subtaxon=germplasm.subtaxa,
        subtaxon_authority=germplasm.subtaxa_authority,
    )
