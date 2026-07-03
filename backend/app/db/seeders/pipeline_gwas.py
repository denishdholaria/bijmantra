"""Pipeline GWAS seeder."""

from __future__ import annotations

import logging

from app.db.seeders.base import BaseSeeder, register_seeder
from app.db.seeders.pipeline_base import PipelineSeederMixin


logger = logging.getLogger(__name__)


@register_seeder
class PipelineGWASSeeder(PipelineSeederMixin, BaseSeeder):
    name = "pipeline_gwas"
    description = "GWAS runs and significant marker associations from data_pipeline/output"
    output_filename = "gwas.json"

    def seed(self) -> int:
        from app.modules.bio_analytics.models import GWASResult, GWASRun

        payload = self.load_pipeline_output(default={})
        count = 0
        runs = {}
        for record in payload.get("runs", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = (
                self.db.query(GWASRun)
                .filter(GWASRun.organization_id == org_id, GWASRun.run_name == record["run_name"])
                .first()
            )
            if obj is None:
                obj = GWASRun(organization_id=org_id, run_name=record["run_name"])
                self.db.add(obj)
                count += 1
            obj.trait_name = record["trait_name"]
            obj.method = record["method"]
            obj.sample_size = record.get("sample_size")
            obj.marker_count = record.get("marker_count")
            obj.significance_threshold = record.get("significance_threshold")
            obj.significant_marker_count = record.get("significant_marker_count")
            obj.manhattan_plot_data = record.get("manhattan_plot_data")
            obj.qq_plot_data = record.get("qq_plot_data")
            self.db.flush()
            runs[record["record_key"]] = obj

        for record in payload.get("results", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            run = runs.get(record["run_key"])
            if org_id is None or run is None:
                continue
            obj = (
                self.db.query(GWASResult)
                .filter(
                    GWASResult.organization_id == org_id,
                    GWASResult.run_id == run.id,
                    GWASResult.marker_name == record["marker_name"],
                )
                .first()
            )
            if obj is None:
                obj = GWASResult(organization_id=org_id, run_id=run.id, marker_name=record["marker_name"])
                self.db.add(obj)
                count += 1
            obj.chromosome = record.get("chromosome")
            obj.position = record.get("position")
            obj.p_value = record.get("p_value")
            obj.neg_log10_p = record.get("neg_log10_p")
            obj.effect_size = record.get("effect_size")
            obj.standard_error = record.get("standard_error")
            obj.maf = record.get("maf")
            obj.is_significant = record.get("is_significant", True)
        self.db.commit()
        org1_runs = self.db.query(GWASRun).filter(GWASRun.organization_id == 1).count()
        if org1_runs == 0:
            logger.error("Pipeline GWAS seeder produced no org 1 GWAS runs")
        logger.info("Seeded %s pipeline GWAS records", count)
        return count

    def clear(self) -> int:
        from app.modules.bio_analytics.models import GWASResult, GWASRun

        payload = self.load_pipeline_output(default={})
        cleared = 0
        for record in payload.get("runs", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            run_ids = [
                run_id
                for (run_id,) in self.db.query(GWASRun.id)
                .filter(GWASRun.organization_id == org_id, GWASRun.run_name == record["run_name"])
                .all()
            ]
            if run_ids:
                cleared += (
                    self.db.query(GWASResult)
                    .filter(GWASResult.organization_id == org_id, GWASResult.run_id.in_(run_ids))
                    .delete(synchronize_session=False)
                )
                cleared += (
                    self.db.query(GWASRun)
                    .filter(GWASRun.organization_id == org_id, GWASRun.id.in_(run_ids))
                    .delete(synchronize_session=False)
                )
        self.db.commit()
        return cleared
