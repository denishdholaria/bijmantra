"""Add doubled haploid tables for DH production

Revision ID: 032
Revises: 031
Create Date: 2026-01-15

Tables created:
- dh_protocols: DH production protocols
- dh_batches: DH production batches
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '032'
down_revision = '031'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== DH PROTOCOLS TABLE ====================
    op.create_table(
        'dh_protocols',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protocol_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('crop', sa.String(100), nullable=False),
        sa.Column('method', sa.String(100), nullable=False),
        sa.Column('inducer', sa.String(255), nullable=True),
        sa.Column('induction_rate', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('doubling_agent', sa.String(100), nullable=True),
        sa.Column('doubling_rate', sa.Float(), nullable=False, server_default='0.25'),
        sa.Column('overall_efficiency', sa.Float(), nullable=True),
        sa.Column('days_to_complete', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dh_protocols_organization_id', 'dh_protocols', ['organization_id'])
    op.create_index('ix_dh_protocols_crop', 'dh_protocols', ['crop'])
    op.create_index('ix_dh_protocols_status', 'dh_protocols', ['status'])
    
    # ==================== DH BATCHES TABLE ====================
    op.create_table(
        'dh_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('protocol_id', sa.Integer(), sa.ForeignKey('dh_protocols.id'), nullable=False),
        sa.Column('donor_cross', sa.String(255), nullable=True),
        sa.Column('donor_plants', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('anthers_cultured', sa.Integer(), nullable=True),
        sa.Column('embryos_formed', sa.Integer(), nullable=True),
        sa.Column('plants_regenerated', sa.Integer(), nullable=True),
        sa.Column('haploids_induced', sa.Integer(), nullable=True),
        sa.Column('haploids_identified', sa.Integer(), nullable=True),
        sa.Column('doubled_plants', sa.Integer(), nullable=True),
        sa.Column('fertile_dh_lines', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('stage', sa.String(100), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dh_batches_organization_id', 'dh_batches', ['organization_id'])
    op.create_index('ix_dh_batches_protocol_id', 'dh_batches', ['protocol_id'])
    op.create_index('ix_dh_batches_status', 'dh_batches', ['status'])
    op.create_index('ix_dh_batches_protocol_status', 'dh_batches', ['protocol_id', 'status'])
    
    # ==================== ENABLE RLS ====================
    op.execute("ALTER TABLE dh_protocols ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dh_batches ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE dh_batches DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dh_protocols DISABLE ROW LEVEL SECURITY")
    
    op.drop_table('dh_batches')
    op.drop_table('dh_protocols')
