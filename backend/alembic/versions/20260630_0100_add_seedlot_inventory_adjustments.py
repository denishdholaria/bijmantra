"""Add append-only seedlot inventory adjustment ledger.

Revision ID: 20260630_0100
Revises: 20260529_0100
Create Date: 2026-06-30 01:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision = "20260630_0100"
down_revision = "20260529_0100"
branch_labels = None
depends_on = None


TABLE_NAME = "seedlot_inventory_adjustments"
ACTION = "seedlot_inventory_adjustment.create"
AUDIT_EVENT = "seed_lot.adjusted"


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _enable_tenant_rls() -> None:
    if not _is_postgresql():
        return
    op.execute(
        f"""
        ALTER TABLE {TABLE_NAME} ENABLE ROW LEVEL SECURITY;
        ALTER TABLE {TABLE_NAME} FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS {TABLE_NAME}_tenant_isolation ON {TABLE_NAME};
        CREATE POLICY {TABLE_NAME}_tenant_isolation ON {TABLE_NAME}
            FOR ALL
            USING (
                current_organization_id() = 0
                OR organization_id = current_organization_id()
            )
            WITH CHECK (
                current_organization_id() = 0
                OR organization_id = current_organization_id()
            );
        """
    )


def _disable_tenant_rls() -> None:
    if not _is_postgresql():
        return
    op.execute(
        f"""
        DROP POLICY IF EXISTS {TABLE_NAME}_tenant_isolation ON {TABLE_NAME};
        ALTER TABLE {TABLE_NAME} DISABLE ROW LEVEL SECURITY;
        """
    )


def upgrade() -> None:
    op.create_table(
        TABLE_NAME,
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("seedlot_id", sa.BigInteger(), nullable=True),
        sa.Column("seedlot_db_id", sa.Text(), nullable=False),
        sa.Column("adjustment_type", sa.Text(), nullable=False),
        sa.Column("quantity_delta", sa.Numeric(20, 6), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False, server_default=ACTION),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("audit_event", sa.Text(), nullable=False, server_default=AUDIT_EVENT),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("reversal_of_public_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["seedlot_id"], ["seedlots.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reversal_of_public_id"], [f"{TABLE_NAME}.public_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id", name="uq_seedlot_inventory_adjustments_public_id"),
        sa.UniqueConstraint(
            "organization_id",
            "actor_user_id",
            "action",
            "idempotency_key",
            name="uq_seedlot_inventory_adjustments_idempotency",
        ),
        sa.CheckConstraint(
            "substring(public_id::text from 15 for 1) = '7'",
            name="ck_seedlot_inventory_adjustments_public_id_uuid7",
        ),
        sa.CheckConstraint(
            "adjustment_type IN ('increase', 'decrease', 'correction', 'reservation', 'release')",
            name="ck_seedlot_inventory_adjustments_type",
        ),
        sa.CheckConstraint(
            "quantity_delta <> 0",
            name="ck_seedlot_inventory_adjustments_quantity_nonzero",
        ),
        sa.CheckConstraint(
            "unit IN ('g', 'kg', 'seeds', 'packets', 'other')",
            name="ck_seedlot_inventory_adjustments_unit",
        ),
        sa.CheckConstraint(
            "length(btrim(reason)) > 0",
            name="ck_seedlot_inventory_adjustments_reason_nonempty",
        ),
        sa.CheckConstraint(
            f"audit_event = '{AUDIT_EVENT}'",
            name="ck_seedlot_inventory_adjustments_audit_event",
        ),
        sa.CheckConstraint(
            f"action = '{ACTION}'",
            name="ck_seedlot_inventory_adjustments_action",
        ),
    )
    op.create_index(
        op.f("ix_seedlot_inventory_adjustments_organization_id"),
        TABLE_NAME,
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_seedlot_inventory_adjustments_seedlot_db_id"),
        TABLE_NAME,
        ["seedlot_db_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_seedlot_inventory_adjustments_created_at"),
        TABLE_NAME,
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_seedlot_inventory_adjustments_reversal_of_public_id"),
        TABLE_NAME,
        ["reversal_of_public_id"],
        unique=False,
    )
    _enable_tenant_rls()


def downgrade() -> None:
    _disable_tenant_rls()
    op.drop_index(op.f("ix_seedlot_inventory_adjustments_reversal_of_public_id"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_seedlot_inventory_adjustments_created_at"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_seedlot_inventory_adjustments_seedlot_db_id"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_seedlot_inventory_adjustments_organization_id"), table_name=TABLE_NAME)
    op.drop_table(TABLE_NAME)
