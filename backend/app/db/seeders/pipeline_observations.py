"""Pipeline observations seeder."""

from __future__ import annotations

import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.db.seeders.pipeline_base import PipelineSeederMixin, pipeline_info


logger = logging.getLogger(__name__)


@register_seeder
class PipelineObservationsSeeder(PipelineSeederMixin, BaseSeeder):
    name = "pipeline_observations"
    description = "Observation units and observations from data_pipeline/output"
    output_filename = "observations.json"

    def seed(self) -> int:
        from app.models.core import Study
        from app.models.germplasm import Germplasm
        from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable

        payload = self.load_pipeline_output(default={})
        count = 0
        unit_lookup = {}

        for record in payload.get("observation_units", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            study = _get_by_tenant_key(self.db, Study, org_id, "study_db_id", _study_db_id(record["study_key"]))
            germplasm = _get_by_tenant_key(self.db, Germplasm, org_id, "germplasm_db_id", _germplasm_db_id(record["germplasm_key"]))
            if study is None or germplasm is None:
                continue
            obj = (
                self.db.query(ObservationUnit)
                .filter(
                    ObservationUnit.organization_id == org_id,
                    ObservationUnit.observation_unit_db_id == record["observation_unit_db_id"],
                )
                .first()
            )
            if obj is None:
                obj = ObservationUnit(
                    organization_id=org_id,
                    observation_unit_db_id=record["observation_unit_db_id"],
                )
                self.db.add(obj)
                count += 1
            obj.study_id = study.id
            obj.germplasm_id = germplasm.id
            obj.observation_unit_name = record["observation_unit_name"]
            obj.observation_level = record.get("observation_level")
            obj.position_coordinate_x = record.get("position_coordinate_x")
            obj.position_coordinate_y = record.get("position_coordinate_y")
            obj.entry_type = record.get("entry_type")
            obj.geo_coordinates = record.get("geo_coordinates")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.flush()
            unit_lookup[record["record_key"]] = obj

        for record in payload.get("observations", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            unit = unit_lookup.get(record["observation_unit_key"])
            variable = _get_by_tenant_key(
                self.db,
                ObservationVariable,
                org_id,
                "observation_variable_db_id",
                _variable_db_id(record["observation_variable_key"]),
            )
            study = _get_by_tenant_key(self.db, Study, org_id, "study_db_id", _study_db_id(record["study_key"]))
            germplasm = _get_by_tenant_key(self.db, Germplasm, org_id, "germplasm_db_id", _germplasm_db_id(record["germplasm_key"]))
            if unit is None or variable is None or study is None or germplasm is None:
                continue
            obj = (
                self.db.query(Observation)
                .filter(
                    Observation.organization_id == org_id,
                    Observation.observation_db_id == record["observation_db_id"],
                )
                .first()
            )
            if obj is None:
                obj = Observation(organization_id=org_id, observation_db_id=record["observation_db_id"])
                self.db.add(obj)
                count += 1
            obj.observation_unit_id = unit.id
            obj.observation_variable_id = variable.id
            obj.study_id = study.id
            obj.germplasm_id = germplasm.id
            obj.collector = record.get("collector")
            obj.observation_time_stamp = record.get("observation_time_stamp")
            obj.value = record.get("value")
            obj.geo_coordinates = record.get("geo_coordinates")
            obj.additional_info = {"pipeline": pipeline_info(record)}
        self.db.commit()
        logger.info("Seeded %s pipeline observation records", count)
        return count

    def clear(self) -> int:
        from app.models.phenotyping import Observation, ObservationUnit

        payload = self.load_pipeline_output(default={})
        cleared = 0
        for record in payload.get("observations", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Observation)
                .filter(
                    Observation.organization_id == org_id,
                    Observation.observation_db_id == record["observation_db_id"],
                )
                .delete(synchronize_session=False)
            )
        for record in payload.get("observation_units", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(ObservationUnit)
                .filter(
                    ObservationUnit.organization_id == org_id,
                    ObservationUnit.observation_unit_db_id == record["observation_unit_db_id"],
                )
                .delete(synchronize_session=False)
            )
        self.db.commit()
        return cleared


def _get_by_tenant_key(db, model, org_id: int, key_field: str, key_value: str):
    return (
        db.query(model)
        .filter(getattr(model, "organization_id") == org_id, getattr(model, key_field) == key_value)
        .first()
    )


def _germplasm_db_id(record_key: str) -> str:
    org, crop, _, index = record_key.split(":")
    return f"pipeline_{org}_{crop}_{index}"


def _study_db_id(record_key: str) -> str:
    org, crop, *_ = record_key.split(":")
    return f"pipeline_{org}_{crop}_study_2025"


def _variable_db_id(record_key: str) -> str:
    org, crop, _, trait_name = record_key.split(":", 3)
    trait_slug = (
        trait_name.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("&", "and")
        .replace("-", "_")
    )
    return f"pipeline_{org}_{crop}_{trait_slug}"
