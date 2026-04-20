"""Complete RLS Coverage for All Tenant-Aware Tables

Revision ID: 023
Revises: 022
Create Date: 2026-01-03

KAVACH (कवच) Security Shield - Phase 2

This migration extends Row-Level Security to ALL tables with organization_id
that were missed in the initial RLS implementation (migration 006).

Evidence (database query on 2026-01-03):
- 86 tables have organization_id column
- 12 tables already have RLS enabled
- 74 tables need RLS added

Tables already covered (migration 006/007):
- organizations, users, programs, trials, studies, locations, people
- seed_bank_vaults, seed_bank_accessions, seed_bank_viability_tests
- seed_bank_regeneration_tasks, seed_bank_exchanges
"""

from alembic import op

# revision identifiers
revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


# Tables that need RLS added (verified via database query)
# These have organization_id but RLS is not yet enabled
RLS_TABLES_TO_ADD = [
    # Germplasm domain
    "germplasm",
    "germplasm_attributes",
    "germplasm_attribute_definitions",
    "germplasm_attribute_values",
    "germplasm_collections",
    "crosses",
    "crossing_projects",
    "planned_crosses",
    "seedlots",
    "seedlot_transactions",
    "breeding_methods",
    
    # Phenotyping domain
    "traits",
    "methods",
    "scales",
    "observation_variables",
    "observation_units",
    "observation_levels",
    "observations",
    "images",
    
    # Genotyping domain
    "samples",
    "plates",
    "call_sets",
    "calls",
    "variants",
    "variant_sets",
    "references",
    "reference_sets",
    "genome_maps",
    "linkage_groups",
    "marker_positions",
    
    # User management
    "teams",
    "roles",
    "team_members",
    "team_invitations",
    "user_profiles",
    "user_preferences",
    "user_sessions",
    "notifications",
    "notification_preferences",
    "quiet_hours",
    "activity_logs",
    
    # IoT/Sensors
    "iot_devices",
    "iot_alert_rules",
    
    # Data management
    "validation_rules",
    "validation_issues",
    "validation_runs",
    "backups",
    "trial_health",
    "health_alerts",
    
    # Collaboration
    "report_templates",
    "report_schedules",
    "generated_reports",
    "collaboration_workspaces",
    "collaboration_activities",
    "collaboration_tasks",
    "collaboration_comments",
    "sync_items",
    "sync_history",
    "offline_data_cache",
    
    # Field operations
    "field_book_studies",
    "field_book_traits",
    "field_book_entries",
    "field_book_observations",
    "events",
    
    # Stress resistance
    "abiotic_stresses",
    "diseases",
    "resistance_genes",
    "tolerance_genes",
    "pyramiding_strategies",
    
    # Nursery
    "nursery_locations",
    "seedling_batches",
    
    # Other
    "lists",
    "ontologies",
    "seasons",
    "vendor_orders",
]


def upgrade() -> None:
    """Enable RLS on all remaining tenant-aware tables."""
    
    for table in RLS_TABLES_TO_ADD:
        # Use DO block to handle tables that may not exist
        # Quote table names to handle reserved keywords like 'references'
        op.execute(f"""
            DO $$ 
            BEGIN
                -- Check if table exists AND has organization_id column
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    AND column_name = 'organization_id'
                    AND table_schema = 'public'
                ) THEN
                    -- Enable RLS
                    ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY;
                    ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY;
                    
                    -- Drop existing policy if exists
                    DROP POLICY IF EXISTS {table}_tenant_isolation ON "{table}";
                    
                    -- Create tenant isolation policy
                    CREATE POLICY {table}_tenant_isolation ON "{table}"
                        FOR ALL
                        USING (
                            current_organization_id() = 0 
                            OR organization_id = current_organization_id()
                        )
                        WITH CHECK (
                            current_organization_id() = 0 
                            OR organization_id = current_organization_id()
                        );
                    
                    -- Create index for RLS performance if not exists
                    CREATE INDEX IF NOT EXISTS idx_{table}_org_id 
                    ON "{table}"(organization_id);
                    
                    RAISE NOTICE 'RLS enabled on table: {table}';
                ELSE
                    RAISE NOTICE 'Table or column does not exist, skipping: {table}';
                END IF;
            END $$;
        """)
    
    # Log completion
    op.execute("""
        DO $$ 
        BEGIN
            RAISE NOTICE 'KAVACH Phase 2 Complete: RLS enabled on all tenant-aware tables';
        END $$;
    """)


def downgrade() -> None:
    """Disable RLS on all tables added in this migration."""
    
    for table in RLS_TABLES_TO_ADD:
        op.execute(f"""
            DO $$ 
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = '{table}'
                    AND table_schema = 'public'
                ) THEN
                    -- Disable RLS
                    ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY;
                    
                    -- Drop policy
                    DROP POLICY IF EXISTS {table}_tenant_isolation ON "{table}";
                    
                    RAISE NOTICE 'RLS disabled on table: {table}';
                END IF;
            END $$;
        """)
