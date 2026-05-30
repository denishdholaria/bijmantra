"""
Org 1 Benchmark Data Seeder

Populates org 1 with observations, GWAS runs, and QTL records so the REEVU
real-question benchmark can progress from 3/14 toward 14/14.

Design principles:
- Idempotent: safe to run multiple times (check-before-create)
- Tenant-isolated: only creates records for org 1, never touches org 2
- Deterministic: uses stable_demo_id() with org1_bench_ prefix
- Realistic: agronomically valid values for rice/wheat traits

Run via:
    cd backend && uv run python -m app.db.seed --only=org1_benchmark
"""

import logging

from sqlalchemy import select

from app.core.demo_dataset import demo_dataset_datetime, stable_demo_float, stable_demo_id
from app.db.seeders.base import BaseSeeder, register_seeder

logger = logging.getLogger(__name__)

# ── Data Constants ────────────────────────────────────────────────────────────

ORG1_TRAITS: dict[str, dict] = {
    "Grain Yield": {
        "min": 3500.0, "max": 7500.0, "unit": "kg/ha",
        "trait_class": "Agronomic",
        "method": "Combine Harvester",
        "scale": "Continuous",
        "ontology_ref": "CO_321:0001218",
    },
    "Plant Height": {
        "min": 65.0, "max": 130.0, "unit": "cm",
        "trait_class": "Morphological",
        "method": "Ruler Measurement",
        "scale": "Continuous",
        "ontology_ref": "CO_321:0000994",
    },
    "Blast Resistance": {
        "min": 1.0, "max": 9.0, "unit": "1-9 scale",
        "trait_class": "Biotic Stress",
        "method": "Visual Scoring",
        "scale": "Ordinal",
        "ontology_ref": "CO_321:0000175",
    },
    "Days to Flowering": {
        "min": 75.0, "max": 120.0, "unit": "days",
        "trait_class": "Phenological",
        "method": "Field Observation",
        "scale": "Continuous",
        "ontology_ref": "CO_321:0000183",
    },
}

ORG1_GWAS_RUNS: list[dict] = [
    {
        "run_key": "org1-grain-yield-gwas-2024",
        "run_name": "Org1 Grain Yield GWAS 2024",
        "trait_name": "Grain Yield",
        "method": "MLM",
        "sample_size": 96,
        "marker_count": 4800,
        "significance_threshold": 0.000005,
        "significant_marker_count": 3,
        "manhattan_plot_data": [
            {"chromosome": "1", "position": 32145678, "log_p": 7.21},
            {"chromosome": "3", "position": 18765432, "log_p": 6.85},
            {"chromosome": "8", "position": 9876543, "log_p": 6.42},
        ],
        "qq_plot_data": {
            "expected": [0.3, 0.6, 0.9, 1.2],
            "observed": [0.32, 0.65, 0.98, 1.35],
        },
    }
]

ORG1_GWAS_RESULTS: list[dict] = [
    {
        "run_key": "org1-grain-yield-gwas-2024",
        "marker_name": "GY-QTL1-RM1",
        "chromosome": "1",
        "position": 32145678,
        "p_value": 0.0000000062,
        "neg_log10_p": 7.21,
        "effect_size": 0.72,
        "standard_error": 0.10,
        "maf": 0.22,
        "is_significant": True,
    },
    {
        "run_key": "org1-grain-yield-gwas-2024",
        "marker_name": "GY-QTL3-RM3",
        "chromosome": "3",
        "position": 18765432,
        "p_value": 0.000000014,
        "neg_log10_p": 6.85,
        "effect_size": 0.58,
        "standard_error": 0.09,
        "maf": 0.31,
        "is_significant": True,
    },
    {
        "run_key": "org1-grain-yield-gwas-2024",
        "marker_name": "GY-QTL8-RM8",
        "chromosome": "8",
        "position": 9876543,
        "p_value": 0.000000038,
        "neg_log10_p": 6.42,
        "effect_size": 0.44,
        "standard_error": 0.08,
        "maf": 0.18,
        "is_significant": True,
    },
]

