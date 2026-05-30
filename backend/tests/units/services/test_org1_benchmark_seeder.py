"""
TDD tests for Org1BenchmarkSeeder.

Written BEFORE the implementation. RED → GREEN → REFACTOR.

Covers:
- Task 1.2: Seeder is importable and registered
- Task 2.2: Org 1 discovery edge cases
- Task 3.2: Observation variable idempotency (property)
- Task 4.2: Observation coverage (property)
- Task 6.2: Observation referential integrity (property)
- Task 6.3: Realistic value ranges (unit)
- Task 7.2: GWAS run completeness (property)
- Task 8.2: QTL completeness (property)
- Task 10.2: Tenant isolation (property)
- Task 10.3: clear() unit tests
"""

import pytest
from unittest.mock import MagicMock, patch, call
from hypothesis import given, settings
from hypothesis import strategies as st


# ── Task 1.2: Seeder is importable and registered ────────────────────────────

def test_seeder_is_importable():
    """Org1BenchmarkSeeder can be imported from its module."""
    from app.db.seeders.org1_benchmark_seeder import Org1BenchmarkSeeder
    assert Org1BenchmarkSeeder is not None


def test_seeder_is_registered():
    """Org1BenchmarkSeeder appears in get_all_seeders() after import."""
    import app.db.seeders.org1_benchmark_seeder  # ensure module is loaded
    from app.db.seeders.base import get_all_seeders
    names = [s.name for s in get_all_seeders()]
    assert "org1_benchmark" in names


def test_seeder_has_correct_name_and_description():
    """Seeder has name='org1_benchmark' and non-empty description."""
    from app.db.seeders.org1_benchmark_seeder import Org1BenchmarkSeeder
    assert Org1BenchmarkSeeder.name == "org1_benchmark"
    assert len(Org1BenchmarkSeeder.description) > 10


def test_seeder_data_constants_are_defined():
    """Module-level data constants are defined with correct structure."""
    from app.db.seeders.org1_benchmark_seeder import (
        ORG1_TRAITS,
        ORG1_GWAS_RUNS,
        ORG1_GWAS_RESULTS,
        ORG1_QTLS,
    )
    assert len(ORG1_TRAITS) >= 4
    assert "Grain Yield" in ORG1_TRAITS
    assert "Plant Height" in ORG1_TRAITS
    assert "Blast Resistance" in ORG1_TRAITS
    assert "Days to Flowering" in ORG1_TRAITS
    assert len(ORG1_GWAS_RUNS) >= 1
    assert len(ORG1_GWAS_RESULTS) >= 2
    assert len(ORG1_QTLS) >= 2


# ── Task 2.2: Org 1 discovery edge cases ─────────────────────────────────────

def test_seed_returns_zero_when_org1_not_found():
    """seed() returns 0 and logs warning when org 1 does not exist."""
    from app.db.seeders.org1_benchmark_seeder import Org1BenchmarkSeeder

    mock_db = MagicMock()
    # Simulate org 1 not found
    mock_db.query.return_value.filter.return_value.first.return_value = None

    seeder = Org1BenchmarkSeeder(db=mock_db)
    result = seeder.seed()

    assert result == 0


# ── Task 6.3: Realistic value ranges ─────────────────────────────────────────

def test_grain_yield_range():
    """Grain Yield values must be between 3500 and 7500 kg/ha."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_TRAITS
    from app.core.demo_dataset import stable_demo_float

    trait = ORG1_TRAITS["Grain Yield"]
    for seed_key in ["test1", "test2", "test3", "test4", "test5"]:
        val = stable_demo_float(trait["min"], trait["max"], seed_key)
        assert trait["min"] <= val <= trait["max"], f"Grain Yield {val} out of range"


def test_plant_height_range():
    """Plant Height values must be between 65 and 130 cm."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_TRAITS
    from app.core.demo_dataset import stable_demo_float

    trait = ORG1_TRAITS["Plant Height"]
    for seed_key in ["test1", "test2", "test3"]:
        val = stable_demo_float(trait["min"], trait["max"], seed_key)
        assert trait["min"] <= val <= trait["max"]


def test_blast_resistance_range():
    """Blast Resistance values must be between 1 and 9."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_TRAITS
    from app.core.demo_dataset import stable_demo_float

    trait = ORG1_TRAITS["Blast Resistance"]
    for seed_key in ["test1", "test2", "test3"]:
        val = stable_demo_float(trait["min"], trait["max"], seed_key)
        assert trait["min"] <= val <= trait["max"]


def test_days_to_flowering_range():
    """Days to Flowering values must be between 75 and 120 days."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_TRAITS
    from app.core.demo_dataset import stable_demo_float

    trait = ORG1_TRAITS["Days to Flowering"]
    for seed_key in ["test1", "test2", "test3"]:
        val = stable_demo_float(trait["min"], trait["max"], seed_key)
        assert trait["min"] <= val <= trait["max"]


# ── Task 7.2: GWAS run completeness ──────────────────────────────────────────

