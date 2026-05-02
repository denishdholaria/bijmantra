"""Add PostGIS GIST indexes on geometry columns and spatial utility functions.

Revision ID: 20260423_1000
Revises: 20260423_0900
Create Date: 2026-04-23 10:00:00.000000

Tasks 8.1, 8.2, 8.3:
  - GIST index on iot_devices.coordinates (Geometry POINT, SRID 4326)
  - GIST index on locations.coordinates (Geometry POINT, SRID 4326)
  - SQL function find_nearest_devices(lat, lon, radius_km, max_results)
  - SQL function find_nearest_locations(lat, lon, radius_km, max_results)

Why GIST for geometry?
  GIST (Generalized Search Tree) is the standard index type for PostGIS
  geometry columns. It supports spatial operators like ST_DWithin, ST_Intersects,
  and ST_Contains efficiently. GIN is not suitable for geometry types.

Why CONCURRENTLY?
  CREATE INDEX CONCURRENTLY builds the index without holding a table lock,
  allowing reads and writes to continue during the build. This is essential
  for production tables that may already contain data.

  IMPORTANT: CREATE INDEX CONCURRENTLY cannot run inside a transaction block.
  This migration commits the implicit Alembic transaction before executing
  the index creation statements, mirroring the pattern used in 20260423_0900.

Why geography cast in the SQL functions?
  ST_DWithin on geography type uses meters as the unit and accounts for
  Earth's curvature, giving accurate distance calculations globally.
  Casting coordinates::geography is safe because the SRID is already 4326
  (WGS84), which is the required SRID for geography type.

Requirement: 6.1, 6.2 (PostGIS GIST Index Hardening and Spatial Utilities)
"""

import sqlalchemy as sa
from alembic import op


revision = "20260423_1000"
down_revision = "20260423_0900"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction block.
    # Commit the implicit Alembic transaction before issuing CONCURRENTLY
    # index builds, mirroring the pattern in 20260423_0900_trgm_gin_indexes.py.
    # -------------------------------------------------------------------------
    connection = op.get_bind()
    connection.execute(sa.text("COMMIT"))

    # GIST index on iot_devices.coordinates (Point geometry, SRID 4326)
    connection.execute(sa.text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_iot_devices_coordinates_gist
        ON iot_devices USING GIST (coordinates)
    """))

    # GIST index on locations.coordinates (Point geometry, SRID 4326)
    connection.execute(sa.text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_locations_coordinates_gist
        ON locations USING GIST (coordinates)
    """))

    # -------------------------------------------------------------------------
    # SQL functions must be created outside the CONCURRENTLY context.
    # op.execute() is fine here — functions don't require CONCURRENTLY.
    # -------------------------------------------------------------------------

    # Create find_nearest_devices SQL function
    op.execute("""
        CREATE OR REPLACE FUNCTION find_nearest_devices(
            p_lat double precision,
            p_lon double precision,
            p_radius_km double precision,
            p_max_results integer DEFAULT 10
        )
        RETURNS TABLE(
            device_id integer,
            device_name text,
            distance_km double precision
        ) AS $$
            SELECT
                id AS device_id,
                name AS device_name,
                ST_Distance(
                    coordinates::geography,
                    ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
                ) / 1000.0 AS distance_km
            FROM iot_devices
            WHERE
                coordinates IS NOT NULL
                AND ST_DWithin(
                    coordinates::geography,
                    ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
                    p_radius_km * 1000.0
                )
            ORDER BY distance_km
            LIMIT p_max_results;
        $$ LANGUAGE sql STABLE;
    """)

    # Create find_nearest_locations SQL function
    op.execute("""
        CREATE OR REPLACE FUNCTION find_nearest_locations(
            p_lat double precision,
            p_lon double precision,
            p_radius_km double precision,
            p_max_results integer DEFAULT 10
        )
        RETURNS TABLE(
            location_id integer,
            location_name text,
            distance_km double precision
        ) AS $$
            SELECT
                id AS location_id,
                location_name,
                ST_Distance(
                    coordinates::geography,
                    ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
                ) / 1000.0 AS distance_km
            FROM locations
            WHERE
                coordinates IS NOT NULL
                AND ST_DWithin(
                    coordinates::geography,
                    ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
                    p_radius_km * 1000.0
                )
            ORDER BY distance_km
            LIMIT p_max_results;
        $$ LANGUAGE sql STABLE;
    """)


def downgrade() -> None:
    # Drop SQL functions first (no transaction restriction)
    op.execute(
        "DROP FUNCTION IF EXISTS find_nearest_locations"
        "(double precision, double precision, double precision, integer)"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS find_nearest_devices"
        "(double precision, double precision, double precision, integer)"
    )

    # DROP INDEX CONCURRENTLY also cannot run inside a transaction block.
    connection = op.get_bind()
    connection.execute(sa.text("COMMIT"))
    connection.execute(sa.text(
        "DROP INDEX CONCURRENTLY IF EXISTS idx_locations_coordinates_gist"
    ))
    connection.execute(sa.text(
        "DROP INDEX CONCURRENTLY IF EXISTS idx_iot_devices_coordinates_gist"
    ))