ORG1_QTLS: list[dict] = [
    {
        "qtl_key": "org1-yield-qtl-chr1",
        "qtl_name": "qGY1.1",
        "trait": "Grain Yield",
        "population": "Org1 Rice Mapping Population",
        "method": "CIM",
        "chromosome": "1",
        "start_position": 31800000.0,
        "end_position": 32500000.0,
        "peak_position": 32145678.0,
        "lod": 7.2,
        "lod_score": 7.2,
        "pve": 14.8,
        "add_effect": 0.38,
        "confidence_interval_low": 31900000.0,
        "confidence_interval_high": 32400000.0,
        "candidate_genes": [
            {
                "gene_id": "LOC_Os01g56510",
                "gene_name": "OsGW5",
                "chromosome": "1",
                "start_position": 32100000,
                "end_position": 32200000,
                "annotation": "Grain width and weight regulator",
            }
        ],
    },
    {
        "qtl_key": "org1-blast-qtl-chr6",
        "qtl_name": "qBR6.1",
        "trait": "Blast Resistance",
        "population": "Org1 Rice Mapping Population",
        "method": "CIM",
        "chromosome": "6",
        "start_position": 17400000.0,
        "end_position": 17900000.0,
        "peak_position": 17652341.0,
        "lod": 6.8,
        "lod_score": 6.8,
        "pve": 18.4,
        "add_effect": -1.2,
        "confidence_interval_low": 17500000.0,
        "confidence_interval_high": 17800000.0,
        "candidate_genes": [
            {
                "gene_id": "LOC_Os06g45810",
                "gene_name": "Pi9",
                "chromosome": "6",
                "start_position": 17600000,
                "end_position": 17700000,
                "annotation": "NBS-LRR blast resistance gene",
            }
        ],
    },
]

ORG1_SPEED_BREEDING_PROTOCOLS: list[dict] = [
    {
        "name": "Org1 Benchmark Rice Speed Breeding Protocol",
        "description": "Benchmark-aligned accelerated generation protocol for rice blast-resistance improvement.",
        "crop": "rice",
        "photoperiod": 22,
        "temperature_day": 28.0,
        "temperature_night": 22.0,
        "humidity": 70.0,
        "light_intensity": 450.0,
        "days_to_flower": 35,
        "days_to_harvest": 82,
        "generations_per_year": 4.0,
        "success_rate": 0.92,
        "status": "active",
    }
]

# Minimum germplasm entries to create if org 1 has fewer than needed
_MIN_GERMPLASM = 5
_MIN_TRIALS = 3


