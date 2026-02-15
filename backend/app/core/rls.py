"""
Row-Level Security (RLS) for Multi-Tenant Isolation

This module provides PostgreSQL RLS policies for tenant isolation.
RLS ensures data isolation at the database level, providing defense-in-depth
even if application code has bugs.

Architecture:
1. Each request sets a session variable: app.current_organization_id
2. RLS policies filter rows based on this variable
3. Superusers can bypass RLS for admin operations

Usage:
    # In your endpoint, after authentication:
    await set_tenant_context(db, user.organization_id)
    
    # All subsequent queries will be filtered by organization_id
    results = await db.execute(select(Program))  # Only returns org's programs
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


# Tables that have organization_id and need RLS
# Updated: 2026-01-13 (Session 79 - Future Modules Migration 029)
# Evidence: 103 tables with RLS enabled (87 existing + 16 new future module tables)
RLS_ENABLED_TABLES = [
    # Core BrAPI tables (migration 006)
    "organizations",
    "programs",
    "trials",
    "studies",
    "locations",
    "people",
    "users",
    
    # Seed Bank tables (migration 007)
    "seed_bank_vaults",
    "seed_bank_accessions",
    "seed_bank_viability_tests",
    "seed_bank_regeneration_tasks",
    "seed_bank_exchanges",
    
    # Germplasm domain (migration 023)
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
    
    # Phenotyping domain (migration 023)
    "traits",
    "methods",
    "scales",
    "observation_variables",
    "observation_units",
    "observation_levels",
    "observations",
    "images",
    
    # Genotyping domain (migration 023)
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
    
    # User management (migration 023)
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
    
    # IoT/Sensors (migration 023)
    "iot_devices",
    "iot_alert_rules",
    
    # Data management (migration 023)
    "validation_rules",
    "validation_issues",
    "validation_runs",
    "backups",
    "trial_health",
    "health_alerts",
    
    # Collaboration (migration 023)
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
    
    # Field operations (migration 023)
    "field_book_studies",
    "field_book_traits",
    "field_book_entries",
    "field_book_observations",
    "events",
    
    # Stress resistance (migration 023)
    "abiotic_stresses",
    "diseases",
    "resistance_genes",
    "tolerance_genes",
    "pyramiding_strategies",
    
    # Nursery (migration 023)
    "nursery_locations",
    "seedling_batches",
    
    # Other (migration 023)
    "lists",
    "ontologies",
    "seasons",
    "vendor_orders",
    
    # Future Modules - Tier 1 (migration 029)
    # Crop Intelligence
    "growing_degree_day_logs",
    "crop_calendars",
    "crop_suitabilities",
    "yield_predictions",
    # Soil & Nutrients
    "soil_tests",
    "fertilizer_recommendations",
    "soil_health_scores",
    "carbon_sequestration",
    # Water & Irrigation
    "fields",
    "water_balances",
    "irrigation_schedules",
    "soil_moisture_readings",
    # Crop Protection
    "disease_risk_forecasts",
    "spray_applications",
    "pest_observations",
    "ipm_strategies",
    
    # Dispatch & Firms (migration 030)
    "firms",
    "dispatches",
    
    # DUS Testing (migration 031)
    "dus_trials",
    
    # Doubled Haploid (migration 032)
    "dh_protocols",
    "dh_batches",
    
    # Phenomic Selection (migration 033)
    "phenomic_datasets",
    "phenomic_models",
    
    # Space Research (migration 034)
    "space_crops",
    "space_experiments",
    
    # Bio-Analytics (migration 035)
    "bio_gs_models",
    "bio_marker_effects",
    "bio_gebv_predictions",
    "bio_gwas_runs",
    "bio_gwas_results",
]


async def set_tenant_context(
    db: AsyncSession,
    organization_id: Optional[int],
    is_superuser: bool = False
) -> None:
    """
    Set the current tenant context for RLS policies.
    
    This sets a PostgreSQL session variable that RLS policies use
    to filter rows. Must be called at the start of each request.
    
    Args:
        db: Database session
        organization_id: The organization ID to filter by
        is_superuser: If True, bypasses RLS (sets org_id to 0)
    """
    if is_superuser:
        # Superusers see all data (org_id = 0 means bypass)
        org_id = 0
    elif organization_id:
        org_id = organization_id
    else:
        # No org context - will see nothing (safe default)
        org_id = -1
    
    # Note: org_id is always an integer, safe to format
    await db.execute(
        text(f"SET LOCAL app.current_organization_id = '{int(org_id)}'")
    )
    logger.debug(f"Set tenant context: organization_id={org_id}, is_superuser={is_superuser}")


async def clear_tenant_context(db: AsyncSession) -> None:
    """
    Clear the tenant context (reset to default).
    
    This is typically called at the end of a request or on error.
    """
    await db.execute(text("RESET app.current_organization_id"))


async def get_current_tenant(db: AsyncSession) -> Optional[int]:
    """
    Get the current tenant context from the session.
    
    Returns:
        The current organization_id, or None if not set
    """
    result = await db.execute(
        text("SELECT current_setting('app.current_organization_id', true)")
    )
    value = result.scalar()
    if value and value not in ('', '-1'):
        return int(value)
    return None


def generate_rls_policy_sql(table_name: str) -> str:
    """
    Generate SQL to create RLS policy for a table.
    
    The policy:
    1. Enables RLS on the table
    2. Creates a policy that filters by organization_id
    3. Allows superusers (org_id = 0) to see all rows
    4. Allows users to see only their organization's rows
    
    Args:
        table_name: Name of the table to create policy for
        
    Returns:
        SQL string to execute
    """
    return f"""
