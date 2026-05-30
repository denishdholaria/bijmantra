"""Pipeline germplasm seeder."""

from __future__ import annotations

import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.db.seeders.pipeline_base import PipelineSeederMixin, pipeline_info


logger = logging.getLogger(__name__)


@register_seeder
class PipelineGermplasmSeeder(PipelineSeederMixin, BaseSeeder):
    name = "pipeline_germplasm"
    description = "Real + synthetic germplasm from data_pipeline/output"
    output_filename = "germplasm.json"

    def seed(self) -> int:
        from app.models.germplasm import Germplasm

        records = self.load_pipeline_output(default=[])
        count = 0
        for record in records:
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = (
                self.db.query(Germplasm)
                .filter(Germplasm.organization_id == org_id, Germplasm.germplasm_db_id == record["germplasm_db_id"])
                .first()
            )
            if obj is None:
                obj = Germplasm(organization_id=org_id, germplasm_db_id=record["germplasm_db_id"])
                self.db.add(obj)
                count += 1
            for field in (
                "germplasm_name",
                "default_display_name",
                "accession_number",
                "common_crop_name",
                "genus",
                "species",
                "country_of_origin_code",
                "institute_code",
                "institute_name",
                "biological_status_of_accession_code",
                "pedigree",
            ):
                setattr(obj, field, record.get(field))
            obj.synonyms = record.get("synonyms") or []
            obj.additional_info = {**(record.get("additional_info") or {}), "pipeline": pipeline_info(record)}
        self.db.commit()
        logger.info("Seeded %s pipeline germplasm records", count)
        return count

    def clear(self) -> int:
        from app.models.germplasm import Germplasm

        records = self.load_pipeline_output(default=[])
        cleared = 0
        for record in records:
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Germplasm)
                .filter(
                    Germplasm.organization_id == org_id,
                    Germplasm.germplasm_db_id == record["germplasm_db_id"],
                )
                .delete(synchronize_session=False)
            )
        self.db.commit()
        return cleared
