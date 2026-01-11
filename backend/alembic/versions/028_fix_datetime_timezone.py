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
    for table in TABLES_WITH_TIMESTAMPS:
        try:
            # Alter created_at column
            op.execute(f'''
                ALTER TABLE {table} 
                ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
                USING created_at AT TIME ZONE 'UTC'
            ''')
            
            # Alter updated_at column
            op.execute(f'''
                ALTER TABLE {table} 
                ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE 
                USING updated_at AT TIME ZONE 'UTC'
            ''')
            
            print(f"✓ Fixed timestamps for {table}")
        except Exception as e:
            # Table might not exist or column might already be correct type
            print(f"⚠ Skipped {table}: {e}")


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
