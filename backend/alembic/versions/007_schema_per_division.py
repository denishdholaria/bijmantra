"""Schema-per-Division Architecture

Revision ID: 007_schema_per_division
Revises: 006_row_level_security
Create Date: 2025-12-12

This migration implements the Parashakti Framework's schema-per-division
architecture. Each division gets its own PostgreSQL schema for:
- Namespace isolation
- Independent evolution
- Clear ownership
- Better organization

Schemas created:
- core (organizations, users, auth)
- plant_sciences (breeding, genomics, molecular)
- seed_bank (vaults, accessions, conservation)
- earth_systems (weather, soil, field)
- commercial (traceability, licensing, DUS)
- integrations (external APIs, webhooks)

This also fixes the UUID/INTEGER inconsistency by standardizing on INTEGER
for organization_id across all tables.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '007_schema_per_division'
down_revision = '006_row_level_security'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create schema-per-division structure."""
    
    # ============================================
    # 1. Create Schemas
    # ============================================
    
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS plant_sciences")
    op.execute("CREATE SCHEMA IF NOT EXISTS seed_bank")
    op.execute("CREATE SCHEMA IF NOT EXISTS earth_systems")
    op.execute("CREATE SCHEMA IF NOT EXISTS commercial")
    op.execute("CREATE SCHEMA IF NOT EXISTS integrations")
    
    # ============================================
    # 2. Move Core Tables to core schema
    # ============================================
    
    # Organizations and Users stay in public for now (referenced by all)
    # But we'll create views in core schema
    op.execute("""
        CREATE OR REPLACE VIEW core.organizations AS 
        SELECT * FROM public.organizations
    """)
    
    op.execute("""
        CREATE OR REPLACE VIEW core.users AS 
        SELECT * FROM public.users
    """)
    
    # ============================================
    # 3. Fix Seed Bank UUID → INTEGER Migration
    # ============================================
    
    # This is the critical fix for RLS compatibility
    
    # seed_bank_vaults
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables 
                      WHERE table_name = 'seed_bank_vaults') THEN
                -- Add new INTEGER column
                ALTER TABLE seed_bank_vaults 
                ADD COLUMN IF NOT EXISTS organization_id_int INTEGER;
                
                -- For existing data, we can't auto-convert UUID to INT
                -- Set to NULL for now (will need manual data migration)
                -- In production, you'd map UUIDs to organization IDs
                
                -- Drop old UUID column
                ALTER TABLE seed_bank_vaults DROP COLUMN IF EXISTS organization_id CASCADE;
                
                -- Rename new column
                ALTER TABLE seed_bank_vaults 
                RENAME COLUMN organization_id_int TO organization_id;
                
                -- Add NOT NULL constraint (after data is populated)
                -- ALTER TABLE seed_bank_vaults ALTER COLUMN organization_id SET NOT NULL;
                
                -- Add foreign key
                ALTER TABLE seed_bank_vaults 
                ADD CONSTRAINT fk_seed_bank_vaults_org 
                FOREIGN KEY (organization_id) REFERENCES organizations(id);
                
                -- Add index
                CREATE INDEX IF NOT EXISTS idx_seed_bank_vaults_org_id 
                ON seed_bank_vaults(organization_id);
            END IF;
        END $$;
    """)
    
    # seed_bank_accessions
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables 
                      WHERE table_name = 'seed_bank_accessions') THEN
                ALTER TABLE seed_bank_accessions ADD COLUMN IF NOT EXISTS organization_id_int INTEGER;
                ALTER TABLE seed_bank_accessions DROP COLUMN IF EXISTS organization_id CASCADE;
                ALTER TABLE seed_bank_accessions RENAME COLUMN organization_id_int TO organization_id;
                ALTER TABLE seed_bank_accessions 
                ADD CONSTRAINT fk_seed_bank_accessions_org 
                FOREIGN KEY (organization_id) REFERENCES organizations(id);
                CREATE INDEX IF NOT EXISTS idx_seed_bank_accessions_org_id 
                ON seed_bank_accessions(organization_id);
            END IF;
        END $$;
    """)
    
    # seed_bank_viability_tests
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables 
                      WHERE table_name = 'seed_bank_viability_tests') THEN
                ALTER TABLE seed_bank_viability_tests ADD COLUMN IF NOT EXISTS organization_id_int INTEGER;
                ALTER TABLE seed_bank_viability_tests DROP COLUMN IF EXISTS organization_id CASCADE;
                ALTER TABLE seed_bank_viability_tests RENAME COLUMN organization_id_int TO organization_id;
                ALTER TABLE seed_bank_viability_tests 
                ADD CONSTRAINT fk_seed_bank_viability_tests_org 
                FOREIGN KEY (organization_id) REFERENCES organizations(id);
                CREATE INDEX IF NOT EXISTS idx_seed_bank_viability_tests_org_id 
                ON seed_bank_viability_tests(organization_id);
            END IF;
        END $$;
    """)
    
    # seed_bank_regeneration_tasks
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables 
                      WHERE table_name = 'seed_bank_regeneration_tasks') THEN
                ALTER TABLE seed_bank_regeneration_tasks ADD COLUMN IF NOT EXISTS organization_id_int INTEGER;
                ALTER TABLE seed_bank_regeneration_tasks DROP COLUMN IF EXISTS organization_id CASCADE;
                ALTER TABLE seed_bank_regeneration_tasks RENAME COLUMN organization_id_int TO organization_id;
                ALTER TABLE seed_bank_regeneration_tasks 
                ADD CONSTRAINT fk_seed_bank_regeneration_tasks_org 
                FOREIGN KEY (organization_id) REFERENCES organizations(id);
                CREATE INDEX IF NOT EXISTS idx_seed_bank_regeneration_tasks_org_id 
                ON seed_bank_regeneration_tasks(organization_id);
            END IF;
        END $$;
    """)
    
    # seed_bank_exchanges
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables 
                      WHERE table_name = 'seed_bank_exchanges') THEN
                ALTER TABLE seed_bank_exchanges ADD COLUMN IF NOT EXISTS organization_id_int INTEGER;
                ALTER TABLE seed_bank_exchanges DROP COLUMN IF EXISTS organization_id CASCADE;
                ALTER TABLE seed_bank_exchanges RENAME COLUMN organization_id_int TO organization_id;
                ALTER TABLE seed_bank_exchanges 
                ADD CONSTRAINT fk_seed_bank_exchanges_org 
                FOREIGN KEY (organization_id) REFERENCES organizations(id);
                CREATE INDEX IF NOT EXISTS idx_seed_bank_exchanges_org_id 
                ON seed_bank_exchanges(organization_id);
            END IF;
        END $$;
    """)
    
    # ============================================
    # 4. Enable RLS on Seed Bank Tables
    # ============================================
    
    # Now that organization_id is INTEGER, we can enable RLS
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_vaults') THEN
                ALTER TABLE seed_bank_vaults ENABLE ROW LEVEL SECURITY;
                ALTER TABLE seed_bank_vaults FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS seed_bank_vaults_tenant_isolation ON seed_bank_vaults;
                CREATE POLICY seed_bank_vaults_tenant_isolation ON seed_bank_vaults
                    FOR ALL
                    USING (current_organization_id() = 0 OR organization_id = current_organization_id())
                    WITH CHECK (current_organization_id() = 0 OR organization_id = current_organization_id());
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_accessions') THEN
                ALTER TABLE seed_bank_accessions ENABLE ROW LEVEL SECURITY;
                ALTER TABLE seed_bank_accessions FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS seed_bank_accessions_tenant_isolation ON seed_bank_accessions;
                CREATE POLICY seed_bank_accessions_tenant_isolation ON seed_bank_accessions
                    FOR ALL
                    USING (current_organization_id() = 0 OR organization_id = current_organization_id())
                    WITH CHECK (current_organization_id() = 0 OR organization_id = current_organization_id());
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_viability_tests') THEN
                ALTER TABLE seed_bank_viability_tests ENABLE ROW LEVEL SECURITY;
                ALTER TABLE seed_bank_viability_tests FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS seed_bank_viability_tests_tenant_isolation ON seed_bank_viability_tests;
                CREATE POLICY seed_bank_viability_tests_tenant_isolation ON seed_bank_viability_tests
                    FOR ALL
                    USING (current_organization_id() = 0 OR organization_id = current_organization_id())
                    WITH CHECK (current_organization_id() = 0 OR organization_id = current_organization_id());
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_regeneration_tasks') THEN
                ALTER TABLE seed_bank_regeneration_tasks ENABLE ROW LEVEL SECURITY;
                ALTER TABLE seed_bank_regeneration_tasks FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS seed_bank_regeneration_tasks_tenant_isolation ON seed_bank_regeneration_tasks;
                CREATE POLICY seed_bank_regeneration_tasks_tenant_isolation ON seed_bank_regeneration_tasks
                    FOR ALL
                    USING (current_organization_id() = 0 OR organization_id = current_organization_id())
                    WITH CHECK (current_organization_id() = 0 OR organization_id = current_organization_id());
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seed_bank_exchanges') THEN
                ALTER TABLE seed_bank_exchanges ENABLE ROW LEVEL SECURITY;
                ALTER TABLE seed_bank_exchanges FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS seed_bank_exchanges_tenant_isolation ON seed_bank_exchanges;
                CREATE POLICY seed_bank_exchanges_tenant_isolation ON seed_bank_exchanges
                    FOR ALL
                    USING (current_organization_id() = 0 OR organization_id = current_organization_id())
                    WITH CHECK (current_organization_id() = 0 OR organization_id = current_organization_id());
            END IF;
        END $$;
    """)
    
    # ============================================
    # 5. Create Schema Search Path Function
    # ============================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION set_division_search_path(division_name TEXT)
        RETURNS VOID AS $$
        BEGIN
            EXECUTE format('SET search_path TO %I, public', division_name);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # ============================================
    # 6. Grant Permissions
    # ============================================
    
    op.execute("""
        GRANT USAGE ON SCHEMA core TO bijmantra_user;
        GRANT USAGE ON SCHEMA plant_sciences TO bijmantra_user;
        GRANT USAGE ON SCHEMA seed_bank TO bijmantra_user;
        GRANT USAGE ON SCHEMA earth_systems TO bijmantra_user;
        GRANT USAGE ON SCHEMA commercial TO bijmantra_user;
        GRANT USAGE ON SCHEMA integrations TO bijmantra_user;
        
        GRANT ALL ON ALL TABLES IN SCHEMA core TO bijmantra_user;
        GRANT ALL ON ALL TABLES IN SCHEMA plant_sciences TO bijmantra_user;
        GRANT ALL ON ALL TABLES IN SCHEMA seed_bank TO bijmantra_user;
        GRANT ALL ON ALL TABLES IN SCHEMA earth_systems TO bijmantra_user;
        GRANT ALL ON ALL TABLES IN SCHEMA commercial TO bijmantra_user;
        GRANT ALL ON ALL TABLES IN SCHEMA integrations TO bijmantra_user;
    """)


def downgrade() -> None:
    """Revert schema-per-division structure."""
    
    # Disable RLS on seed bank tables
    op.execute("""
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
    """)
    
    # Note: Cannot easily revert UUID migration without data loss
    # This would require manual intervention
    
    # Drop schemas
    op.execute("DROP SCHEMA IF EXISTS integrations CASCADE")
    op.execute("DROP SCHEMA IF EXISTS commercial CASCADE")
    op.execute("DROP SCHEMA IF EXISTS earth_systems CASCADE")
    op.execute("DROP SCHEMA IF EXISTS seed_bank CASCADE")
    op.execute("DROP SCHEMA IF EXISTS plant_sciences CASCADE")
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")
    
    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS set_division_search_path(TEXT)")