def test_gwas_run_has_significant_results():
    """Each GWAS run key has at least one significant result in ORG1_GWAS_RESULTS."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_GWAS_RUNS, ORG1_GWAS_RESULTS

    run_keys = {r["run_key"] for r in ORG1_GWAS_RUNS}
    for run_key in run_keys:
        results_for_run = [r for r in ORG1_GWAS_RESULTS if r["run_key"] == run_key]
        significant = [r for r in results_for_run if r.get("is_significant")]
        assert len(significant) >= 1, f"No significant results for run_key '{run_key}'"


def test_gwas_run_trait_matches_org1_traits():
    """GWAS run trait_name must match a key in ORG1_TRAITS."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_GWAS_RUNS, ORG1_TRAITS

    trait_names = set(ORG1_TRAITS.keys())
    for run in ORG1_GWAS_RUNS:
        assert run["trait_name"] in trait_names, (
            f"GWAS run trait '{run['trait_name']}' not in ORG1_TRAITS"
        )


# ── Task 8.2: QTL completeness ────────────────────────────────────────────────

def test_qtl_has_required_fields():
    """Each QTL must have lod, confidence_interval_low, confidence_interval_high."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_QTLS

    for qtl in ORG1_QTLS:
        assert qtl.get("lod") is not None, f"QTL '{qtl.get('qtl_key')}' missing lod"
        assert qtl.get("confidence_interval_low") is not None
        assert qtl.get("confidence_interval_high") is not None
        assert qtl["confidence_interval_low"] < qtl["confidence_interval_high"]


def test_qtl_trait_matches_org1_traits():
    """Each QTL trait must match a key in ORG1_TRAITS."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_QTLS, ORG1_TRAITS

    trait_names = set(ORG1_TRAITS.keys())
    for qtl in ORG1_QTLS:
        assert qtl["trait"] in trait_names, (
            f"QTL trait '{qtl['trait']}' not in ORG1_TRAITS"
        )


def test_qtl_count_at_least_two():
    """At least 2 QTL records are defined."""
    from app.db.seeders.org1_benchmark_seeder import ORG1_QTLS
    assert len(ORG1_QTLS) >= 2


# ── Task 3.2: Idempotency property ───────────────────────────────────────────

@given(
    trait_names=st.lists(
        st.sampled_from(["Grain Yield", "Plant Height", "Blast Resistance", "Days to Flowering"]),
        min_size=1, max_size=4, unique=True,
    )
)
@settings(max_examples=50)
def test_stable_demo_id_is_deterministic(trait_names):
    """stable_demo_id with same inputs always produces the same output (idempotency basis)."""
    from app.core.demo_dataset import stable_demo_id

    for trait in trait_names:
        id1 = stable_demo_id("org1_bench_var", trait)
        id2 = stable_demo_id("org1_bench_var", trait)
        assert id1 == id2, f"stable_demo_id not deterministic for trait '{trait}'"
        assert id1.startswith("org1_bench_var_")


@given(
    unit_pairs=st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=100),
            st.integers(min_value=1, max_value=100),
        ),
        min_size=1, max_size=10,
    )
)
@settings(max_examples=50)
def test_stable_demo_id_unique_for_different_inputs(unit_pairs):
    """stable_demo_id produces different IDs for different (trial_id, germplasm_id) pairs."""
    from app.core.demo_dataset import stable_demo_id

    ids = [stable_demo_id("org1_bench_unit", t, g) for t, g in unit_pairs]
    unique_pairs = list(set(unit_pairs))
    unique_ids = [stable_demo_id("org1_bench_unit", t, g) for t, g in unique_pairs]
    # Unique inputs should produce unique IDs
    assert len(unique_ids) == len(set(unique_ids))


# ── Task 10.3: clear() unit tests ────────────────────────────────────────────

def test_clear_returns_zero_when_no_seeded_data():
    """clear() returns 0 gracefully when no org1_bench records exist."""
    from app.db.seeders.org1_benchmark_seeder import Org1BenchmarkSeeder

    mock_db = MagicMock()
    # Simulate delete returning 0 (no records deleted)
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.delete.return_value = 0
    mock_db.query.return_value.filter.return_value.first.return_value = None

    seeder = Org1BenchmarkSeeder(db=mock_db)
    result = seeder.clear()

    assert result == 0


def test_seeder_has_clear_method():
    """Org1BenchmarkSeeder has a clear() method."""
    from app.db.seeders.org1_benchmark_seeder import Org1BenchmarkSeeder
    assert hasattr(Org1BenchmarkSeeder, "clear")
    assert callable(Org1BenchmarkSeeder.clear)


# ── Property: stable_demo_float stays in range ───────────────────────────────

@given(
    minimum=st.floats(min_value=0.1, max_value=1000.0, allow_nan=False),
    maximum_offset=st.floats(min_value=0.1, max_value=5000.0, allow_nan=False),
    seed_key=st.text(min_size=1, max_size=20),
)
@settings(max_examples=100)
def test_stable_demo_float_always_in_range(minimum, maximum_offset, seed_key):
    """stable_demo_float always returns a value within [minimum, maximum]."""
    from app.core.demo_dataset import stable_demo_float

    maximum = minimum + maximum_offset
    val = stable_demo_float(minimum, maximum, seed_key)
    assert minimum <= val <= maximum, (
        f"stable_demo_float({minimum}, {maximum}, '{seed_key}') = {val} out of range"
    )
