"""Pipeline genotyping seeder."""

from __future__ import annotations

import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.db.seeders.pipeline_base import PipelineSeederMixin, pipeline_info


logger = logging.getLogger(__name__)


@register_seeder
class PipelineGenotypingSeeder(PipelineSeederMixin, BaseSeeder):
    name = "pipeline_genotyping"
    description = "Reference, map, and variant records from data_pipeline/output"
    output_filename = "genotyping.json"

    def seed(self) -> int:
        from app.models.genotyping import Call, CallSet, GenomeMap, LinkageGroup, Reference, ReferenceSet, Variant

        payload = self.load_pipeline_output(default={})
        count = 0
        ref_sets = {}
        references = {}
        maps = {}
        variants = {}
        call_sets = {}

        for record in payload.get("reference_sets", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = self._get_or_create(ReferenceSet, org_id, "reference_set_db_id", record["reference_set_db_id"])
            count += int(obj.id is None)
            obj.reference_set_name = record["reference_set_name"]
            obj.description = record.get("description")
            obj.assembly_pui = record.get("assembly_pui")
            obj.species = record.get("species")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.add(obj)
            self.db.flush()
            ref_sets[record["record_key"]] = obj

        for record in payload.get("references", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            ref_set = ref_sets.get(record["reference_set_key"])
            if org_id is None or ref_set is None:
                continue
            obj = self._get_or_create(Reference, org_id, "reference_db_id", record["reference_db_id"])
            count += int(obj.id is None)
            obj.reference_set_id = ref_set.id
            obj.reference_name = record["reference_name"]
            obj.length = record.get("length")
            obj.species = record.get("species")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.add(obj)
            self.db.flush()
            references[record["record_key"]] = obj

        for record in payload.get("genome_maps", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = self._get_or_create(GenomeMap, org_id, "map_db_id", record["map_db_id"])
            count += int(obj.id is None)
            obj.map_name = record["map_name"]
            obj.common_crop_name = record.get("common_crop_name")
            obj.type = record.get("type")
            obj.unit = record.get("unit")
            obj.scientific_name = record.get("scientific_name")
            obj.marker_count = record.get("marker_count")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.add(obj)
            self.db.flush()
            maps[record["record_key"]] = obj

        for record in payload.get("linkage_groups", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            genome_map = maps.get(record["map_key"])
            if org_id is None or genome_map is None:
                continue
            obj = (
                self.db.query(LinkageGroup)
                .filter(
                    LinkageGroup.organization_id == org_id,
                    LinkageGroup.map_id == genome_map.id,
                    LinkageGroup.linkage_group_name == record["linkage_group_name"],
                )
                .first()
            )
            if obj is None:
                obj = LinkageGroup(organization_id=org_id, map_id=genome_map.id, linkage_group_name=record["linkage_group_name"])
                self.db.add(obj)
                count += 1
            obj.max_position = record.get("max_position")
            obj.marker_count = record.get("marker_count")
            obj.additional_info = {"pipeline": pipeline_info(record)}

        for record in payload.get("variants", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            reference = references.get(record["reference_key"])
            if org_id is None or reference is None:
                continue
            obj = self._get_or_create(Variant, org_id, "variant_db_id", record["variant_db_id"])
            count += int(obj.id is None)
            obj.reference_id = reference.id
            obj.variant_name = record["variant_name"]
            obj.variant_type = record.get("variant_type")
            obj.reference_bases = record.get("reference_bases")
            obj.alternate_bases = record.get("alternate_bases")
            obj.start = record.get("start")
            obj.end = record.get("end")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.add(obj)
            self.db.flush()
            variants[record["record_key"]] = obj
        for record in payload.get("call_sets", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = self._get_or_create(CallSet, org_id, "call_set_db_id", record["call_set_db_id"])
            count += int(obj.id is None)
            obj.call_set_name = record["call_set_name"]
            obj.sample_db_id = record.get("sample_db_id")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.add(obj)
            self.db.flush()
            call_sets[record["record_key"]] = obj
        for record in payload.get("calls", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            variant = variants.get(record["variant_key"])
            call_set = call_sets.get(record["call_set_key"])
            if org_id is None or variant is None or call_set is None:
                continue
            obj = self._get_or_create(Call, org_id, "call_db_id", record["call_db_id"])
            count += int(obj.id is None)
            obj.variant_id = variant.id
            obj.call_set_id = call_set.id
            obj.genotype_value = record.get("genotype_value")
            obj.genotype = record.get("genotype")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.add(obj)
        self.db.commit()
        logger.info("Seeded %s pipeline genotyping records", count)
        return count

    def clear(self) -> int:
        from app.models.genotyping import Call, CallSet, GenomeMap, LinkageGroup, Reference, ReferenceSet, Variant

        payload = self.load_pipeline_output(default={})
        cleared = 0
        for record in payload.get("calls", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Call)
                .filter(Call.organization_id == org_id, Call.call_db_id == record["call_db_id"])
                .delete(synchronize_session=False)
            )
        for record in payload.get("call_sets", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(CallSet)
                .filter(CallSet.organization_id == org_id, CallSet.call_set_db_id == record["call_set_db_id"])
                .delete(synchronize_session=False)
            )
        for record in payload.get("variants", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Variant)
                .filter(Variant.organization_id == org_id, Variant.variant_db_id == record["variant_db_id"])
                .delete(synchronize_session=False)
            )
        for record in payload.get("genome_maps", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            map_ids = [
                map_id
                for (map_id,) in self.db.query(GenomeMap.id)
                .filter(GenomeMap.organization_id == org_id, GenomeMap.map_db_id == record["map_db_id"])
                .all()
            ]
            if map_ids:
                cleared += (
                    self.db.query(LinkageGroup)
                    .filter(LinkageGroup.organization_id == org_id, LinkageGroup.map_id.in_(map_ids))
                    .delete(synchronize_session=False)
                )
                cleared += (
                    self.db.query(GenomeMap)
                    .filter(GenomeMap.organization_id == org_id, GenomeMap.id.in_(map_ids))
                    .delete(synchronize_session=False)
                )
        for record in payload.get("references", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Reference)
                .filter(
                    Reference.organization_id == org_id,
                    Reference.reference_db_id == record["reference_db_id"],
                )
                .delete(synchronize_session=False)
            )
        for record in payload.get("reference_sets", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(ReferenceSet)
                .filter(
                    ReferenceSet.organization_id == org_id,
                    ReferenceSet.reference_set_db_id == record["reference_set_db_id"],
                )
                .delete(synchronize_session=False)
            )
        self.db.commit()
        return cleared

    def _get_or_create(self, model, org_id: int, key_field: str, key_value: str):
        existing = (
            self.db.query(model)
            .filter(getattr(model, "organization_id") == org_id, getattr(model, key_field) == key_value)
            .first()
        )
        if existing is not None:
            return existing
        return model(organization_id=org_id, **{key_field: key_value})
