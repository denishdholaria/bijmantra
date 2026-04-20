"""Add phenomic selection tables for high-throughput phenotyping

Revision ID: 033
Revises: 032
Create Date: 2026-01-15

Tables created:
- phenomic_datasets: Spectral data collections (NIRS, hyperspectral, thermal)
- phenomic_models: Prediction models trained on spectral data
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = '033'
down_revision = '032'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== PHENOMIC DATASETS TABLE ====================
    op.create_table(
        'phenomic_datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('crop', sa.String(100), nullable=False),
        sa.Column('platform', sa.String(100), nullable=False),
        sa.Column('samples', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('wavelengths', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('traits_predicted', JSON, nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_phenomic_datasets_dataset_code', 'phenomic_datasets', ['dataset_code'], unique=True)
    op.create_index('ix_phenomic_datasets_organization_id', 'phenomic_datasets', ['organization_id'])
    op.create_index('ix_phenomic_datasets_crop', 'phenomic_datasets', ['crop'])
    op.create_index('ix_phenomic_datasets_platform', 'phenomic_datasets', ['platform'])
    op.create_index('ix_phenomic_datasets_status', 'phenomic_datasets', ['status'])
    
    # ==================== PHENOMIC MODELS TABLE ====================
    op.create_table(
        'phenomic_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('model_type', sa.String(100), nullable=False),
        sa.Column('dataset_id', sa.Integer(), sa.ForeignKey('phenomic_datasets.id'), nullable=False),
        sa.Column('target_trait', sa.String(255), nullable=False),
        sa.Column('r_squared', sa.Float(), nullable=True),
        sa.Column('rmse', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('parameters', JSON, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='training'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_phenomic_models_model_code', 'phenomic_models', ['model_code'], unique=True)
    op.create_index('ix_phenomic_models_organization_id', 'phenomic_models', ['organization_id'])
    op.create_index('ix_phenomic_models_dataset_id', 'phenomic_models', ['dataset_id'])
    op.create_index('ix_phenomic_models_status', 'phenomic_models', ['status'])
    op.create_index('ix_phenomic_models_dataset_status', 'phenomic_models', ['dataset_id', 'status'])
    
    # ==================== ENABLE RLS ====================
    op.execute("ALTER TABLE phenomic_datasets ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE phenomic_models ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE phenomic_models DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE phenomic_datasets DISABLE ROW LEVEL SECURITY")
    
    op.drop_table('phenomic_models')
    op.drop_table('phenomic_datasets')
