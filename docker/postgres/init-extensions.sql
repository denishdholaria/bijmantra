-- Initialize PostgreSQL extensions for Bijmantra
-- Runs automatically on first container start
--
-- NOTE: pgaudit is NOT created here because it requires shared_preload_libraries
-- to be set before PostgreSQL starts. It is enabled by Alembic migration
-- 20260423_0300_enable_pgaudit.py after the server is running with the correct
-- SPILO_CONFIGURATION (which sets shared_preload_libraries = 'timescaledb,pgaudit').

-- Time-series optimization for IoT telemetry (must be loaded first)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Vector similarity search for Veena AI
CREATE EXTENSION IF NOT EXISTS vector;

-- Spatial data for locations and IoT devices
CREATE EXTENSION IF NOT EXISTS postgis;

-- Fuzzy text matching for germplasm search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Database-level credential encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Hierarchical organization and germplasm lineage
CREATE EXTENSION IF NOT EXISTS ltree;

-- Confirm extensions are loaded
DO $$
BEGIN
    RAISE NOTICE 'Bijmantra PostgreSQL extensions initialized:';
    RAISE NOTICE '  - timescaledb for IoT time-series optimization';
    RAISE NOTICE '  - vector (pgvector) for AI embeddings (Veena)';
    RAISE NOTICE '  - postgis for spatial data and IoT device locations';
    RAISE NOTICE '  - pg_trgm for fuzzy text matching (germplasm search)';
    RAISE NOTICE '  - uuid-ossp for UUID generation';
    RAISE NOTICE '  - pgcrypto for database-level credential encryption';
    RAISE NOTICE '  - ltree for hierarchical organization and germplasm lineage';
    RAISE NOTICE '  - pgaudit will be enabled by Alembic migration 20260423_0300';
END $$;
