"""Demo bio analytics seeder.

Seeds deterministic GWAS, QTL, and candidate-gene records for the Demo Organization
so the trusted REEVU genomics path can resolve authoritative local evidence.
"""

import logging

from sqlalchemy import select

from app.core.demo_dataset import DEMO_DATASET_ORG_NAME, demo_dataset_datetime, stable_demo_id
from app.db.seeders.base import BaseSeeder, register_seeder


logger = logging.getLogger(__name__)


DEMO_GWAS_RUNS = [
    {
        "run_key": "rice-blast-association-panel",
        "run_name": "Demo Rice Blast Association Panel",
        "trait_name": "Blast Resistance",
        "method": "MLM",
        "sample_size": 128,
        "marker_count": 5600,
        "significance_threshold": 0.000005,
        "significant_marker_count": 2,
        "manhattan_plot_data": [
            {"chromosome": "6", "position": 17652341, "log_p": 7.82},
            {"chromosome": "12", "position": 10984523, "log_p": 7.05},
        ],
        "qq_plot_data": {
            "expected": [0.3, 0.6, 0.9],
            "observed": [0.35, 0.72, 1.02],
        },
    }
]

DEMO_GWAS_RESULTS = [
    {
        "run_key": "rice-blast-association-panel",
        "marker_name": "Pi9-STS",
        "chromosome": "6",
        "position": 17652341,
        "p_value": 0.0000000151,
        "neg_log10_p": 7.82,
        "effect_size": 0.84,
        "standard_error": 0.12,
        "maf": 0.18,
        "is_significant": True,
    },
    {
        "run_key": "rice-blast-association-panel",
        "marker_name": "Pi-ta-YL155",
        "chromosome": "12",
        "position": 10984523,
        "p_value": 0.000000089,
        "neg_log10_p": 7.05,
        "effect_size": 0.63,
        "standard_error": 0.11,
        "maf": 0.24,
        "is_significant": True,
    },
]

DEMO_QTLS = [
    {
        "qtl_key": "blast-resistance-chr6",
        "qtl_name": "qBLAST6.1",
        "trait": "Blast Resistance",
        "population": "Demo Rice Blast Panel",
        "method": "CIM",
        "chromosome": "6",
        "start_position": 17400000.0,
        "end_position": 17900000.0,
        "peak_position": 17652341.0,
        "lod": 6.8,
        "lod_score": 6.8,
        "pve": 18.4,
        "add_effect": -1.2,
        "dom_effect": -0.3,
        "marker_name": "Pi9-STS",
        "confidence_interval_low": 17500000.0,
        "confidence_interval_high": 17800000.0,
        "candidate_genes": [
            {
                "gene_id": "LOC_Os06g17900",
                "gene_name": "Pi9",
                "chromosome": "6",
                "start_position": 17641000,
                "end_position": 17657500,
                "source": "IRGSP-1.0",
                "description": "Rice blast resistance NLR candidate gene.",
                "go_terms": ["GO:0006952", "GO:0009607"],
            }
        ],
        "additional_info": {
            "crop": "Rice",
            "supporting_run": "Demo Rice Blast Association Panel",
            "supporting_markers": ["Pi9-STS"],
        },
    },
    {
        "qtl_key": "blast-resistance-chr12",
        "qtl_name": "qBLAST12.1",
        "trait": "Blast Resistance",
        "population": "Demo Rice Blast Panel",
        "method": "CIM",
        "chromosome": "12",
        "start_position": 10700000.0,
        "end_position": 11100000.0,
        "peak_position": 10984523.0,
        "lod": 5.9,
        "lod_score": 5.9,
        "pve": 14.1,
        "add_effect": -0.9,
        "dom_effect": -0.2,
        "marker_name": "Pi-ta-YL155",
        "confidence_interval_low": 10820000.0,
        "confidence_interval_high": 11040000.0,
        "candidate_genes": [
            {
                "gene_id": "LOC_Os12g18360",
                "gene_name": "Pi-ta",
                "chromosome": "12",
                "start_position": 10976000,
                "end_position": 10993000,
                "source": "IRGSP-1.0",
                "description": "Rice blast resistance candidate gene near the peak marker.",
                "go_terms": ["GO:0006952", "GO:0043531"],
            }
        ],
        "additional_info": {
            "crop": "Rice",
            "supporting_run": "Demo Rice Blast Association Panel",
            "supporting_markers": ["Pi-ta-YL155"],
        },
    },
]


