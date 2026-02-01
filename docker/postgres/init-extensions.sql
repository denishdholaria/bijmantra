-- Initialize PostgreSQL extensions for Bijmantra
-- Runs automatically on first container start

-- Vector similarity search for Veena AI
CREATE EXTENSION IF NOT EXISTS vector;

-- Spatial data for locations
CREATE EXTENSION IF NOT EXISTS postgis;

-- Fuzzy text matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Confirm extensions are loaded
DO $$
BEGIN
    RAISE NOTICE 'Bijmantra PostgreSQL extensions initialized:';
    RAISE NOTICE '  - vector (pgvector) for AI embeddings';
    RAISE NOTICE '  - postgis for spatial data';
    RAISE NOTICE '  - pg_trgm for fuzzy search';
    RAISE NOTICE '  - uuid-ossp for UUID generation';
END $$;
