"""Add collaboration and reporting tables

Revision ID: 016
Revises: 015
Create Date: 2025-12-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("""
        CREATE TYPE reportformat AS ENUM ('PDF', 'Excel', 'CSV', 'PowerPoint', 'JSON');
        CREATE TYPE reportcategory AS ENUM ('trials', 'germplasm', 'breeding', 'phenotyping', 'genomics', 'inventory', 'quality');
        CREATE TYPE schedulefrequency AS ENUM ('daily', 'weekly', 'monthly', 'quarterly');
        CREATE TYPE reportstatus AS ENUM ('pending', 'generating', 'completed', 'failed', 'expired');
        CREATE TYPE schedulestatus AS ENUM ('active', 'paused', 'disabled');
        CREATE TYPE memberrole AS ENUM ('owner', 'admin', 'editor', 'viewer');
        CREATE TYPE memberstatus AS ENUM ('online', 'away', 'busy', 'offline');
        CREATE TYPE workspacetype AS ENUM ('trial', 'study', 'crossing_project', 'analysis', 'report');
        CREATE TYPE collabactivitytype AS ENUM ('created', 'updated', 'commented', 'shared', 'completed', 'assigned');
        CREATE TYPE taskstatus AS ENUM ('todo', 'in_progress', 'done');
        CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high');
        CREATE TYPE syncstatus AS ENUM ('synced', 'pending', 'conflict', 'error');
        CREATE TYPE syncaction AS ENUM ('upload', 'download', 'full_sync');
        CREATE TYPE syncentitytype AS ENUM ('observation', 'germplasm', 'trial', 'study', 'cross', 'image', 'sample');
    """)

    # Report Templates
    op.create_table(
        'report_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category', postgresql.ENUM('trials', 'germplasm', 'breeding', 'phenotyping', 'genomics', 'inventory', 'quality', name='reportcategory', create_type=False), nullable=False),
        sa.Column('formats', sa.JSON(), default=[]),
        sa.Column('parameters', sa.JSON(), default=[]),
        sa.Column('template_content', sa.Text()),
        sa.Column('last_generated', sa.DateTime()),
        sa.Column('generation_count', sa.Integer(), default=0),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_report_templates_organization_id', 'report_templates', ['organization_id'])
    op.create_index('ix_report_templates_category', 'report_templates', ['category'])

    # Report Schedules
    op.create_table(
        'report_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('schedule', postgresql.ENUM('daily', 'weekly', 'monthly', 'quarterly', name='schedulefrequency', create_type=False), nullable=False),
        sa.Column('schedule_time', sa.String(10)),
        sa.Column('schedule_day', sa.Integer()),
        sa.Column('next_run', sa.DateTime()),
        sa.Column('last_run', sa.DateTime()),
        sa.Column('recipients', sa.JSON(), default=[]),
        sa.Column('parameters', sa.JSON(), default={}),
        sa.Column('status', postgresql.ENUM('active', 'paused', 'disabled', name='schedulestatus', create_type=False), default='active'),
        sa.Column('created_by_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['template_id'], ['report_templates.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_report_schedules_organization_id', 'report_schedules', ['organization_id'])
    op.create_index('ix_report_schedules_template_id', 'report_schedules', ['template_id'])

    # Generated Reports
    op.create_table(
        'generated_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('format', postgresql.ENUM('PDF', 'Excel', 'CSV', 'PowerPoint', 'JSON', name='reportformat', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'generating', 'completed', 'failed', 'expired', name='reportstatus', create_type=False), default='pending'),
        sa.Column('size_bytes', sa.Integer(), default=0),
        sa.Column('file_path', sa.String(500)),
        sa.Column('download_url', sa.String(500)),
        sa.Column('parameters', sa.JSON(), default={}),
        sa.Column('error_message', sa.Text()),
        sa.Column('generated_by_id', sa.Integer()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['template_id'], ['report_templates.id']),
        sa.ForeignKeyConstraint(['schedule_id'], ['report_schedules.id']),
        sa.ForeignKeyConstraint(['generated_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_generated_reports_organization_id', 'generated_reports', ['organization_id'])
    op.create_index('ix_generated_reports_template_id', 'generated_reports', ['template_id'])

    # Collaboration Workspaces
    op.create_table(
        'collaboration_workspaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('type', postgresql.ENUM('trial', 'study', 'crossing_project', 'analysis', 'report', name='workspacetype', create_type=False), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.String(100)),
        sa.Column('settings', sa.JSON(), default={}),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_collaboration_workspaces_organization_id', 'collaboration_workspaces', ['organization_id'])

    # Workspace Members
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', postgresql.ENUM('owner', 'admin', 'editor', 'viewer', name='memberrole', create_type=False), default='viewer'),
        sa.Column('joined_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['collaboration_workspaces.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_member')
    )
    op.create_index('ix_workspace_members_workspace_id', 'workspace_members', ['workspace_id'])
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'])

    # User Presence
    op.create_table(
        'user_presence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('online', 'away', 'busy', 'offline', name='memberstatus', create_type=False), default='offline'),
        sa.Column('current_workspace_id', sa.Integer()),
        sa.Column('last_active', sa.DateTime()),
        sa.Column('last_heartbeat', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['current_workspace_id'], ['collaboration_workspaces.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_presence')
    )
    op.create_index('ix_user_presence_user_id', 'user_presence', ['user_id'])

    # Collaboration Activities
    op.create_table(
        'collaboration_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer()),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('activity_type', postgresql.ENUM('created', 'updated', 'commented', 'shared', 'completed', 'assigned', name='collabactivitytype', create_type=False), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('entity_name', sa.String(255)),
        sa.Column('description', sa.Text()),
        sa.Column('metadata', sa.JSON(), default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['collaboration_workspaces.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_collaboration_activities_organization_id', 'collaboration_activities', ['organization_id'])
    op.create_index('ix_collaboration_activities_workspace_id', 'collaboration_activities', ['workspace_id'])
    op.create_index('ix_collaboration_activities_user_id', 'collaboration_activities', ['user_id'])

    # Collaboration Tasks
    op.create_table(
        'collaboration_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer()),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('assignee_id', sa.Integer()),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('todo', 'in_progress', 'done', name='taskstatus', create_type=False), default='todo'),
        sa.Column('priority', postgresql.ENUM('low', 'medium', 'high', name='taskpriority', create_type=False), default='medium'),
        sa.Column('due_date', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['collaboration_workspaces.id']),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_collaboration_tasks_organization_id', 'collaboration_tasks', ['organization_id'])
    op.create_index('ix_collaboration_tasks_workspace_id', 'collaboration_tasks', ['workspace_id'])
    op.create_index('ix_collaboration_tasks_assignee_id', 'collaboration_tasks', ['assignee_id'])

    # Collaboration Comments
    op.create_table(
        'collaboration_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer()),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['collaboration_workspaces.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['collaboration_comments.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_collaboration_comments_organization_id', 'collaboration_comments', ['organization_id'])
    op.create_index('ix_collaboration_comments_entity_id', 'collaboration_comments', ['entity_id'])

    # Sync Items
    op.create_table(
        'sync_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', postgresql.ENUM('observation', 'germplasm', 'trial', 'study', 'cross', 'image', 'sample', name='syncentitytype', create_type=False), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('status', postgresql.ENUM('synced', 'pending', 'conflict', 'error', name='syncstatus', create_type=False), default='pending'),
        sa.Column('size_bytes', sa.Integer(), default=0),
        sa.Column('local_data', sa.JSON()),
        sa.Column('server_data', sa.JSON()),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('last_modified', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sync_items_organization_id', 'sync_items', ['organization_id'])
    op.create_index('ix_sync_items_user_id', 'sync_items', ['user_id'])
    op.create_index('ix_sync_items_status', 'sync_items', ['status'])

    # Sync History
    op.create_table(
        'sync_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', postgresql.ENUM('upload', 'download', 'full_sync', name='syncaction', create_type=False), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('items_count', sa.Integer(), default=0),
        sa.Column('bytes_transferred', sa.Integer(), default=0),
        sa.Column('status', sa.String(20)),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sync_history_organization_id', 'sync_history', ['organization_id'])
    op.create_index('ix_sync_history_user_id', 'sync_history', ['user_id'])

    # Offline Data Cache
    op.create_table(
        'offline_data_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('item_count', sa.Integer(), default=0),
        sa.Column('size_bytes', sa.Integer(), default=0),
        sa.Column('last_updated', sa.DateTime()),
        sa.Column('last_full_sync', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'category', name='uq_user_cache_category')
    )
    op.create_index('ix_offline_data_cache_user_id', 'offline_data_cache', ['user_id'])

    # Sync Settings
    op.create_table(
        'sync_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('auto_sync', sa.Boolean(), default=True),
        sa.Column('sync_on_wifi_only', sa.Boolean(), default=True),
        sa.Column('background_sync', sa.Boolean(), default=True),
        sa.Column('sync_images', sa.Boolean(), default=True),
        sa.Column('sync_interval_minutes', sa.Integer(), default=15),
        sa.Column('max_offline_days', sa.Integer(), default=30),
        sa.Column('conflict_resolution', sa.String(20), default='server_wins'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_sync_settings_user')
    )
    op.create_index('ix_sync_settings_user_id', 'sync_settings', ['user_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('sync_settings')
    op.drop_table('offline_data_cache')
    op.drop_table('sync_history')
    op.drop_table('sync_items')
    op.drop_table('collaboration_comments')
    op.drop_table('collaboration_tasks')
    op.drop_table('collaboration_activities')
    op.drop_table('user_presence')
    op.drop_table('workspace_members')
    op.drop_table('collaboration_workspaces')
    op.drop_table('generated_reports')
    op.drop_table('report_schedules')
    op.drop_table('report_templates')
    
    # Drop enums
    op.execute("""
        DROP TYPE IF EXISTS syncentitytype;
        DROP TYPE IF EXISTS syncaction;
        DROP TYPE IF EXISTS syncstatus;
        DROP TYPE IF EXISTS taskpriority;
        DROP TYPE IF EXISTS taskstatus;
        DROP TYPE IF EXISTS collabactivitytype;
        DROP TYPE IF EXISTS workspacetype;
        DROP TYPE IF EXISTS memberstatus;
        DROP TYPE IF EXISTS memberrole;
        DROP TYPE IF EXISTS schedulestatus;
        DROP TYPE IF EXISTS reportstatus;
        DROP TYPE IF EXISTS schedulefrequency;
        DROP TYPE IF EXISTS reportcategory;
        DROP TYPE IF EXISTS reportformat;
    """)