@register_seeder
class Org1BenchmarkSeeder(BaseSeeder):
    """Seed benchmark-aligned observations, GWAS, and QTL data for org 1.

    Idempotent — safe to run multiple times. Only touches org 1.
    Uses org1_bench_ prefix for all stable IDs.
    """

    name = "org1_benchmark"
    description = (
        "Benchmark-aligned observations, GWAS, and QTL data for org 1 "
        "to improve REEVU real-question benchmark from 3/14 toward 14/14"
    )
    is_demo_data = False  # system scope — not demo data, targets org 1 directly

    def should_run(self, env: str = "dev") -> bool:
        """Run in any non-production environment regardless of SEED_DEMO_DATA."""
        from app.core.demo_dataset import is_production_environment
        return not is_production_environment(env)

    def seed(self) -> int:
        """Seed all benchmark data for org 1. Returns count of records created/updated."""
        from app.models.core import Organization

        # 1. Resolve org 1
        org = self.db.query(Organization).filter(Organization.id == 1).first()
        if org is None:
            logger.warning("Org1BenchmarkSeeder: org 1 not found — skipping")
            return 0

        org_id = org.id
        logger.info("Org1BenchmarkSeeder: seeding for org_id=%s (%s)", org_id, org.name)

        count = 0

        # 2. Discover or create trials, studies, germplasm
        trials, studies, germplasm_list = self._ensure_minimum_records(org_id)
        if not trials or not germplasm_list:
            logger.warning("Org1BenchmarkSeeder: insufficient trials or germplasm — aborting")
            return 0

        # 3. Seed observation variables
        obs_vars, new_vars = self._seed_observation_variables(org_id)
        count += new_vars

        # 4. Seed observation units
        obs_units, new_units = self._seed_observation_units(org_id, trials, studies, germplasm_list)
        count += new_units

        # 5. Seed observations
        count += self._seed_observations(org_id, obs_units, obs_vars)

        # 6. Seed GWAS runs + results
        count += self._seed_gwas(org_id)

        # 7. Seed QTLs + candidate genes
        count += self._seed_qtls(org_id)

        # 8. Seed speed-breeding protocol evidence for protocol recommendation benchmark cases
        count += self._seed_speed_breeding_protocols(org_id)

        self.db.commit()
        logger.info("Org1BenchmarkSeeder: seeded %d records for org 1", count)
        return count

    def clear(self) -> int:
        """Remove only org1_bench-prefixed records from org 1. Returns count cleared."""
        count = 0
        try:
            count += self._clear_candidate_genes()
            count += self._clear_gwas_results()
            count += self._clear_qtls()
            count += self._clear_gwas_runs()
            count += self._clear_observations()
            count += self._clear_observation_units()
            count += self._clear_observation_variables()
            count += self._clear_speed_breeding_protocols()
            self.db.commit()
        except Exception as exc:
            logger.error("Org1BenchmarkSeeder.clear() failed: %s", exc)
            self.db.rollback()
        return count

    # ── Private: ensure minimum records ──────────────────────────────────────

    def _ensure_minimum_records(self, org_id: int):
        """Discover or create the minimum trials, studies, and germplasm for org 1."""
        from app.models.core import Trial, Study, Program
        from app.models.germplasm import Germplasm

        trials = (
            self.db.query(Trial)
            .filter(Trial.organization_id == org_id)
            .limit(10)
            .all()
        )
        studies = (
            self.db.query(Study)
            .filter(Study.organization_id == org_id)
            .limit(20)
            .all()
        )
        germplasm_list = (
            self.db.query(Germplasm)
            .filter(Germplasm.organization_id == org_id)
            .limit(20)
            .all()
        )

        # Create minimal trials if needed
        if len(trials) < _MIN_TRIALS:
            program = (
                self.db.query(Program)
                .filter(Program.organization_id == org_id)
                .first()
            )
            # program_id is NOT NULL — create a benchmark program if org 1 has none
            if program is None:
                prog_db_id = stable_demo_id("org1_bench_program", org_id)
                program = (
                    self.db.query(Program)
                    .filter(Program.program_db_id == prog_db_id)
                    .first()
                )
                if program is None:
                    program = Program(
                        organization_id=org_id,
                        program_db_id=prog_db_id,
                        program_name="Org1 Benchmark Breeding Program",
                        objective="Benchmark data for REEVU real-question evaluation",
                    )
                    self.db.add(program)
                    self.db.flush()
                    logger.info(
                        "Org1BenchmarkSeeder: created benchmark program id=%s for org %s",
                        program.id, org_id,
                    )

            for i in range(len(trials), _MIN_TRIALS):
                trial_db_id = stable_demo_id("org1_bench_trial", org_id, i)
                existing = (
                    self.db.query(Trial)
                    .filter(Trial.trial_db_id == trial_db_id)
                    .first()
                )
                if existing is None:
                    trial = Trial(
                        organization_id=org_id,
                        trial_db_id=trial_db_id,
                        trial_name=f"Org1 Benchmark Trial {i + 1}",
                        trial_type="Yield Trial",
                        program_id=program.id,
                    )
                    self.db.add(trial)
                    self.db.flush()
                    trials.append(trial)

                    study = Study(
                        organization_id=org_id,
                        study_db_id=stable_demo_id("org1_bench_study", org_id, i),
                        study_name=f"Org1 Benchmark Study {i + 1}",
                        trial_id=trial.id,
                    )
                    self.db.add(study)
                    self.db.flush()
                    studies.append(study)

        # Create minimal germplasm if needed
        if len(germplasm_list) < _MIN_GERMPLASM:
            rice_names = ["IR64", "Swarna", "MTU7029", "Samba Mahsuri", "BPT5204"]
            for i in range(len(germplasm_list), _MIN_GERMPLASM):
                germ_db_id = stable_demo_id("org1_bench_germ", org_id, i)
                existing = (
                    self.db.query(Germplasm)
                    .filter(Germplasm.germplasm_db_id == germ_db_id)
                    .first()
                )
                if existing is None:
                    germ = Germplasm(
                        organization_id=org_id,
                        germplasm_db_id=germ_db_id,
                        germplasm_name=rice_names[i % len(rice_names)],
                        common_crop_name="Rice",
                        accession_number=stable_demo_id("org1_bench_acc", org_id, i),
                    )
                    self.db.add(germ)
                    self.db.flush()
                    germplasm_list.append(germ)

        return trials[:_MIN_TRIALS], studies, germplasm_list[:_MIN_GERMPLASM]

    # ── Private: observation variables ───────────────────────────────────────

    def _seed_observation_variables(self, org_id: int) -> tuple[dict[str, object], int]:
        """Create/upsert observation variable records. Returns ({trait_name: obj}, new_count)."""
        from app.models.phenotyping import ObservationVariable

        result: dict[str, object] = {}
        new_count = 0
        for trait_name, trait_data in ORG1_TRAITS.items():
            obs_db_id = stable_demo_id("org1_bench_var", trait_name)
            existing = (
                self.db.query(ObservationVariable)
                .filter(ObservationVariable.observation_variable_db_id == obs_db_id)
                .first()
            )
            if existing is None:
                var = ObservationVariable(
                    organization_id=org_id,
                    observation_variable_db_id=obs_db_id,
                    observation_variable_name=trait_name,
                    common_crop_name="Rice",
                    trait_name=trait_name,
                    trait_description=f"Benchmark trait: {trait_name}",
                    trait_class=trait_data["trait_class"],
                    method_name=trait_data["method"],
                    scale_name=trait_data["scale"],
                    data_type="Numerical",
                    status="active",
                )
                self.db.add(var)
                self.db.flush()
                result[trait_name] = var
                new_count += 1
            else:
                result[trait_name] = existing
        return result, new_count

    # ── Private: observation units ────────────────────────────────────────────

    def _seed_observation_units(
        self, org_id: int, trials, studies, germplasm_list
    ) -> tuple[list, int]:
        """Create/upsert observation units. Returns (units_list, new_count)."""
        from app.models.phenotyping import ObservationUnit

        study_by_trial: dict[int, object] = {}
        for study in studies:
            if study.trial_id and study.trial_id not in study_by_trial:
                study_by_trial[study.trial_id] = study

        units = []
        new_count = 0
        for trial in trials:
            study = study_by_trial.get(trial.id)
            if study is None:
                continue
            for germ in germplasm_list:
                unit_db_id = stable_demo_id("org1_bench_unit", trial.id, germ.id)
                existing = (
                    self.db.query(ObservationUnit)
                    .filter(ObservationUnit.observation_unit_db_id == unit_db_id)
                    .first()
                )
                if existing is None:
                    unit = ObservationUnit(
                        organization_id=org_id,
                        observation_unit_db_id=unit_db_id,
                        observation_unit_name=f"org1_bench_{trial.id}_{germ.id}",
                        study_id=study.id,
                        germplasm_id=germ.id,
                        entry_type="test",
                    )
                    self.db.add(unit)
                    self.db.flush()
                    units.append(unit)
                    new_count += 1
                else:
                    units.append(existing)
        return units, new_count

    # ── Private: observations ─────────────────────────────────────────────────

    def _seed_observations(
        self, org_id: int, obs_units: list, obs_vars: dict[str, object]
    ) -> int:
        """Create/upsert observations for each (unit, trait) pair."""
        from app.models.phenotyping import Observation

        count = 0
        # Use first 2 traits for minimum coverage
        trait_names = list(ORG1_TRAITS.keys())[:2]

        for unit in obs_units:
            for trait_name in trait_names:
                var = obs_vars.get(trait_name)
                if var is None:
                    continue
                obs_db_id = stable_demo_id("org1_bench_obs", unit.id, trait_name)
                existing = (
                    self.db.query(Observation)
                    .filter(Observation.observation_db_id == obs_db_id)
                    .first()
                )
                trait_data = ORG1_TRAITS[trait_name]
                value = stable_demo_float(
                    trait_data["min"], trait_data["max"],
                    unit.id, trait_name,
                )
                if existing is None:
                    obs = Observation(
                        organization_id=org_id,
                        observation_db_id=obs_db_id,
                        observation_variable_id=var.id,
                        observation_unit_id=unit.id,
                        study_id=unit.study_id,
                        germplasm_id=unit.germplasm_id,
                        value=str(value),
                        observation_time_stamp=demo_dataset_datetime().isoformat(),
                    )
                    self.db.add(obs)
                    count += 1
                else:
                    existing.value = str(value)
        return count

    # ── Private: GWAS ─────────────────────────────────────────────────────────

    def _seed_gwas(self, org_id: int) -> int:
        """Create/upsert GWAS runs and results. Returns count."""
        from app.modules.bio_analytics.models import GWASRun, GWASResult

        count = 0
        run_id_by_key: dict[str, int] = {}

        for run_data in ORG1_GWAS_RUNS:
            existing = (
                self.db.query(GWASRun)
                .filter(
                    GWASRun.organization_id == org_id,
                    GWASRun.run_name == run_data["run_name"],
                )
                .first()
            )
            if existing is None:
                run = GWASRun(
                    organization_id=org_id,
                    run_name=run_data["run_name"],
                    trait_name=run_data["trait_name"],
                    method=run_data["method"],
                    sample_size=run_data["sample_size"],
                    marker_count=run_data["marker_count"],
                    significance_threshold=run_data["significance_threshold"],
                    significant_marker_count=run_data["significant_marker_count"],
                    manhattan_plot_data=run_data.get("manhattan_plot_data"),
                    qq_plot_data=run_data.get("qq_plot_data"),
                    created_at=demo_dataset_datetime(),
                )
                self.db.add(run)
                self.db.flush()
                run_id_by_key[run_data["run_key"]] = run.id
                count += 1
            else:
                run_id_by_key[run_data["run_key"]] = existing.id

        for result_data in ORG1_GWAS_RESULTS:
            run_id = run_id_by_key.get(result_data["run_key"])
            if run_id is None:
                continue
            existing = (
                self.db.query(GWASResult)
                .filter(
                    GWASResult.run_id == run_id,
                    GWASResult.marker_name == result_data["marker_name"],
                )
                .first()
            )
            if existing is None:
                result = GWASResult(
                    organization_id=org_id,
                    run_id=run_id,
                    marker_name=result_data["marker_name"],
                    chromosome=result_data["chromosome"],
                    position=result_data["position"],
                    p_value=result_data["p_value"],
                    neg_log10_p=result_data["neg_log10_p"],
                    effect_size=result_data["effect_size"],
                    standard_error=result_data["standard_error"],
                    maf=result_data["maf"],
                    is_significant=result_data["is_significant"],
                )
                self.db.add(result)
                count += 1
        return count

    # ── Private: QTLs ─────────────────────────────────────────────────────────

    def _seed_qtls(self, org_id: int) -> int:
        """Create/upsert QTL records and candidate genes. Returns count."""
        from app.modules.bio_analytics.models import BioQTL, CandidateGene

        count = 0
        for qtl_data in ORG1_QTLS:
            qtl_db_id = stable_demo_id("org1_bench_qtl", qtl_data["qtl_key"])
            existing = (
                self.db.query(BioQTL)
                .filter(BioQTL.qtl_db_id == qtl_db_id)
                .first()
            )
            if existing is None:
                qtl = BioQTL(
                    organization_id=org_id,
                    qtl_db_id=qtl_db_id,
                    qtl_name=qtl_data["qtl_name"],
                    trait=qtl_data["trait"],
                    population=qtl_data["population"],
                    method=qtl_data["method"],
                    chromosome=qtl_data["chromosome"],
                    start_position=qtl_data["start_position"],
                    end_position=qtl_data["end_position"],
                    peak_position=qtl_data["peak_position"],
                    lod=qtl_data["lod"],
                    lod_score=qtl_data["lod_score"],
                    pve=qtl_data["pve"],
                    add_effect=qtl_data["add_effect"],
                    confidence_interval_low=qtl_data["confidence_interval_low"],
                    confidence_interval_high=qtl_data["confidence_interval_high"],
                )
                self.db.add(qtl)
                self.db.flush()
                qtl_id = qtl.id
                count += 1
            else:
                qtl_id = existing.id

            for gene_data in qtl_data.get("candidate_genes", []):
                existing_gene = (
                    self.db.query(CandidateGene)
                    .filter(
                        CandidateGene.qtl_id == qtl_id,
                        CandidateGene.gene_id == gene_data["gene_id"],
                    )
                    .first()
                )
                if existing_gene is None:
                    gene = CandidateGene(
                        organization_id=org_id,
                        qtl_id=qtl_id,
                        gene_id=gene_data["gene_id"],
                        gene_name=gene_data["gene_name"],
                        chromosome=gene_data["chromosome"],
                        start_position=gene_data["start_position"],
                        end_position=gene_data["end_position"],
                        description=gene_data.get("annotation"),
                    )
                    self.db.add(gene)
                    count += 1
        return count

    def _seed_speed_breeding_protocols(self, org_id: int) -> int:
        """Create/upsert benchmark speed-breeding protocols. Returns count."""
        from app.models.speed_breeding import SpeedBreedingProtocol

        count = 0
        for protocol_data in ORG1_SPEED_BREEDING_PROTOCOLS:
            existing = (
                self.db.query(SpeedBreedingProtocol)
                .filter(
                    SpeedBreedingProtocol.organization_id == org_id,
                    SpeedBreedingProtocol.name == protocol_data["name"],
                )
                .first()
            )
            if existing is None:
                protocol = SpeedBreedingProtocol(
                    organization_id=org_id,
                    **protocol_data,
                )
                self.db.add(protocol)
                count += 1
            else:
                for key, value in protocol_data.items():
                    setattr(existing, key, value)
        return count

    # ── Private: clear helpers ────────────────────────────────────────────────

    def _clear_candidate_genes(self) -> int:
        """Remove candidate genes linked to org1_bench QTLs."""
        try:
            from app.modules.bio_analytics.models import BioQTL, CandidateGene

            qtl_ids = [
                row.id
                for row in self.db.query(BioQTL)
                .filter(BioQTL.qtl_db_id.like("org1_bench_qtl_%"))
                .all()
            ]
            if not qtl_ids:
                return 0
            deleted = (
                self.db.query(CandidateGene)
                .filter(CandidateGene.qtl_id.in_(qtl_ids))
                .delete(synchronize_session=False)
            )
            return deleted or 0
        except Exception:
            return 0

    def _clear_gwas_results(self) -> int:
        try:
            from app.modules.bio_analytics.models import GWASRun, GWASResult

            run_names = [r["run_name"] for r in ORG1_GWAS_RUNS]
            run_ids = [
                row.id
                for row in self.db.query(GWASRun)
                .filter(GWASRun.run_name.in_(run_names))
                .all()
            ]
            if not run_ids:
                return 0
            deleted = (
                self.db.query(GWASResult)
                .filter(GWASResult.run_id.in_(run_ids))
                .delete(synchronize_session=False)
            )
            return deleted or 0
        except Exception:
            return 0

    def _clear_qtls(self) -> int:
        try:
            from app.modules.bio_analytics.models import BioQTL

            deleted = (
                self.db.query(BioQTL)
                .filter(BioQTL.qtl_db_id.like("org1_bench_qtl_%"))
                .delete(synchronize_session=False)
            )
            return deleted or 0
        except Exception:
            return 0

    def _clear_gwas_runs(self) -> int:
        try:
            from app.modules.bio_analytics.models import GWASRun

            run_names = [r["run_name"] for r in ORG1_GWAS_RUNS]
            deleted = (
                self.db.query(GWASRun)
                .filter(GWASRun.run_name.in_(run_names))
                .delete(synchronize_session=False)
            )
            return deleted or 0
        except Exception:
            return 0

    def _clear_observations(self) -> int:
        try:
            from app.models.phenotyping import Observation

            deleted = (
                self.db.query(Observation)
                .filter(Observation.observation_db_id.like("org1_bench_obs_%"))
                .delete(synchronize_session=False)
            )
            return deleted or 0
        except Exception:
            return 0

    def _clear_observation_units(self) -> int:
        try:
            from app.models.phenotyping import ObservationUnit

            deleted = (
                self.db.query(ObservationUnit)
                .filter(ObservationUnit.observation_unit_db_id.like("org1_bench_unit_%"))
                .delete(synchronize_session=False)
            )
            return deleted or 0
        except Exception:
            return 0

    def _clear_observation_variables(self) -> int:
        try:
            from app.models.phenotyping import ObservationVariable

            deleted = (
                self.db.query(ObservationVariable)
                .filter(ObservationVariable.observation_variable_db_id.like("org1_bench_var_%"))
                .delete(synchronize_session=False)
            )
            return deleted or 0
        except Exception:
            return 0

    def _clear_speed_breeding_protocols(self) -> int:
        try:
            from app.models.speed_breeding import SpeedBreedingProtocol

            protocol_names = [protocol["name"] for protocol in ORG1_SPEED_BREEDING_PROTOCOLS]
            deleted = (
                self.db.query(SpeedBreedingProtocol)
                .filter(SpeedBreedingProtocol.name.in_(protocol_names))
                .delete(synchronize_session=False)
            )
            return deleted or 0
        except Exception:
            return 0
