"""Fix datetime columns to use timezone

All created_at and updated_at columns need to be TIMESTAMP WITH TIME ZONE
to work correctly with asyncpg and timezone-aware Python datetimes.

Revision ID: 028
Revises: 027
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None


# All tables that inherit from BaseModel and have created_at/updated_at
TABLES_WITH_TIMESTAMPS = [
    'organizations',
    'users',
    'programs',
    'locations',
    'trials',
    'studies',
    'persons',
    'seasons',
    'ontologies',
    'lists',
    'germplasm',
    'crosses',
    'seedlots',
    'breeding_methods',
    'traits',
    'methods',
    'scales',
    'observation_variables',
    'observations',
    'images',
    'samples',
    'plates',
    'calls',
    'variants',
    'genome_maps',
    'marker_positions',
    'references',
    'allele_matrices',
    'vendor_orders',
    'events',
    'observation_units',
    'iot_devices',
    'iot_sensors',
    'iot_telemetry',
    'iot_alert_rules',
    'iot_alert_events',
    'iot_aggregates',
    'iot_environment_links',
    'system_settings',
    'roles',
    'user_roles',
    'notifications',
    'notification_preferences',
    'quiet_hours',
    'user_profiles',
    'user_preferences',
    'user_sessions',
    'teams',
    'team_members',
    'activity_logs',
    'workspaces',
    'workspace_members',
    'tasks',
    'reports',
    'sync_items',
    'validation_rules',
    'backups',
    'trial_health',
    'field_book_studies',
    'diseases',
    'resistance_genes',
    'pyramiding_strategies',
    'user_dock_preferences',
    # Add any other tables that have created_at/updated_at
]


def upgrade():
    """Convert all timestamp columns to timezone-aware"""
    bind = op.get_bind()
    preparer = bind.dialect.identifier_preparer

    # core.organizations/core.users are simple compatibility views over the
    # public tables. PostgreSQL cannot alter a column type while a view depends
    # on that column, so drop and recreate these views around the conversion.
    bind.execute(sa.text("DROP VIEW IF EXISTS core.organizations"))
    bind.execute(sa.text("DROP VIEW IF EXISTS core.users"))

    for table in TABLES_WITH_TIMESTAMPS:
        converted = []
        for column in ("created_at", "updated_at"):
            if not _column_needs_timezone(bind, table, column):
                continue

            try:
                quoted_table = preparer.quote(table)
                quoted_column = preparer.quote(column)
                with bind.begin_nested():
                    bind.execute(sa.text(f"""
                        ALTER TABLE {quoted_table}
                        ALTER COLUMN {quoted_column} TYPE TIMESTAMP WITH TIME ZONE
                        USING {quoted_column} AT TIME ZONE 'UTC'
                    """))
                converted.append(column)
            except Exception as e:
                # Keep Alembic's outer transaction usable if one legacy table
                # is missing or blocked by a dependency.
                print(f"⚠ Skipped {table}.{column}: {e}")

        if converted:
            print(f"✓ Fixed timestamps for {table}")

    bind.execute(sa.text("""
        CREATE OR REPLACE VIEW core.organizations AS
        SELECT * FROM public.organizations
    """))
    bind.execute(sa.text("""
        CREATE OR REPLACE VIEW core.users AS
        SELECT * FROM public.users
    """))


def _column_needs_timezone(bind, table, column):
    """Return True when a public table column exists and is not timestamptz."""
    result = bind.execute(
        sa.text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table
              AND column_name = :column
        """),
        {"table": table, "column": column},
    ).scalar()
    return result is not None and result != "timestamp with time zone"


def downgrade():
    """Convert back to timezone-naive (not recommended)"""
    for table in TABLES_WITH_TIMESTAMPS:
        try:
            op.execute(f'''
                ALTER TABLE {table} 
                ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
            ''')
            op.execute(f'''
                ALTER TABLE {table} 
                ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE
            ''')
        except Exception:
            pass
