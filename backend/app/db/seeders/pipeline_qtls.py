"""Pipeline QTL and candidate gene seeder."""

from __future__ import annotations

import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.db.seeders.pipeline_base import PipelineSeederMixin, pipeline_info


logger = logging.getLogger(__name__)


@register_seeder
class PipelineQTLSeeder(PipelineSeederMixin, BaseSeeder):
    name = "pipeline_qtls"
    description = "QTL intervals and candidate genes from data_pipeline/output"
    output_filename = "qtls.json"

    def seed(self) -> int:
        from app.modules.bio_analytics.models import BioQTL, CandidateGene

        payload = self.load_pipeline_output(default={})
        count = 0
        qtls = {}
        for record in payload.get("qtls", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = (
                self.db.query(BioQTL)
                .filter(BioQTL.organization_id == org_id, BioQTL.qtl_db_id == record["qtl_db_id"])
                .first()
            )
            if obj is None:
                obj = BioQTL(organization_id=org_id, qtl_db_id=record["qtl_db_id"])
                self.db.add(obj)
                count += 1
            for field in (
                "qtl_name",
                "trait",
                "population",
                "method",
                "chromosome",
                "start_position",
                "end_position",
                "peak_position",
                "lod",
                "lod_score",
                "pve",
                "add_effect",
                "marker_name",
                "confidence_interval_low",
                "confidence_interval_high",
            ):
                setattr(obj, field, record.get(field))
            obj.candidate_genes_json = record.get("candidate_genes")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.flush()
            qtls[record["record_key"]] = obj

        for record in payload.get("candidate_genes", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            qtl = qtls.get(record["qtl_key"])
            if org_id is None or qtl is None:
                continue
            obj = (
                self.db.query(CandidateGene)
                .filter(
                    CandidateGene.organization_id == org_id,
                    CandidateGene.qtl_id == qtl.id,
                    CandidateGene.gene_id == record["gene_id"],
                )
                .first()
            )
            if obj is None:
                obj = CandidateGene(organization_id=org_id, qtl_id=qtl.id, gene_id=record["gene_id"])
                self.db.add(obj)
                count += 1
            for field in (
                "gene_name",
                "chromosome",
                "start_position",
                "end_position",
                "source",
                "description",
                "go_terms",
            ):
                setattr(obj, field, record.get(field))
        self.db.commit()
        org1_qtls = self.db.query(BioQTL).filter(BioQTL.organization_id == 1).count()
        if org1_qtls < 2:
            logger.error("Pipeline QTL seeder produced fewer than 2 org 1 QTL records")
        logger.info("Seeded %s pipeline QTL records", count)
        return count

    def clear(self) -> int:
        from app.modules.bio_analytics.models import BioQTL, CandidateGene

        payload = self.load_pipeline_output(default={})
        cleared = 0
        for record in payload.get("qtls", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            qtl_ids = [
                qtl_id
                for (qtl_id,) in self.db.query(BioQTL.id)
                .filter(BioQTL.organization_id == org_id, BioQTL.qtl_db_id == record["qtl_db_id"])
                .all()
            ]
            if qtl_ids:
                cleared += (
                    self.db.query(CandidateGene)
                    .filter(CandidateGene.organization_id == org_id, CandidateGene.qtl_id.in_(qtl_ids))
                    .delete(synchronize_session=False)
                )
                cleared += (
                    self.db.query(BioQTL)
                    .filter(BioQTL.organization_id == org_id, BioQTL.id.in_(qtl_ids))
                    .delete(synchronize_session=False)
                )
        self.db.commit()
        return cleared
