"""Add compute lineage records.

Revision ID: 20260311_0300
Revises: 20260310_0200
Create Date: 2026-03-11 03:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '20260311_0300'
down_revision = '20260310_0200'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		'compute_lineage_records',
		sa.Column('lineage_record_id', sa.String(length=64), nullable=False),
		sa.Column('organization_id', sa.Integer(), nullable=True),
		sa.Column('user_id', sa.Integer(), nullable=True),
		sa.Column('job_id', sa.String(length=255), nullable=True),
		sa.Column('routine', sa.String(length=32), nullable=False),
		sa.Column('output_kind', sa.String(length=64), nullable=True),
		sa.Column('execution_mode', sa.String(length=16), nullable=False),
		sa.Column('status', sa.String(length=32), nullable=False),
		sa.Column('contract_version', sa.String(length=32), nullable=False),
		sa.Column('input_summary', sa.JSON(), nullable=True),
		sa.Column('provenance', sa.JSON(), nullable=True),
		sa.Column('policy_flags', sa.JSON(), nullable=True),
		sa.Column('result_summary', sa.JSON(), nullable=True),
		sa.Column('error', sa.JSON(), nullable=True),
		sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('id', sa.Integer(), nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
		sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
		sa.ForeignKeyConstraint(['user_id'], ['users.id']),
		sa.PrimaryKeyConstraint('id'),
	)
	op.create_index(op.f('ix_compute_lineage_records_lineage_record_id'), 'compute_lineage_records', ['lineage_record_id'], unique=True)
	op.create_index(op.f('ix_compute_lineage_records_organization_id'), 'compute_lineage_records', ['organization_id'], unique=False)
	op.create_index(op.f('ix_compute_lineage_records_user_id'), 'compute_lineage_records', ['user_id'], unique=False)
	op.create_index(op.f('ix_compute_lineage_records_job_id'), 'compute_lineage_records', ['job_id'], unique=False)
	op.create_index(op.f('ix_compute_lineage_records_routine'), 'compute_lineage_records', ['routine'], unique=False)
	op.create_index(op.f('ix_compute_lineage_records_execution_mode'), 'compute_lineage_records', ['execution_mode'], unique=False)
	op.create_index(op.f('ix_compute_lineage_records_status'), 'compute_lineage_records', ['status'], unique=False)
	op.create_index(op.f('ix_compute_lineage_records_completed_at'), 'compute_lineage_records', ['completed_at'], unique=False)
	op.create_index('ix_compute_lineage_org_status', 'compute_lineage_records', ['organization_id', 'status'], unique=False)
	op.create_index('ix_compute_lineage_job_status', 'compute_lineage_records', ['job_id', 'status'], unique=False)
	op.create_index('ix_compute_lineage_org_created', 'compute_lineage_records', ['organization_id', 'created_at'], unique=False)


def downgrade() -> None:
	op.drop_index('ix_compute_lineage_org_created', table_name='compute_lineage_records')
	op.drop_index('ix_compute_lineage_job_status', table_name='compute_lineage_records')
	op.drop_index('ix_compute_lineage_org_status', table_name='compute_lineage_records')
	op.drop_index(op.f('ix_compute_lineage_records_completed_at'), table_name='compute_lineage_records')
	op.drop_index(op.f('ix_compute_lineage_records_status'), table_name='compute_lineage_records')
	op.drop_index(op.f('ix_compute_lineage_records_execution_mode'), table_name='compute_lineage_records')
	op.drop_index(op.f('ix_compute_lineage_records_routine'), table_name='compute_lineage_records')
	op.drop_index(op.f('ix_compute_lineage_records_job_id'), table_name='compute_lineage_records')
	op.drop_index(op.f('ix_compute_lineage_records_user_id'), table_name='compute_lineage_records')
	op.drop_index(op.f('ix_compute_lineage_records_organization_id'), table_name='compute_lineage_records')
	op.drop_index(op.f('ix_compute_lineage_records_lineage_record_id'), table_name='compute_lineage_records')
	op.drop_table('compute_lineage_records')