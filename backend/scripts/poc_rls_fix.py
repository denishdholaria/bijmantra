#!/usr/bin/env python3
"""
Project VAJRA: RLS/View Migration POC Script

This script demonstrates the "Pause → Migrate → Restore" strategy
for safely migrating PostgreSQL tables that have RLS views and policies.

IMPORTANT: This is a PROOF-OF-CONCEPT. It does NOT execute actual migrations.
           Use this to understand the pattern before integrating into Alembic.

Author: Principal Architect (Claude Opus 4.5)
Date: 2026-02-02
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RLSBackupRecord:
    """Represents a backed-up RLS object (view or policy)."""
    object_type: str  # 'view' or 'policy'
    object_name: str
    schema_name: str
    definition: str
    table_name: Optional[str] = None


# =============================================================================
# SQL Templates for Copy-Paste into Alembic Migrations
# =============================================================================

PAUSE_RLS_VIEWS_SQL = """
-- STEP 1: Create temporary backup table
CREATE TEMP TABLE IF NOT EXISTS _rls_migration_backup (
    id SERIAL PRIMARY KEY,
    object_type TEXT NOT NULL,
    object_name TEXT NOT NULL,
    schema_name TEXT NOT NULL,
    table_name TEXT,
    full_definition TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- STEP 2: Backup views that depend on the target table
INSERT INTO _rls_migration_backup (object_type, object_name, schema_name, full_definition)
SELECT 
    'view',
    c.relname,
    n.nspname,
    pg_get_viewdef(c.oid, true)
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_depend d ON d.refobjid = c.oid
JOIN pg_class dep ON dep.oid = d.objid
WHERE c.relkind = 'v'
AND dep.relname = '{target_table}'
AND n.nspname NOT IN ('pg_catalog', 'information_schema');

-- STEP 3: Backup RLS policies on the target table
INSERT INTO _rls_migration_backup (object_type, object_name, schema_name, table_name, full_definition)
SELECT 
    'policy',
    pol.polname,
    nsp.nspname,
    cls.relname,
    format(
        'CREATE POLICY %I ON %I.%I FOR %s USING (%s) WITH CHECK (%s)',
        pol.polname,
        nsp.nspname,
        cls.relname,
        CASE pol.polcmd 
            WHEN 'r' THEN 'SELECT'
            WHEN 'a' THEN 'INSERT'
            WHEN 'w' THEN 'UPDATE'
            WHEN 'd' THEN 'DELETE'
            WHEN '*' THEN 'ALL'
        END,
        pg_get_expr(pol.polqual, pol.polrelid),
        COALESCE(pg_get_expr(pol.polwithcheck, pol.polrelid), 'true')
    )
FROM pg_policy pol
JOIN pg_class cls ON cls.oid = pol.polrelid
JOIN pg_namespace nsp ON nsp.oid = cls.relnamespace
WHERE cls.relname = '{target_table}';

-- STEP 4: Drop policies first (they depend on the table)
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT object_name, table_name, schema_name 
        FROM _rls_migration_backup 
        WHERE object_type = 'policy'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', 
                      rec.object_name, rec.schema_name, rec.table_name);
    END LOOP;
END $$;

-- STEP 5: Drop dependent views
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT object_name, schema_name 
        FROM _rls_migration_backup 
        WHERE object_type = 'view'
        ORDER BY id DESC  -- Drop in reverse order of creation
    LOOP
        EXECUTE format('DROP VIEW IF EXISTS %I.%I CASCADE', 
                      rec.schema_name, rec.object_name);
    END LOOP;
END $$;
"""

RESTORE_RLS_VIEWS_SQL = """
-- STEP 6: Restore views first
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT object_name, schema_name, full_definition 
        FROM _rls_migration_backup 
        WHERE object_type = 'view'
        ORDER BY id ASC  -- Restore in original order
    LOOP
        EXECUTE format('CREATE OR REPLACE VIEW %I.%I AS %s', 
                      rec.schema_name, rec.object_name, rec.full_definition);
    END LOOP;
END $$;

-- STEP 7: Restore policies
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT full_definition 
        FROM _rls_migration_backup 
        WHERE object_type = 'policy'
    LOOP
        EXECUTE rec.full_definition;
    END LOOP;
END $$;

-- STEP 8: Cleanup
DROP TABLE IF EXISTS _rls_migration_backup;
"""


# =============================================================================
# POC Functions (Simulation Only)
# =============================================================================

def simulate_migration(target_table: str = "users") -> None:
    """
    Simulates the RLS migration workflow.
    
    This function prints the SQL that WOULD be executed, without connecting
    to any database. Use this to understand the pattern.
    """
    print("=" * 70)
    print(f"  PROJECT VAJRA: RLS Migration Simulation for '{target_table}'")
    print("=" * 70)
    print()
    
    print("PHASE 1: PAUSE (Backup and Drop)")
    print("-" * 40)
    print(PAUSE_RLS_VIEWS_SQL.format(target_table=target_table))
    print()
    
    print("PHASE 2: MIGRATE (Your Schema Change)")
    print("-" * 40)
    print(f"""
-- Example: Add a new column to {target_table}
ALTER TABLE {target_table} ADD COLUMN new_field VARCHAR(255);

-- Example: Modify column type
-- ALTER TABLE {target_table} ALTER COLUMN existing_field TYPE TEXT;
""")
    print()
    
    print("PHASE 3: RESTORE (Recreate Views and Policies)")
    print("-" * 40)
    print(RESTORE_RLS_VIEWS_SQL)
    print()
    
    print("=" * 70)
    print("  SIMULATION COMPLETE - No actual changes were made")
    print("=" * 70)


def generate_alembic_template(target_table: str = "users") -> str:
    """
    Generates a ready-to-use Alembic migration template.
    
    Returns:
        str: Python code for an Alembic migration file.
    """
    return f'''"""RLS-Safe migration for {target_table} table

Revision ID: xxx_rls_safe_{target_table}
Revises: <previous_revision>
Create Date: 2026-02-02

Uses VAJRA Pause-Migrate-Restore pattern.
See: docs/adr/ADR-002-RLS-Migration-Strategy.md
"""

from alembic import op
import sqlalchemy as sa


revision = 'xxx_rls_safe_{target_table}'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply schema changes with RLS preservation."""
    
    # PHASE 1: Pause RLS views and policies
    op.execute("""
{PAUSE_RLS_VIEWS_SQL.format(target_table=target_table)}
    """)
    
    # PHASE 2: Your actual schema change
    op.add_column('{target_table}', sa.Column('new_field', sa.String(255)))
    
    # PHASE 3: Restore RLS views and policies
    op.execute("""
{RESTORE_RLS_VIEWS_SQL}
    """)


def downgrade() -> None:
    """Reverse the schema changes."""
    
    # PHASE 1: Pause RLS views and policies
    op.execute("""
{PAUSE_RLS_VIEWS_SQL.format(target_table=target_table)}
    """)
    
    # PHASE 2: Reverse the schema change
    op.drop_column('{target_table}', 'new_field')
    
    # PHASE 3: Restore RLS views and policies
    op.execute("""
{RESTORE_RLS_VIEWS_SQL}
    """)
'''


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    import sys
    
    table = sys.argv[1] if len(sys.argv) > 1 else "users"
    
    print()
    simulate_migration(table)
    print()
    print("To generate an Alembic template, run:")
    print(f"  python {__file__} {table} --template")
    
    if len(sys.argv) > 2 and sys.argv[2] == "--template":
        print()
        print("=" * 70)
        print("  ALEMBIC TEMPLATE")
        print("=" * 70)
        print(generate_alembic_template(table))
