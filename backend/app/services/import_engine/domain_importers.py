from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Location, Program, Trial
from app.models.germplasm import Germplasm
from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable
from app.services.import_engine.base import BaseImporter


class GermplasmImporter(BaseImporter):
    model = Germplasm
    required_fields = {"germplasm_name"}
    allowed_fields = {
        "germplasm_name", "accession_number", "genus", "species", "common_crop_name",
        "pedigree", "country_of_origin_code", "organization_id",
    }

    @property
    def domain(self) -> str:
        return "germplasm"

    async def resolve_foreign_keys(self, row: dict[str, object]) -> dict[str, object]:
        row["organization_id"] = self.organization_id
        return row


class TrialImporter(BaseImporter):
    model = Trial
    required_fields = {"trial_name", "program_name"}
    allowed_fields = {
        "trial_name", "trial_description", "trial_type", "start_date", "end_date",
        "common_crop_name", "program_id", "location_id", "organization_id", "program_name", "location_name",
    }

    @property
    def domain(self) -> str:
        return "trial"

    async def resolve_foreign_keys(self, row: dict[str, object]) -> dict[str, object]:
        program_name = row.pop("program_name", None)
        location_name = row.pop("location_name", None)

        if program_name:
            p = await self.db.execute(select(Program.id).where(
                Program.organization_id == self.organization_id,
                Program.program_name == str(program_name),
            ))
            row["program_id"] = p.scalar_one_or_none()
        if location_name:
            l = await self.db.execute(select(Location.id).where(
                Location.organization_id == self.organization_id,
                Location.location_name == str(location_name),
            ))
            row["location_id"] = l.scalar_one_or_none()

        row["organization_id"] = self.organization_id
        return row


class ObservationImporter(BaseImporter):
    model = Observation
    required_fields = {"trait", "observation_unit_name", "value"}
    allowed_fields = {
        "trait", "observation_unit_name", "value", "date", "observation_variable_id",
        "observation_unit_id", "study_id", "germplasm_id", "organization_id", "observation_time_stamp",
    }

    @property
    def domain(self) -> str:
        return "observation"

    async def resolve_foreign_keys(self, row: dict[str, object]) -> dict[str, object]:
        trait_name = row.pop("trait", None)
        unit_name = row.pop("observation_unit_name", None)

        trait_id = None
        unit = None

        if trait_name:
            t = await self.db.execute(select(ObservationVariable.id).where(
                ObservationVariable.organization_id == self.organization_id,
                ObservationVariable.observation_variable_name == str(trait_name),
            ))
            trait_id = t.scalar_one_or_none()

        if unit_name:
            u = await self.db.execute(select(
                ObservationUnit.id,
                ObservationUnit.study_id,
                ObservationUnit.germplasm_id,
            ).where(
                ObservationUnit.organization_id == self.organization_id,
                ObservationUnit.observation_unit_name == str(unit_name),
            ))
            unit = u.first()

        if trait_id and unit:
            row["observation_variable_id"] = trait_id
            row["observation_unit_id"] = unit.id
            row["study_id"] = unit.study_id
            row["germplasm_id"] = unit.germplasm_id

        if "date" in row and "observation_time_stamp" not in row:
            row["observation_time_stamp"] = row.pop("date")

        row["value"] = str(row.get("value", ""))
        row["organization_id"] = self.organization_id
        return row
