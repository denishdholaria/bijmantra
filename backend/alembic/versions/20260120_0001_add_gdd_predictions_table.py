"""add_gdd_predictions_table

Revision ID: a1b2c3d4e5f6
Revises: 14da62c13441
Create Date: 2026-01-20 10:00:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '14da62c13441'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create gdd_predictions table
    op.create_table(
        'gdd_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('crop_name', sa.String(100), nullable=False),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('target_stage', sa.String(100), nullable=False),
        sa.Column('predicted_date', sa.Date(), nullable=True),
        sa.Column('predicted_gdd', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_gdd_pred_org_field', 'gdd_predictions', ['organization_id', 'field_id'])
    op.create_index('ix_gdd_pred_org_date', 'gdd_predictions', ['organization_id', 'prediction_date'])

    # Enable RLS
    op.execute('ALTER TABLE gdd_predictions ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.drop_table('gdd_predictions')
