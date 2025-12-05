"""Seed Bank division tables

Revision ID: 004_seed_bank
Revises: 003_add_vector_store
Create Date: 2025-12-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004_seed_bank'
down_revision = '003_add_vector_store'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Vault types enum
    vault_type = postgresql.ENUM('base', 'active', 'cryo', name='vault_type')
    vault_type.create(op.get_bind(), checkfirst=True)
    
    vault_status = postgresql.ENUM('optimal', 'warning', 'critical', name='vault_status')
    vault_status.create(op.get_bind(), checkfirst=True)
    
    accession_status = postgresql.ENUM('active', 'depleted', 'regenerating', name='accession_status')
    accession_status.create(op.get_bind(), checkfirst=True)
    
    test_status = postgresql.ENUM('scheduled', 'in-progress', 'completed', name='test_status')
    test_status.create(op.get_bind(), checkfirst=True)
    
    regen_priority = postgresql.ENUM('high', 'medium', 'low', name='regeneration_priority')
    regen_priority.create(op.get_bind(), checkfirst=True)
    
    regen_status = postgresql.ENUM('planned', 'in-progress', 'harvested', 'completed', name='regeneration_status')
    regen_status.create(op.get_bind(), checkfirst=True)
    
    exchange_type = postgresql.ENUM('incoming', 'outgoing', name='exchange_type')
    exchange_type.create(op.get_bind(), checkfirst=True)
    
    exchange_status = postgresql.ENUM('pending', 'approved', 'shipped', 'received', 'rejected', name='exchange_status')
    exchange_status.create(op.get_bind(), checkfirst=True)

    # Vaults table
    op.create_table(
        'seed_bank_vaults',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.Enum('base', 'active', 'cryo', name='vault_type'), nullable=False),
        sa.Column('temperature', sa.Float, nullable=False),
        sa.Column('humidity', sa.Float, nullable=False),
        sa.Column('capacity', sa.Integer, nullable=False),
        sa.Column('used', sa.Integer, default=0),
        sa.Column('status', sa.Enum('optimal', 'warning', 'critical', name='vault_status'), default='optimal'),
        sa.Column('last_inspection', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Accessions table
    op.create_table(
        'seed_bank_accessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('accession_number', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('genus', sa.String(100), nullable=False, index=True),
        sa.Column('species', sa.String(100), nullable=False, index=True),
        sa.Column('subspecies', sa.String(100)),
        sa.Column('common_name', sa.String(255)),
        sa.Column('origin', sa.String(100), index=True),
        sa.Column('collection_date', sa.DateTime),
        sa.Column('collection_site', sa.String(500)),
        sa.Column('latitude', sa.Float),
        sa.Column('longitude', sa.Float),
        sa.Column('altitude', sa.Float),
        sa.Column('vault_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seed_bank_vaults.id')),
        sa.Column('seed_count', sa.Integer, default=0),
        sa.Column('viability', sa.Float, default=100.0),
        sa.Column('status', sa.Enum('active', 'depleted', 'regenerating', name='accession_status'), default='active', index=True),
        sa.Column('acquisition_type', sa.String(50)),
        sa.Column('donor_institution', sa.String(255)),
        sa.Column('mls', sa.Boolean, default=False),
        sa.Column('pedigree', sa.Text),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Viability tests table
    op.create_table(
        'seed_bank_viability_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('batch_number', sa.String(50), nullable=False, unique=True),
        sa.Column('accession_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seed_bank_accessions.id'), nullable=False),
        sa.Column('test_date', sa.DateTime, nullable=False),
        sa.Column('seeds_tested', sa.Integer, nullable=False),
        sa.Column('germinated', sa.Integer, default=0),
        sa.Column('germination_rate', sa.Float, default=0.0),
        sa.Column('status', sa.Enum('scheduled', 'in-progress', 'completed', name='test_status'), default='scheduled'),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Regeneration tasks table
    op.create_table(
        'seed_bank_regeneration_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('accession_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seed_bank_accessions.id'), nullable=False),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('priority', sa.Enum('high', 'medium', 'low', name='regeneration_priority'), default='medium'),
        sa.Column('target_quantity', sa.Integer, nullable=False),
        sa.Column('planned_season', sa.String(50)),
        sa.Column('status', sa.Enum('planned', 'in-progress', 'harvested', 'completed', name='regeneration_status'), default='planned'),
        sa.Column('location_id', postgresql.UUID(as_uuid=True)),
        sa.Column('harvested_quantity', sa.Integer),
        sa.Column('completed_date', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Germplasm exchanges table
    op.create_table(
        'seed_bank_exchanges',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('request_number', sa.String(50), nullable=False, unique=True),
        sa.Column('type', sa.Enum('incoming', 'outgoing', name='exchange_type'), nullable=False),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True)),
        sa.Column('institution_name', sa.String(255), nullable=False),
        sa.Column('accession_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('status', sa.Enum('pending', 'approved', 'shipped', 'received', 'rejected', name='exchange_status'), default='pending'),
        sa.Column('request_date', sa.DateTime, nullable=False),
        sa.Column('smta', sa.Boolean, default=True),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('seed_bank_exchanges')
    op.drop_table('seed_bank_regeneration_tasks')
    op.drop_table('seed_bank_viability_tests')
    op.drop_table('seed_bank_accessions')
    op.drop_table('seed_bank_vaults')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS exchange_status')
    op.execute('DROP TYPE IF EXISTS exchange_type')
    op.execute('DROP TYPE IF EXISTS regeneration_status')
    op.execute('DROP TYPE IF EXISTS regeneration_priority')
    op.execute('DROP TYPE IF EXISTS test_status')
    op.execute('DROP TYPE IF EXISTS accession_status')
    op.execute('DROP TYPE IF EXISTS vault_status')
    op.execute('DROP TYPE IF EXISTS vault_type')
