"""Add data management tables (collections, validation, backups)

Revision ID: 015
Revises: 014_stress_resistance_field_ops
Create Date: 2025-12-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # GERMPLASM COLLECTIONS
    # ============================================
    op.create_table(
        'germplasm_collections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('collection_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('collection_type', sa.Enum('core', 'working', 'active', 'base', 'breeding', 'reference', name='collectiontype'), nullable=True),
        sa.Column('status', sa.Enum('active', 'archived', 'pending', name='collectionstatus'), nullable=True),
        sa.Column('accession_count', sa.Integer(), nullable=True, default=0),
        sa.Column('species', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('curator_name', sa.String(255), nullable=True),
        sa.Column('curator_email', sa.String(255), nullable=True),
        sa.Column('curator_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['curator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_germplasm_collections_organization_id', 'germplasm_collections', ['organization_id'])
    op.create_index('ix_germplasm_collections_collection_code', 'germplasm_collections', ['collection_code'])
    op.create_index('ix_germplasm_collections_status', 'germplasm_collections', ['status'])
    
    op.create_table(
        'germplasm_collection_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('collection_id', sa.Integer(), nullable=False),
        sa.Column('germplasm_id', sa.Integer(), nullable=False),
        sa.Column('added_by', sa.Integer(), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['germplasm_collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['germplasm_id'], ['germplasm.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_germplasm_collection_members_collection_id', 'germplasm_collection_members', ['collection_id'])
    op.create_index('ix_germplasm_collection_members_germplasm_id', 'germplasm_collection_members', ['germplasm_id'])
    op.create_index('ix_germplasm_collection_members_unique', 'germplasm_collection_members', ['collection_id', 'germplasm_id'], unique=True)
    
    # ============================================
    # VALIDATION RULES
    # ============================================
    op.create_table(
        'validation_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('rule_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('severity', sa.Enum('error', 'warning', 'info', name='validationseverity'), nullable=True),
        sa.Column('entity_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=True),
        sa.Column('rule_config', postgresql.JSON(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_validation_rules_organization_id', 'validation_rules', ['organization_id'])
    op.create_index('ix_validation_rules_rule_code', 'validation_rules', ['rule_code'])
    op.create_index('ix_validation_rules_enabled', 'validation_rules', ['enabled'])
    
    # ============================================
    # VALIDATION RUNS
    # ============================================
    op.create_table(
        'validation_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='validationrunstatus'), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('entity_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('rule_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('records_checked', sa.Integer(), nullable=True, default=0),
        sa.Column('issues_found', sa.Integer(), nullable=True, default=0),
        sa.Column('errors_found', sa.Integer(), nullable=True, default=0),
        sa.Column('warnings_found', sa.Integer(), nullable=True, default=0),
        sa.Column('triggered_by', sa.Integer(), nullable=True),
        sa.Column('trigger_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_validation_runs_organization_id', 'validation_runs', ['organization_id'])
    op.create_index('ix_validation_runs_status', 'validation_runs', ['status'])
    
    # ============================================
    # VALIDATION ISSUES
    # ============================================
    op.create_table(
        'validation_issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=True),
        sa.Column('run_id', sa.Integer(), nullable=True),
        sa.Column('issue_type', sa.Enum('error', 'warning', 'info', name='validationseverity', create_type=False), nullable=True),
        sa.Column('status', sa.Enum('open', 'resolved', 'ignored', name='validationissuestatus'), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('record_id', sa.String(255), nullable=True),
        sa.Column('field_name', sa.String(100), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('suggestion', sa.Text(), nullable=True),
        sa.Column('actual_value', sa.Text(), nullable=True),
        sa.Column('expected_value', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['validation_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['run_id'], ['validation_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_validation_issues_organization_id', 'validation_issues', ['organization_id'])
    op.create_index('ix_validation_issues_rule_id', 'validation_issues', ['rule_id'])
    op.create_index('ix_validation_issues_run_id', 'validation_issues', ['run_id'])
    op.create_index('ix_validation_issues_status', 'validation_issues', ['status'])
    op.create_index('ix_validation_issues_entity_type', 'validation_issues', ['entity_type'])
    op.create_index('ix_validation_issues_record_id', 'validation_issues', ['record_id'])
    
    # ============================================
    # BACKUPS
    # ============================================
    op.create_table(
        'backups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('backup_name', sa.String(255), nullable=False),
        sa.Column('backup_type', sa.Enum('full', 'incremental', 'manual', name='backuptype'), nullable=True),
        sa.Column('status', sa.Enum('in_progress', 'completed', 'failed', name='backupstatus'), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True, default=0),
        sa.Column('storage_path', sa.String(500), nullable=True),
        sa.Column('storage_provider', sa.String(50), nullable=True, default='local'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('tables_included', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('record_counts', postgresql.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_retained', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backups_organization_id', 'backups', ['organization_id'])
    op.create_index('ix_backups_status', 'backups', ['status'])
    op.create_index('ix_backups_backup_type', 'backups', ['backup_type'])
    op.create_index('ix_backups_created_at', 'backups', ['created_at'])
    
    # ============================================
    # CROP HEALTH
    # ============================================
    op.create_table(
        'trial_health',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('trial_id', sa.Integer(), nullable=True),
        sa.Column('trial_name', sa.String(255), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('crop', sa.String(100), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=True, default=100.0),
        sa.Column('disease_risk', sa.Enum('low', 'medium', 'high', name='diseaserisklevel'), nullable=True),
        sa.Column('stress_level', sa.Float(), nullable=True, default=0.0),
        sa.Column('last_scan_at', sa.DateTime(), nullable=True),
        sa.Column('plots_scanned', sa.Integer(), nullable=True, default=0),
        sa.Column('total_plots', sa.Integer(), nullable=True, default=0),
        sa.Column('issues', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['trial_id'], ['trials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trial_health_organization_id', 'trial_health', ['organization_id'])
    op.create_index('ix_trial_health_trial_id', 'trial_health', ['trial_id'])
    op.create_index('ix_trial_health_disease_risk', 'trial_health', ['disease_risk'])
    
    op.create_table(
        'health_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('trial_health_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.Enum('disease', 'stress', 'pest', 'weather', name='alerttype'), nullable=True),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='alertseverity'), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), nullable=True, default=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['trial_health_id'], ['trial_health.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_health_alerts_organization_id', 'health_alerts', ['organization_id'])
    op.create_index('ix_health_alerts_trial_health_id', 'health_alerts', ['trial_health_id'])
    op.create_index('ix_health_alerts_severity', 'health_alerts', ['severity'])
    op.create_index('ix_health_alerts_acknowledged', 'health_alerts', ['acknowledged'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('health_alerts')
    op.drop_table('trial_health')
    op.drop_table('backups')
    op.drop_table('validation_issues')
    op.drop_table('validation_runs')
    op.drop_table('validation_rules')
    op.drop_table('germplasm_collection_members')
    op.drop_table('germplasm_collections')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS alertseverity")
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.execute("DROP TYPE IF EXISTS diseaserisklevel")
    op.execute("DROP TYPE IF EXISTS backupstatus")
    op.execute("DROP TYPE IF EXISTS backuptype")
    op.execute("DROP TYPE IF EXISTS validationissuestatus")
    op.execute("DROP TYPE IF EXISTS validationrunstatus")
    op.execute("DROP TYPE IF EXISTS validationseverity")
    op.execute("DROP TYPE IF EXISTS collectionstatus")
    op.execute("DROP TYPE IF EXISTS collectiontype")
