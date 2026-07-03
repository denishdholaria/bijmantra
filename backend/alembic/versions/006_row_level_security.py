"""Row-Level Security for Multi-Tenant Isolation

Revision ID: 006_row_level_security
Revises: 005_security_audit_tables
Create Date: 2025-12-12

This migration enables PostgreSQL Row-Level Security (RLS) on all
tenant-aware tables. RLS provides database-level enforcement of
multi-tenant isolation, ensuring data security even if application
code has bugs.

How it works:
1. Application sets session variable: SET LOCAL app.current_organization_id = X
2. RLS policies filter all queries by organization_id
3. Superusers (org_id = 0) bypass RLS for admin operations
4. No context (org_id = -1) sees nothing (safe default)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_row_level_security'
down_revision = '005_security_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable Row-Level Security on all tenant-aware tables."""
    
    # Execute RLS setup SQL
    op.execute("""
-- ============================================
-- Row-Level Security for Multi-Tenant Isolation
-- ============================================

-- Helper function to safely get current organization
CREATE OR REPLACE FUNCTION current_organization_id() 
RETURNS INTEGER AS $$
BEGIN
    RETURN COALESCE(
        NULLIF(current_setting('app.current_organization_id', true), '')::integer,
        -1
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN -1;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================
-- Core Tables RLS
-- ============================================

-- Organizations table (special case - users see only their own org)
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS organizations_tenant_isolation ON organizations;
CREATE POLICY organizations_tenant_isolation ON organizations
    FOR ALL
    USING (
        current_organization_id() = 0
        OR id = current_organization_id()
    );

-- Users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS users_tenant_isolation ON users;
CREATE POLICY users_tenant_isolation ON users
    FOR ALL
    USING (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    );

-- Programs table
ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE programs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS programs_tenant_isolation ON programs;
CREATE POLICY programs_tenant_isolation ON programs
    FOR ALL
    USING (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    );

-- Trials table
ALTER TABLE trials ENABLE ROW LEVEL SECURITY;
ALTER TABLE trials FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS trials_tenant_isolation ON trials;
CREATE POLICY trials_tenant_isolation ON trials
    FOR ALL
    USING (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    );

-- Studies table
ALTER TABLE studies ENABLE ROW LEVEL SECURITY;
ALTER TABLE studies FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS studies_tenant_isolation ON studies;
CREATE POLICY studies_tenant_isolation ON studies
    FOR ALL
    USING (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    );

-- Locations table
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS locations_tenant_isolation ON locations;
CREATE POLICY locations_tenant_isolation ON locations
    FOR ALL
    USING (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    );

-- People table
ALTER TABLE people ENABLE ROW LEVEL SECURITY;
ALTER TABLE people FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS people_tenant_isolation ON people;
CREATE POLICY people_tenant_isolation ON people
    FOR ALL
    USING (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    )
    WITH CHECK (
        current_organization_id() = 0
        OR organization_id = current_organization_id()
    );

-- ============================================
-- Seed Bank Tables RLS (conditional)
-- ============================================

-- Note: Seed Bank tables use UUID for organization_id, so we skip RLS for now
-- They need to be migrated to use INTEGER organization_id first
-- DO $$ 
-- BEGIN
--     IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_vaults') THEN
--         ALTER TABLE seed_bank_vaults ENABLE ROW LEVEL SECURITY;
--         ALTER TABLE seed_bank_vaults FORCE ROW LEVEL SECURITY;
--         DROP POLICY IF EXISTS seed_bank_vaults_tenant_isolation ON seed_bank_vaults;
--         CREATE POLICY seed_bank_vaults_tenant_isolation ON seed_bank_vaults
--             FOR ALL
--             USING (current_organization_id() = 0 OR organization_id::text = current_organization_id()::text)
--             WITH CHECK (current_organization_id() = 0 OR organization_id::text = current_organization_id()::text);
--     END IF;
-- END $$;

-- Note: Remaining seed bank tables also use UUID, skipping for now
-- DO $$ 
-- BEGIN
--     IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_accessions') THEN
--         ALTER TABLE seed_bank_accessions ENABLE ROW LEVEL SECURITY;
--         ...
--     END IF;
-- END $$;

-- ============================================
-- Performance Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_programs_org_id ON programs(organization_id);
CREATE INDEX IF NOT EXISTS idx_trials_org_id ON trials(organization_id);
CREATE INDEX IF NOT EXISTS idx_studies_org_id ON studies(organization_id);
CREATE INDEX IF NOT EXISTS idx_locations_org_id ON locations(organization_id);
CREATE INDEX IF NOT EXISTS idx_people_org_id ON people(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(organization_id);
    """)


def downgrade() -> None:
    """Disable Row-Level Security on all tables."""
    
    op.execute("""
-- Disable RLS on all tables

-- Core tables
ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS organizations_tenant_isolation ON organizations;

ALTER TABLE users DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS users_tenant_isolation ON users;

ALTER TABLE programs DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS programs_tenant_isolation ON programs;

ALTER TABLE trials DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS trials_tenant_isolation ON trials;

ALTER TABLE studies DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS studies_tenant_isolation ON studies;

ALTER TABLE locations DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS locations_tenant_isolation ON locations;

ALTER TABLE people DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS people_tenant_isolation ON people;

-- Seed Bank tables (if exist)
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_vaults') THEN
        ALTER TABLE seed_bank_vaults DISABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS seed_bank_vaults_tenant_isolation ON seed_bank_vaults;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_accessions') THEN
        ALTER TABLE seed_bank_accessions DISABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS seed_bank_accessions_tenant_isolation ON seed_bank_accessions;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_viability_tests') THEN
        ALTER TABLE seed_bank_viability_tests DISABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS seed_bank_viability_tests_tenant_isolation ON seed_bank_viability_tests;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_regeneration_tasks') THEN
        ALTER TABLE seed_bank_regeneration_tasks DISABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS seed_bank_regeneration_tasks_tenant_isolation ON seed_bank_regeneration_tasks;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_exchanges') THEN
        ALTER TABLE seed_bank_exchanges DISABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS seed_bank_exchanges_tenant_isolation ON seed_bank_exchanges;
    END IF;
END $$;

-- Drop indexes
DROP INDEX IF EXISTS idx_programs_org_id;
DROP INDEX IF EXISTS idx_trials_org_id;
DROP INDEX IF EXISTS idx_studies_org_id;
DROP INDEX IF EXISTS idx_locations_org_id;
DROP INDEX IF EXISTS idx_people_org_id;
DROP INDEX IF EXISTS idx_users_org_id;

-- Drop helper function
DROP FUNCTION IF EXISTS current_organization_id();
    """)
