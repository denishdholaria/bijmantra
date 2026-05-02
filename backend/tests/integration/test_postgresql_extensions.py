"""
PostgreSQL extension integration tests.

Verifies all 8 extensions are enabled and functional.
Requires a live PostgreSQL instance with all extensions loaded.
Set BIJMANTRA_TEST_POSTGRES_DSN to run.
"""

import os

import pytest
from sqlalchemy import create_engine, text

pytestmark = [pytest.mark.integration, pytest.mark.postgres_integration]
POSTGRES_DSN_ENV = "BIJMANTRA_TEST_POSTGRES_DSN"

REQUIRED_EXTENSIONS = [
    "timescaledb",
    "vector",
    "postgis",
    "pg_trgm",
    "uuid-ossp",
    "pgcrypto",
    "pgaudit",
    "ltree",
]


def get_dsn():
    dsn = os.environ.get(POSTGRES_DSN_ENV)
    if not dsn:
        pytest.skip(f"{POSTGRES_DSN_ENV} not configured")
    return dsn


# --- Task 10.1: All 8 extensions present ---


def test_all_required_extensions_enabled():
    """All 8 required extensions must be present in pg_extension."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT extname FROM pg_extension ORDER BY extname"))
        loaded = {row[0] for row in result.all()}

        missing = [ext for ext in REQUIRED_EXTENSIONS if ext not in loaded]
        assert not missing, f"Missing extensions: {missing}"


@pytest.mark.parametrize("extension", REQUIRED_EXTENSIONS)
def test_extension_individually_enabled(extension):
    """Each required extension must be individually verifiable."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = :ext"),
            {"ext": extension},
        )
        row = result.fetchone()
        assert row is not None, f"Extension '{extension}' is not enabled"


# --- Task 10.3: TimescaleDB hypertable ---


def test_timescaledb_hypertable_exists():
    """iot_telemetry must be a TimescaleDB hypertable."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT hypertable_name
                FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'iot_telemetry'
            """)
        )
        row = result.fetchone()
        assert row is not None, "iot_telemetry is not a hypertable"


def test_timescaledb_continuous_aggregates_exist():
    """iot_telemetry_hourly and iot_telemetry_daily continuous aggregates must exist."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT view_name
                FROM timescaledb_information.continuous_aggregates
                WHERE view_name IN ('iot_telemetry_hourly', 'iot_telemetry_daily')
                ORDER BY view_name
            """)
        )
        views = {row[0] for row in result.all()}
        assert "iot_telemetry_hourly" in views, "iot_telemetry_hourly continuous aggregate missing"
        assert "iot_telemetry_daily" in views, "iot_telemetry_daily continuous aggregate missing"


def test_timescaledb_compression_policy_exists():
    """iot_telemetry must have a compression policy."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT hypertable_name
                FROM timescaledb_information.jobs
                WHERE hypertable_name = 'iot_telemetry'
                  AND proc_name = 'policy_compression'
            """)
        )
        row = result.fetchone()
        assert row is not None, "iot_telemetry has no compression policy"


# --- Task 10.4: ltree ancestor/descendant queries ---


def test_ltree_extension_functional():
    """ltree operators must work correctly."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        conn.execute(text("BEGIN"))
        try:
            conn.execute(
                text("""
                CREATE TEMP TABLE ltree_test (
                    id serial PRIMARY KEY,
                    path ltree
                )
            """)
            )
            conn.execute(
                text("""
                INSERT INTO ltree_test (path) VALUES
                ('root'),
                ('root.child1'),
                ('root.child1.grandchild1'),
                ('root.child2')
            """)
            )

            # Test descendant query (<@)
            result = conn.execute(
                text("""
                SELECT path::text FROM ltree_test
                WHERE path <@ 'root.child1'
                ORDER BY path::text
            """)
            )
            descendants = [row[0] for row in result.all()]
            assert "root.child1" in descendants
            assert "root.child1.grandchild1" in descendants
            assert "root.child2" not in descendants

            # Test ancestor query (@>)
            result = conn.execute(
                text("""
                SELECT path::text FROM ltree_test
                WHERE path @> 'root.child1.grandchild1'
                ORDER BY path::text
            """)
            )
            ancestors = [row[0] for row in result.all()]
            assert "root" in ancestors
            assert "root.child1" in ancestors
            assert "root.child1.grandchild1" in ancestors
            assert "root.child2" not in ancestors

        finally:
            conn.execute(text("ROLLBACK"))


def test_ltree_org_path_column_exists():
    """organizations table must have org_path ltree column."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'organizations'
                  AND column_name = 'org_path'
            """)
        )
        row = result.fetchone()
        assert row is not None, "organizations.org_path column missing"


def test_get_org_subtree_function_exists():
    """get_org_subtree() utility function must exist."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_name = 'get_org_subtree'
                  AND routine_type = 'FUNCTION'
            """)
        )
        row = result.fetchone()
        assert row is not None, "get_org_subtree() function missing"


# --- Task 10.5: pg_trgm similarity search ---


def test_pg_trgm_similarity_function():
    """similarity() function must return a score between 0 and 1."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT similarity('wheat', 'wheat') AS exact_match"))
        score = result.scalar_one()
        assert score == 1.0, f"Expected 1.0 for exact match, got {score}"

        result = conn.execute(
            text("SELECT similarity('wheat', 'completely_different_xyz') AS no_match")
        )
        score = result.scalar_one()
        assert score < 0.3, f"Expected low score for dissimilar strings, got {score}"


def test_pg_trgm_gin_indexes_exist():
    """GIN indexes with gin_trgm_ops must exist on searchable text columns."""
    engine = create_engine(get_dsn())
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT indexname
                FROM pg_indexes
                WHERE indexname IN (
                    'idx_germplasm_name_trgm',
                    'idx_germplasm_display_name_trgm',
                    'idx_users_full_name_trgm',
                    'idx_users_email_trgm',
                    'idx_programs_name_trgm',
                    'idx_trials_name_trgm',
                    'idx_studies_name_trgm'
                )
                ORDER BY indexname
            """)
        )
        found = {row[0] for row in result.all()}
        expected = {
            "idx_germplasm_name_trgm",
            "idx_germplasm_display_name_trgm",
            "idx_users_full_name_trgm",
            "idx_users_email_trgm",
            "idx_programs_name_trgm",
            "idx_trials_name_trgm",
            "idx_studies_name_trgm",
        }
        missing = expected - found
        assert not missing, f"Missing GIN indexes: {missing}"
