from pathlib import Path

from app.core.config import settings
from app.core.demo_dataset import (
    DEMO_DATASET,
    demo_dataset_date,
    demo_dataset_datetime,
    stable_demo_choice,
    stable_demo_float,
    stable_demo_id,
)
from app.db.seeders.base import BaseSeeder


BACKEND_ROOT = Path(__file__).resolve().parents[3]
SEEDER_REGISTRY_FILE = BACKEND_ROOT / "app" / "db" / "seeders" / "__init__.py"
DEMO_BIO_ANALYTICS_FILE = BACKEND_ROOT / "app" / "db" / "seeders" / "demo_bio_analytics.py"
CANONICAL_DEMO_SEEDERS = [
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_benchmark_alignment.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_bio_analytics.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_brapi.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_brapi_phenotyping.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_collaboration.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_core.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_crossing.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_data_management.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_field_operations.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_genotyping.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_germplasm.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_iot.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_phenotyping.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_stress_resistance.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_user_management.py",
    BACKEND_ROOT / "app" / "db" / "seeders" / "demo_users.py",
]
PROHIBITED_PATTERNS = (
    "uuid.uuid4",
    "import random",
    "random.",
    "datetime.now(",
    "date.today(",
)


class _StubSeeder(BaseSeeder):
    def seed(self) -> int:
        return 0

    def clear(self) -> int:
        return 0


def test_demo_dataset_contract_matches_runtime_settings() -> None:
    assert settings.DEMO_DATASET_NAME == DEMO_DATASET.name
    assert settings.DEMO_DATASET_VERSION == DEMO_DATASET.version
    assert settings.DEMO_ORG_NAME == DEMO_DATASET.organization_name
    assert settings.DEMO_USER_EMAIL == DEMO_DATASET.user_email
    assert "tdd" in DEMO_DATASET.supported_flows
    assert DEMO_DATASET.isolated_from == ("production", "staging")


def test_demo_dataset_helpers_are_deterministic() -> None:
    assert demo_dataset_datetime().isoformat() == "2025-08-15T10:00:00+00:00"
    assert demo_dataset_date().isoformat() == "2025-08-15"

    assert stable_demo_id("demo_loc", "IRRI Research Station") == stable_demo_id(
        "demo_loc", "IRRI Research Station"
    )
    assert stable_demo_id("demo_loc", "IRRI Research Station") != stable_demo_id(
        "demo_loc", "CRRI Research Farm"
    )

    rainfall = stable_demo_choice(
        [0.0, 0.0, 2.5, 5.0, 12.0],
        "env-kharif-2025-field-a",
        2,
        "precipitation_total",
    )
    assert rainfall == stable_demo_choice(
        [0.0, 0.0, 2.5, 5.0, 12.0],
        "env-kharif-2025-field-a",
        2,
        "precipitation_total",
    )

    assert stable_demo_float(50, 150, "Plot-001-A", "Plant Height", digits=2) == stable_demo_float(
        50,
        150,
        "Plot-001-A",
        "Plant Height",
        digits=2,
    )


def test_base_seeder_allows_same_demo_dataset_for_tdd(monkeypatch) -> None:
    seeder = _StubSeeder(db=None)

    monkeypatch.setattr(settings, "SEED_DEMO_DATA", True)
    assert seeder.should_run("dev") is True
    assert seeder.should_run("test") is True
    assert seeder.should_run("prod") is False


def test_canonical_demo_seeders_avoid_runtime_entropy_and_wall_clock() -> None:
    missing_files = [path.name for path in CANONICAL_DEMO_SEEDERS if not path.exists()]
    assert not missing_files, f"Missing canonical demo seeders: {missing_files}"

    violations = []
    for path in CANONICAL_DEMO_SEEDERS:
        content = path.read_text(encoding="utf-8")
        for pattern in PROHIBITED_PATTERNS:
            if pattern in content:
                violations.append(f"{path.name}: {pattern}")

    assert not violations, (
        "Canonical demo seeders must remain deterministic and reproducible: "
        + ", ".join(violations)
    )


def test_demo_benchmark_seeders_import_after_prerequisites() -> None:
    content = SEEDER_REGISTRY_FILE.read_text(encoding="utf-8")

    demo_germplasm_import = content.index("from .demo_germplasm import DemoGermplasmSeeder")
    demo_brapi_import = content.index("from .demo_brapi import DemoBrAPISeeder")
    demo_phenotyping_import = content.index("from .demo_phenotyping import DemoPhenotypingSeeder")
    benchmark_alignment_import = content.index(
        "from .demo_benchmark_alignment import DemoBenchmarkAlignmentSeeder"
    )
    bio_analytics_import = content.index(
        "from .demo_bio_analytics import DemoBioAnalyticsSeeder"
    )

    assert demo_germplasm_import < demo_brapi_import
    assert demo_germplasm_import < demo_phenotyping_import
    assert demo_germplasm_import < benchmark_alignment_import
    assert demo_brapi_import < benchmark_alignment_import
    assert demo_phenotyping_import < benchmark_alignment_import

    assert demo_germplasm_import < bio_analytics_import


def test_demo_bio_analytics_clear_is_scoped_to_seeded_records() -> None:
    content = DEMO_BIO_ANALYTICS_FILE.read_text(encoding="utf-8")

    broad_delete_patterns = (
        "self.db.query(CandidateGene).filter(CandidateGene.organization_id == org_id).delete()",
        "self.db.query(BioQTL).filter(BioQTL.organization_id == org_id).delete()",
        "self.db.query(GWASResult).filter(GWASResult.organization_id == org_id).delete()",
        "self.db.query(GWASRun).filter(GWASRun.organization_id == org_id).delete()",
    )

    for pattern in broad_delete_patterns:
        assert pattern not in content

    assert "GWASRun.run_name.in_(seeded_run_names)" in content
    assert "BioQTL.qtl_db_id.in_(seeded_qtl_db_ids)" in content
    assert "CandidateGene.qtl_id.in_(seeded_qtl_ids)" in content
    assert "GWASResult.run_id.in_(seeded_run_ids)" in content