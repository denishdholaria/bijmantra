"""Add organization capability installation table.

Revision ID: 20260529_0100
Revises: 20260520_0400
Create Date: 2026-05-29 01:00:00.000000
"""

import sqlalchemy as sa

from alembic import op


revision = "20260529_0100"
down_revision = "20260520_0400"
branch_labels = None
depends_on = None


TABLE_NAME = "organization_capability_installations"


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
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("capability_id", sa.String(length=160), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False, server_default="installed"),
        sa.Column("granted_permissions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("data_scopes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("installed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("disabled_by_user_id", sa.Integer(), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["installed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["disabled_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "capability_id",
            name="uq_org_capability_installation",
        ),
    )
    op.create_index(
        op.f("ix_organization_capability_installations_organization_id"),
        TABLE_NAME,
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_capability_installations_capability_id"),
        TABLE_NAME,
        ["capability_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_capability_installations_installed_by_user_id"),
        TABLE_NAME,
        ["installed_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_capability_installations_disabled_by_user_id"),
        TABLE_NAME,
        ["disabled_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_org_capability_installations_org_enabled",
        TABLE_NAME,
        ["organization_id", "enabled"],
        unique=False,
    )
    _enable_tenant_rls()


def downgrade() -> None:
    _disable_tenant_rls()
    op.drop_index("ix_org_capability_installations_org_enabled", table_name=TABLE_NAME)
    op.drop_index(
        op.f("ix_organization_capability_installations_disabled_by_user_id"),
        table_name=TABLE_NAME,
    )
    op.drop_index(
        op.f("ix_organization_capability_installations_installed_by_user_id"),
        table_name=TABLE_NAME,
    )
    op.drop_index(
        op.f("ix_organization_capability_installations_capability_id"),
        table_name=TABLE_NAME,
    )
    op.drop_index(
        op.f("ix_organization_capability_installations_organization_id"),
        table_name=TABLE_NAME,
    )
    op.drop_table(TABLE_NAME)
