"""Convert iot_telemetry to TimescaleDB hypertable with compression, retention, and continuous aggregates.

Revision ID: 20260423_0500
Revises: 20260423_0400
Create Date: 2026-04-23 05:00:00.000000
"""

from alembic import op


revision = "20260423_0500"
down_revision = "20260423_0400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TimescaleDB requires every primary/unique constraint on a hypertable to
    # include the partitioning column. The original table used id-only primary
    # key, so make it compatible before create_hypertable().
    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('public.iot_telemetry') IS NOT NULL
               AND NOT EXISTS (
                   SELECT 1
                   FROM pg_constraint c
                   JOIN pg_attribute a
                     ON a.attrelid = c.conrelid
                    AND a.attnum = ANY(c.conkey)
                   WHERE c.conrelid = 'public.iot_telemetry'::regclass
                     AND c.contype = 'p'
                     AND a.attname = 'timestamp'
               ) THEN
                ALTER TABLE iot_telemetry DROP CONSTRAINT IF EXISTS iot_telemetry_pkey;
                ALTER TABLE iot_telemetry ADD CONSTRAINT iot_telemetry_pkey PRIMARY KEY (id, timestamp);
            END IF;
        END $$;
    """)

    # Step 1: Convert iot_telemetry to a TimescaleDB hypertable
    # migrate_data=true preserves existing rows
    op.execute("""
        SELECT create_hypertable(
            'iot_telemetry',
            'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            migrate_data => true,
            if_not_exists => true
        )
    """)

    # Step 2: Enable compression on the hypertable
    # segmentby device_id and sensor_id for efficient per-device queries
    # orderby timestamp DESC for optimal compression of recent data
    op.execute("""
        ALTER TABLE iot_telemetry SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'device_id, sensor_id',
            timescaledb.compress_orderby = 'timestamp DESC'
        )
    """)

    # Step 3: Add compression policy — compress chunks older than 7 days
    op.execute("""
        SELECT add_compression_policy('iot_telemetry', INTERVAL '7 days', if_not_exists => true)
    """)

    # Step 4: Add retention policy — drop data older than 90 days
    # In production, override with TIMESCALE_RETENTION_DAYS env var via a separate config
    op.execute("""
        SELECT add_retention_policy('iot_telemetry', INTERVAL '90 days', if_not_exists => true)
    """)

    # Step 5: Create hourly continuous aggregate
    op.execute("""
        CREATE MATERIALIZED VIEW iot_telemetry_hourly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 hour', timestamp) AS bucket,
            device_id,
            sensor_id,
            AVG(value) AS avg_value,
            MIN(value) AS min_value,
            MAX(value) AS max_value,
            COUNT(*) AS sample_count
        FROM iot_telemetry
        GROUP BY bucket, device_id, sensor_id
        WITH NO DATA
    """)

    # Step 6: Create daily continuous aggregate
    op.execute("""
        CREATE MATERIALIZED VIEW iot_telemetry_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket('1 day', timestamp) AS bucket,
            device_id,
            sensor_id,
            AVG(value) AS avg_value,
            MIN(value) AS min_value,
            MAX(value) AS max_value,
            COUNT(*) AS sample_count
        FROM iot_telemetry
        GROUP BY bucket, device_id, sensor_id
        WITH NO DATA
    """)

    # Step 7: Add refresh policy for hourly aggregate (1h lag)
    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'iot_telemetry_hourly',
            start_offset => INTERVAL '3 hours',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists => true
        )
    """)

    # Step 8: Add refresh policy for daily aggregate (1d lag)
    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'iot_telemetry_daily',
            start_offset => INTERVAL '3 days',
            end_offset => INTERVAL '1 day',
            schedule_interval => INTERVAL '1 day',
            if_not_exists => true
        )
    """)


def downgrade() -> None:
    # Remove refresh policies
    op.execute("SELECT remove_continuous_aggregate_policy('iot_telemetry_daily', if_not_exists => true)")
    op.execute("SELECT remove_continuous_aggregate_policy('iot_telemetry_hourly', if_not_exists => true)")

    # Drop continuous aggregates
    op.execute("DROP MATERIALIZED VIEW IF EXISTS iot_telemetry_daily CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS iot_telemetry_hourly CASCADE")

    # Remove retention policy
    op.execute("SELECT remove_retention_policy('iot_telemetry', if_not_exists => true)")

    # Remove compression policy
    op.execute("SELECT remove_compression_policy('iot_telemetry', if_not_exists => true)")

    # Decompress all chunks before converting back
    op.execute("SELECT decompress_chunk(c) FROM show_chunks('iot_telemetry') c")

    # Convert hypertable back to regular table
    # Note: This preserves all data
    # revert_hypertable_to_table was added in TimescaleDB 2.13 (bundled in timescale/timescaledb-ha:pg16-latest)
    op.execute("""
        SELECT revert_hypertable_to_table('iot_telemetry')
    """)