def _seeded_gwas_run_names() -> list[str]:
    return [run_data["run_name"] for run_data in DEMO_GWAS_RUNS]


def _seeded_qtl_db_ids() -> list[str]:
    return [stable_demo_id("demo_qtl", qtl_data["qtl_key"]) for qtl_data in DEMO_QTLS]


@register_seeder
class DemoBioAnalyticsSeeder(BaseSeeder):
    """Seeds deterministic genomics analytics records for Demo Organization."""

    name = "demo_bio_analytics"
    description = "Demo GWAS, QTL, and candidate-gene records for REEVU genomics evidence"

    def seed(self) -> int:
        from app.models.core import Organization
        from app.models import BioQTL, CandidateGene, GWASResult, GWASRun

        demo_org = self.db.execute(
            select(Organization).where(Organization.name == DEMO_DATASET_ORG_NAME)
        ).scalar_one_or_none()

        if not demo_org:
            logger.warning("Demo Organization not found. Run demo seeders that create it first.")
            return 0

        org_id = demo_org.id
        seeded = 0
        demo_timestamp = demo_dataset_datetime()

        runs_by_name = {
            run.run_name: run
            for run in self.db.query(GWASRun).filter(GWASRun.organization_id == org_id).all()
        }
        run_lookup: dict[str, GWASRun] = {}
        for run_data in DEMO_GWAS_RUNS:
            run = runs_by_name.get(run_data["run_name"])
            if run is None:
                run = GWASRun(
                    organization_id=org_id,
                    run_name=run_data["run_name"],
                    trait_name=run_data["trait_name"],
                    method=run_data["method"],
                )
                self.db.add(run)
                seeded += 1

            run.sample_size = run_data["sample_size"]
            run.marker_count = run_data["marker_count"]
            run.significance_threshold = run_data["significance_threshold"]
            run.significant_marker_count = run_data["significant_marker_count"]
            run.manhattan_plot_data = run_data["manhattan_plot_data"]
            run.qq_plot_data = run_data["qq_plot_data"]
            run.run_date = demo_timestamp

            self.db.flush()
            run_lookup[run_data["run_key"]] = run

        existing_results = {
            (result.run_id, result.marker_name): result
            for result in self.db.query(GWASResult)
            .filter(GWASResult.organization_id == org_id)
            .all()
        }
        for result_data in DEMO_GWAS_RESULTS:
            run = run_lookup[result_data["run_key"]]
            result = existing_results.get((run.id, result_data["marker_name"]))
            if result is None:
                result = GWASResult(
                    organization_id=org_id,
                    run_id=run.id,
                    marker_name=result_data["marker_name"],
                )
                self.db.add(result)
                seeded += 1

            result.chromosome = result_data["chromosome"]
            result.position = result_data["position"]
            result.p_value = result_data["p_value"]
            result.neg_log10_p = result_data["neg_log10_p"]
            result.effect_size = result_data["effect_size"]
            result.standard_error = result_data["standard_error"]
            result.maf = result_data["maf"]
            result.is_significant = result_data["is_significant"]

        qtls_by_db_id = {
            qtl.qtl_db_id: qtl
            for qtl in self.db.query(BioQTL).filter(BioQTL.organization_id == org_id).all()
        }
        for qtl_data in DEMO_QTLS:
            qtl_db_id = stable_demo_id("demo_qtl", qtl_data["qtl_key"])
            qtl = qtls_by_db_id.get(qtl_db_id)
            if qtl is None:
                qtl = BioQTL(
                    organization_id=org_id,
                    qtl_db_id=qtl_db_id,
                    qtl_name=qtl_data["qtl_name"],
                    trait=qtl_data["trait"],
                    chromosome=qtl_data["chromosome"],
                )
                self.db.add(qtl)
                seeded += 1

            qtl.qtl_name = qtl_data["qtl_name"]
            qtl.trait = qtl_data["trait"]
            qtl.population = qtl_data["population"]
            qtl.method = qtl_data["method"]
            qtl.chromosome = qtl_data["chromosome"]
            qtl.start_position = qtl_data["start_position"]
            qtl.end_position = qtl_data["end_position"]
            qtl.peak_position = qtl_data["peak_position"]
            qtl.lod = qtl_data["lod"]
            qtl.lod_score = qtl_data["lod_score"]
            qtl.pve = qtl_data["pve"]
            qtl.add_effect = qtl_data["add_effect"]
            qtl.dom_effect = qtl_data["dom_effect"]
            qtl.marker_name = qtl_data["marker_name"]
            qtl.confidence_interval_low = qtl_data["confidence_interval_low"]
            qtl.confidence_interval_high = qtl_data["confidence_interval_high"]
            qtl.analysis_date = demo_timestamp
            qtl.candidate_genes_json = [
                {
                    "gene_id": candidate["gene_id"],
                    "gene_name": candidate["gene_name"],
                }
                for candidate in qtl_data["candidate_genes"]
            ]
            qtl.additional_info = qtl_data["additional_info"]

            self.db.flush()

            existing_candidates = {
                gene.gene_id: gene
                for gene in self.db.query(CandidateGene)
                .filter(CandidateGene.organization_id == org_id, CandidateGene.qtl_id == qtl.id)
                .all()
            }
            for candidate_data in qtl_data["candidate_genes"]:
                candidate = existing_candidates.get(candidate_data["gene_id"])
                if candidate is None:
                    candidate = CandidateGene(
                        organization_id=org_id,
                        qtl_id=qtl.id,
                        gene_id=candidate_data["gene_id"],
                    )
                    self.db.add(candidate)
                    seeded += 1

                candidate.gene_name = candidate_data["gene_name"]
                candidate.chromosome = candidate_data["chromosome"]
                candidate.start_position = candidate_data["start_position"]
                candidate.end_position = candidate_data["end_position"]
                candidate.source = candidate_data["source"]
                candidate.description = candidate_data["description"]
                candidate.go_terms = candidate_data["go_terms"]

        self.db.commit()
        logger.info("Seeded %s demo bio analytics records", seeded)
        return seeded

    def clear(self) -> int:
        from app.models.core import Organization
        from app.models import BioQTL, CandidateGene, GWASResult, GWASRun

        demo_org = self.db.execute(
            select(Organization).where(Organization.name == DEMO_DATASET_ORG_NAME)
        ).scalar_one_or_none()
        if not demo_org:
            return 0

        org_id = demo_org.id
        cleared = 0
        seeded_run_names = _seeded_gwas_run_names()
        seeded_qtl_db_ids = _seeded_qtl_db_ids()
        seeded_run_ids = [
            run_id
            for (run_id,) in self.db.query(GWASRun.id)
            .filter(
                GWASRun.organization_id == org_id,
                GWASRun.run_name.in_(seeded_run_names),
            )
            .all()
        ]
        seeded_qtl_ids = [
            qtl_id
            for (qtl_id,) in self.db.query(BioQTL.id)
            .filter(
                BioQTL.organization_id == org_id,
                BioQTL.qtl_db_id.in_(seeded_qtl_db_ids),
            )
            .all()
        ]

        if seeded_qtl_ids:
            cleared += (
                self.db.query(CandidateGene)
                .filter(
                    CandidateGene.organization_id == org_id,
                    CandidateGene.qtl_id.in_(seeded_qtl_ids),
                )
                .delete(synchronize_session=False)
            )
        if seeded_run_ids:
            cleared += (
                self.db.query(GWASResult)
                .filter(
                    GWASResult.organization_id == org_id,
                    GWASResult.run_id.in_(seeded_run_ids),
                )
                .delete(synchronize_session=False)
            )
        if seeded_qtl_db_ids:
            cleared += (
                self.db.query(BioQTL)
                .filter(
                    BioQTL.organization_id == org_id,
                    BioQTL.qtl_db_id.in_(seeded_qtl_db_ids),
                )
                .delete(synchronize_session=False)
            )
        if seeded_run_names:
            cleared += (
                self.db.query(GWASRun)
                .filter(
                    GWASRun.organization_id == org_id,
                    GWASRun.run_name.in_(seeded_run_names),
                )
                .delete(synchronize_session=False)
            )
        self.db.commit()
        logger.info("Cleared %s demo bio analytics records", cleared)
        return cleared