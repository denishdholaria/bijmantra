"""Convert iot_connectivity_logs and growing_degree_day_logs to TimescaleDB hypertables.

Revision ID: 20260423_0600
Revises: 20260423_0500
Create Date: 2026-04-23 06:00:00.000000

Task 5.1: Convert iot_connectivity_logs to hypertable (7-day chunks, 30-day retention,
          compression after 14 days segmented by device_id).

Task 5.2: Convert growing_degree_day_logs to hypertable (30-day chunks, 365-day retention).
          The log_date column is a Date type — TimescaleDB 2.x supports Date columns directly
          via create_hypertable. No compression policy is added because the table has daily
          granularity and low volume.
"""

from alembic import op


revision = "20260423_0600"
down_revision = "20260423_0500"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # iot_connectivity_logs
    # -------------------------------------------------------------------------

    # Step 1: Convert to hypertable — 7-day chunks, preserve existing rows
    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('public.iot_connectivity_logs') IS NOT NULL THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint c
                    JOIN pg_attribute a
                      ON a.attrelid = c.conrelid
                     AND a.attnum = ANY(c.conkey)
                    WHERE c.conrelid = 'public.iot_connectivity_logs'::regclass
                      AND c.contype = 'p'
                      AND a.attname = 'timestamp'
                ) THEN
                    ALTER TABLE iot_connectivity_logs DROP CONSTRAINT IF EXISTS iot_connectivity_logs_pkey;
                    ALTER TABLE iot_connectivity_logs ADD CONSTRAINT iot_connectivity_logs_pkey PRIMARY KEY (id, timestamp);
                END IF;

                PERFORM create_hypertable(
                    'iot_connectivity_logs',
                    'timestamp',
                    chunk_time_interval => INTERVAL '7 days',
                    migrate_data => true,
                    if_not_exists => true
                );

                ALTER TABLE iot_connectivity_logs SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'device_id',
                    timescaledb.compress_orderby = 'timestamp DESC'
                );

                PERFORM add_compression_policy('iot_connectivity_logs', INTERVAL '14 days', if_not_exists => true);
                PERFORM add_retention_policy('iot_connectivity_logs', INTERVAL '30 days', if_not_exists => true);
            END IF;
        END $$;
    """)

    # -------------------------------------------------------------------------
    # growing_degree_day_logs
    # -------------------------------------------------------------------------
    # Volume justification: daily GDD records accumulate ~365 rows/field/year.
    # At scale (thousands of fields over multiple seasons) this becomes a
    # significant table. Hypertable partitioning enables efficient date-range
    # queries and automatic retention without application-level cleanup.
    #
    # log_date is a Date column. TimescaleDB 2.x supports Date columns directly
    # as the partitioning dimension — no cast to timestamptz is required.

    # Step 5: Convert to hypertable — 30-day chunks, preserve existing rows
    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('public.growing_degree_day_logs') IS NOT NULL THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint c
                    JOIN pg_attribute a
                      ON a.attrelid = c.conrelid
                     AND a.attnum = ANY(c.conkey)
                    WHERE c.conrelid = 'public.growing_degree_day_logs'::regclass
                      AND c.contype = 'p'
                      AND a.attname = 'log_date'
                ) THEN
                    ALTER TABLE growing_degree_day_logs DROP CONSTRAINT IF EXISTS growing_degree_day_logs_pkey;
                    ALTER TABLE growing_degree_day_logs ADD CONSTRAINT growing_degree_day_logs_pkey PRIMARY KEY (id, log_date);
                END IF;

                PERFORM create_hypertable(
                    'growing_degree_day_logs',
                    'log_date',
                    chunk_time_interval => INTERVAL '30 days',
                    migrate_data => true,
                    if_not_exists => true
                );

                PERFORM add_retention_policy('growing_degree_day_logs', INTERVAL '365 days', if_not_exists => true);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # -------------------------------------------------------------------------
    # growing_degree_day_logs — reverse in LIFO order
    # -------------------------------------------------------------------------
    op.execute("SELECT remove_retention_policy('growing_degree_day_logs', if_not_exists => true)")
    op.execute("SELECT revert_hypertable_to_table('growing_degree_day_logs')")

    # -------------------------------------------------------------------------
    # iot_connectivity_logs
    # -------------------------------------------------------------------------
    op.execute("SELECT remove_retention_policy('iot_connectivity_logs', if_not_exists => true)")
    op.execute("SELECT remove_compression_policy('iot_connectivity_logs', if_not_exists => true)")

    # Decompress all chunks before reverting — revert_hypertable_to_table
    # requires no compressed chunks to be present.
    op.execute("SELECT decompress_chunk(c) FROM show_chunks('iot_connectivity_logs') c")

    op.execute("SELECT revert_hypertable_to_table('iot_connectivity_logs')")
