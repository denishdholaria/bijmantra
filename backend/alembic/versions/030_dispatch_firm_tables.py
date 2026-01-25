"""Add dispatch and firm tables for seed operations

Revision ID: 030
Revises: 029
Create Date: 2026-01-15

Tables created:
- firms: Dealers, distributors, retailers for seed business
- dispatches: Seed dispatch orders
- dispatch_items: Line items in dispatches
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== FIRMS TABLE ====================
    op.create_table(
        'firms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('firm_code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('firm_type', sa.String(50), nullable=False),  # dealer, distributor, retailer, farmer, institution, government
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('gst_number', sa.String(50), nullable=True),  # Tax ID
        sa.Column('credit_limit', sa.Float(), nullable=False, server_default='0'),
        sa.Column('credit_used', sa.Float(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_firms_organization_id', 'firms', ['organization_id'])
    op.create_index('ix_firms_firm_type', 'firms', ['firm_type'])
    op.create_index('ix_firms_status', 'firms', ['status'])
    op.create_index('ix_firms_city_state', 'firms', ['city', 'state'])
    
    # ==================== DISPATCHES TABLE ====================
    op.create_table(
        'dispatches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dispatch_number', sa.String(50), nullable=False, unique=True),
        sa.Column('recipient_id', sa.Integer(), sa.ForeignKey('firms.id'), nullable=True),  # FK to firms
        sa.Column('recipient_name', sa.String(255), nullable=False),
        sa.Column('recipient_address', sa.Text(), nullable=True),
        sa.Column('recipient_contact', sa.String(255), nullable=True),
        sa.Column('recipient_phone', sa.String(50), nullable=True),
        sa.Column('transfer_type', sa.String(50), nullable=False),  # sale, internal, donation, sample, return
        sa.Column('total_quantity_kg', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('carrier', sa.String(100), nullable=True),
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dispatches_organization_id', 'dispatches', ['organization_id'])
    op.create_index('ix_dispatches_status', 'dispatches', ['status'])
    op.create_index('ix_dispatches_transfer_type', 'dispatches', ['transfer_type'])
    op.create_index('ix_dispatches_recipient_id', 'dispatches', ['recipient_id'])
    op.create_index('ix_dispatches_created_at', 'dispatches', ['created_at'])
    
    # ==================== DISPATCH ITEMS TABLE ====================
    op.create_table(
        'dispatch_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dispatch_id', sa.Integer(), sa.ForeignKey('dispatches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('seedlot_id', sa.Integer(), sa.ForeignKey('seedlots.id'), nullable=True),  # FK to seedlots
        sa.Column('lot_id', sa.String(100), nullable=False),  # External lot reference
        sa.Column('variety_name', sa.String(255), nullable=True),
        sa.Column('crop', sa.String(100), nullable=True),
        sa.Column('seed_class', sa.String(50), nullable=True),  # breeder, foundation, certified, truthful
        sa.Column('quantity_kg', sa.Float(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_price', sa.Float(), nullable=True),
        sa.Column('picked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('packed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dispatch_items_dispatch_id', 'dispatch_items', ['dispatch_id'])
    op.create_index('ix_dispatch_items_seedlot_id', 'dispatch_items', ['seedlot_id'])
    
    # ==================== ENABLE RLS ====================
    op.execute("ALTER TABLE firms ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE dispatches ENABLE ROW LEVEL SECURITY")
    # dispatch_items inherits RLS through dispatch_id FK


def downgrade() -> None:
    op.execute("ALTER TABLE dispatches DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE firms DISABLE ROW LEVEL SECURITY")
    
    op.drop_table('dispatch_items')
    op.drop_table('dispatches')
    op.drop_table('firms')
