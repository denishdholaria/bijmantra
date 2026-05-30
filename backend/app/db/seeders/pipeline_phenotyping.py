"""Pipeline phenotyping variable seeder."""

from __future__ import annotations

import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.db.seeders.pipeline_base import PipelineSeederMixin, pipeline_info


logger = logging.getLogger(__name__)


@register_seeder
class PipelinePhenotypingSeeder(PipelineSeederMixin, BaseSeeder):
    name = "pipeline_phenotyping"
    description = "Observation variables from data_pipeline/output"
    output_filename = "phenotyping.json"

    def seed(self) -> int:
        from app.models.phenotyping import ObservationVariable

        payload = self.load_pipeline_output(default={})
        count = 0
        for record in payload.get("observation_variables", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = (
                self.db.query(ObservationVariable)
                .filter(
                    ObservationVariable.organization_id == org_id,
                    ObservationVariable.observation_variable_db_id == record["observation_variable_db_id"],
                )
                .first()
            )
            if obj is None:
                obj = ObservationVariable(
                    organization_id=org_id,
                    observation_variable_db_id=record["observation_variable_db_id"],
                )
                self.db.add(obj)
                count += 1
            for field in (
                "observation_variable_name",
                "common_crop_name",
                "trait_name",
                "trait_description",
                "trait_class",
                "method_name",
                "scale_name",
                "data_type",
                "valid_values",
                "ontology_db_id",
                "ontology_name",
                "status",
            ):
                setattr(obj, field, record.get(field))
            obj.additional_info = {"pipeline": pipeline_info(record)}
        self.db.commit()
        logger.info("Seeded %s pipeline observation variables", count)
        return count

    def clear(self) -> int:
        from app.models.phenotyping import ObservationVariable

        payload = self.load_pipeline_output(default={})
        cleared = 0
        for record in payload.get("observation_variables", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(ObservationVariable)
                .filter(
                    ObservationVariable.organization_id == org_id,
                    ObservationVariable.observation_variable_db_id
                    == record["observation_variable_db_id"],
                )
                .delete(synchronize_session=False)
            )
        self.db.commit()
        return cleared
