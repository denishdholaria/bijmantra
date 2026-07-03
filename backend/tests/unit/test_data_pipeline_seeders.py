from __future__ import annotations

from unittest.mock import MagicMock


def test_pipeline_seeders_are_importable_and_named():
    from app.db.seeders.pipeline_genotyping import PipelineGenotypingSeeder
    from app.db.seeders.pipeline_germplasm import PipelineGermplasmSeeder
    from app.db.seeders.pipeline_gwas import PipelineGWASSeeder
    from app.db.seeders.pipeline_genotyping import PipelineGenotypingSeeder
    from app.db.seeders.pipeline_observations import PipelineObservationsSeeder
    from app.db.seeders.pipeline_phenotyping import PipelinePhenotypingSeeder
    from app.db.seeders.pipeline_qtls import PipelineQTLSeeder
    from app.db.seeders.pipeline_trials import PipelineTrialsSeeder

    assert PipelineGermplasmSeeder.name == "pipeline_germplasm"
    assert PipelinePhenotypingSeeder.name == "pipeline_phenotyping"
    assert PipelineGenotypingSeeder.name == "pipeline_genotyping"
    assert PipelineTrialsSeeder.name == "pipeline_trials"
    assert PipelineObservationsSeeder.name == "pipeline_observations"
    assert PipelineGWASSeeder.name == "pipeline_gwas"
    assert PipelineQTLSeeder.name == "pipeline_qtls"


def test_pipeline_seeder_mixin_resolves_repo_output_path():
    from app.db.seeders.pipeline_base import PipelineSeederMixin

    mixin = PipelineSeederMixin()
    output_dir = mixin.pipeline_output_dir()

    assert output_dir.name == "output"
    assert output_dir.parent.name == "data_pipeline"


def test_pipeline_seeders_refuse_missing_output_gracefully():
    from app.db.seeders.pipeline_germplasm import PipelineGermplasmSeeder

    seeder = PipelineGermplasmSeeder(db=MagicMock())
    seeder.output_filename = "definitely_missing_pipeline_output.json"

    assert seeder.seed() == 0


def test_pipeline_seeders_are_idempotent_and_unblock_org1_reevu_tables(db_session):
    from app.models.base import Base
    from app.core.demo_dataset import DEMO_DATASET_ORG_NAME, DEMO_DATASET_USER_EMAIL
    from app.db.seeders.pipeline_germplasm import PipelineGermplasmSeeder
    from app.db.seeders.pipeline_gwas import PipelineGWASSeeder
    from app.db.seeders.pipeline_genotyping import PipelineGenotypingSeeder
    from app.db.seeders.pipeline_observations import PipelineObservationsSeeder
    from app.db.seeders.pipeline_phenotyping import PipelinePhenotypingSeeder
    from app.db.seeders.pipeline_qtls import PipelineQTLSeeder
    from app.db.seeders.pipeline_trials import PipelineTrialsSeeder
    from app.models.core import Organization
    from app.models.phenotyping import Observation
    from app.modules.bio_analytics.models import BioQTL, GWASRun

    required_table_names = [
        "organizations",
        "people",
        "locations",
        "seasons",
        "programs",
        "trials",
        "studies",
        "crossing_projects",
        "crosses",
        "germplasm",
        "observation_variables",
        "observation_units",
        "observations",
        "reference_sets",
        "references",
        "genome_maps",
        "linkage_groups",
        "variant_sets",
        "variants",
        "bio_gwas_runs",
        "bio_gwas_results",
        "bio_qtls",
        "bio_candidate_genes",
    ]
    Base.metadata.create_all(
        bind=db_session.bind,
        tables=[Base.metadata.tables[name] for name in required_table_names if name in Base.metadata.tables],
    )

    if db_session.get(Organization, 1) is None:
        db_session.add(
            Organization(
                id=1,
                name="Pipeline Benchmark Organization",
                contact_email="benchmark@example.org",
                is_active=True,
            )
        )
        db_session.commit()

    if db_session.get(Organization, 2) is None:
        db_session.add(
            Organization(
                id=2,
                name=DEMO_DATASET_ORG_NAME,
                contact_email=DEMO_DATASET_USER_EMAIL,
                is_active=True,
            )
        )
        db_session.commit()

    seeder_classes = [
        PipelineTrialsSeeder,
        PipelineGermplasmSeeder,
        PipelinePhenotypingSeeder,
        PipelineObservationsSeeder,
        PipelineGenotypingSeeder,
        PipelineGWASSeeder,
        PipelineQTLSeeder,
    ]
    for seeder_class in reversed(seeder_classes):
        seeder_class(db_session).clear()

    first_counts = [seeder_class(db_session).seed() for seeder_class in seeder_classes]
    second_counts = [seeder_class(db_session).seed() for seeder_class in seeder_classes]

    assert any(count > 0 for count in first_counts)
    assert second_counts == [0, 0, 0, 0, 0, 0, 0]
    assert db_session.query(Observation).filter(Observation.organization_id == 1).count() >= 1
    assert db_session.query(GWASRun).filter(GWASRun.organization_id == 1).count() >= 1
    assert db_session.query(BioQTL).filter(BioQTL.organization_id == 1).count() >= 2