-- Enable RLS on {table_name}
ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;

-- Force RLS for table owner too (important for security)
ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;

-- Drop existing policy if exists
DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name};

-- Create tenant isolation policy
-- org_id = 0 means superuser (bypass RLS)
-- org_id = -1 means no context (see nothing)
-- Otherwise, filter by organization_id
CREATE POLICY {table_name}_tenant_isolation ON {table_name}
    FOR ALL
    USING (
        COALESCE(current_setting('app.current_organization_id', true), '-1')::integer = 0
        OR organization_id = COALESCE(current_setting('app.current_organization_id', true), '-1')::integer
    )
    WITH CHECK (
        COALESCE(current_setting('app.current_organization_id', true), '-1')::integer = 0
        OR organization_id = COALESCE(current_setting('app.current_organization_id', true), '-1')::integer
    );

-- Grant usage to application role
-- (Assumes bijmantra_user is the application database user)
"""


def generate_all_rls_policies_sql() -> str:
    """
    Generate SQL to create RLS policies for all tenant-aware tables.
    
    Returns:
        Complete SQL script for all RLS policies
    """
    sql_parts = [
        "-- Row-Level Security Policies for Multi-Tenant Isolation",
        "-- Generated by Bijmantra RLS module",
        "",
        "-- Create helper function to get current organization",
        """
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
""",
        "",
    ]
    
    for table in RLS_ENABLED_TABLES:
        sql_parts.append(f"-- RLS for {table}")
        sql_parts.append(generate_rls_policy_sql(table))
        sql_parts.append("")
    
    return "\n".join(sql_parts)


def generate_disable_rls_sql() -> str:
    """
    Generate SQL to disable RLS on all tables (for testing/migration).
    
    Returns:
        SQL script to disable all RLS policies
    """
    sql_parts = ["-- Disable RLS on all tenant-aware tables"]
    
    for table in RLS_ENABLED_TABLES:
        sql_parts.append(f"""
DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};
ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
""")
    
    return "\n".join(sql_parts)


# SQL for the migration
RLS_MIGRATION_SQL = """
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
        current_organization_id() = 0  -- Superuser sees all
        OR id = current_organization_id()  -- Users see only their org
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
-- Seed Bank Tables RLS
-- ============================================

-- Seed Bank Vaults
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

-- Seed Bank Accessions
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

-- Seed Bank Viability Tests
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

-- Seed Bank Regeneration Tasks
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

-- Seed Bank Exchanges
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

-- ============================================
-- Create index for RLS performance
-- ============================================

-- Ensure organization_id columns are indexed for RLS performance
CREATE INDEX IF NOT EXISTS idx_programs_org_id ON programs(organization_id);
CREATE INDEX IF NOT EXISTS idx_trials_org_id ON trials(organization_id);
CREATE INDEX IF NOT EXISTS idx_studies_org_id ON studies(organization_id);
CREATE INDEX IF NOT EXISTS idx_locations_org_id ON locations(organization_id);
CREATE INDEX IF NOT EXISTS idx_people_org_id ON people(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(organization_id);
"""

RLS_DOWNGRADE_SQL = """
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

-- Drop helper function
DROP FUNCTION IF EXISTS current_organization_id();
"""
