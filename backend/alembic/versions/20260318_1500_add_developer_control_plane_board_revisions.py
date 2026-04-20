"""Add developer control-plane board revision ledger.

Revision ID: 20260318_1500
Revises: 20260318_1300
Create Date: 2026-03-18 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_1500"
down_revision = "20260318_1300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "developer_control_plane_board_revisions",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("board_id", sa.String(length=255), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("visibility", sa.String(length=64), nullable=False),
        sa.Column("canonical_board_json", sa.Text(), nullable=False),
        sa.Column("canonical_board_hash", sa.String(length=64), nullable=False),
        sa.Column("saved_by_user_id", sa.Integer(), nullable=False),
        sa.Column("save_source", sa.String(length=64), nullable=False),
        sa.Column("summary_metadata", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["saved_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_developer_control_plane_board_revisions_id"),
        "developer_control_plane_board_revisions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_board_revisions_organization_id"),
        "developer_control_plane_board_revisions",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_board_revisions_board_id"),
        "developer_control_plane_board_revisions",
        ["board_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_board_revisions_canonical_board_hash"),
        "developer_control_plane_board_revisions",
        ["canonical_board_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_board_revisions_saved_by_user_id"),
        "developer_control_plane_board_revisions",
        ["saved_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_developer_control_plane_board_revisions_org_board_created_at",
        "developer_control_plane_board_revisions",
        ["organization_id", "board_id", "created_at"],
        unique=False,
    )

    op.execute(
        """
        ALTER TABLE developer_control_plane_board_revisions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE developer_control_plane_board_revisions FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS developer_control_plane_board_revisions_tenant_isolation ON developer_control_plane_board_revisions;
        CREATE POLICY developer_control_plane_board_revisions_tenant_isolation ON developer_control_plane_board_revisions
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS developer_control_plane_board_revisions_tenant_isolation ON developer_control_plane_board_revisions;"
    )
    op.drop_index(
        "ix_developer_control_plane_board_revisions_org_board_created_at",
        table_name="developer_control_plane_board_revisions",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_board_revisions_saved_by_user_id"),
        table_name="developer_control_plane_board_revisions",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_board_revisions_canonical_board_hash"),
        table_name="developer_control_plane_board_revisions",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_board_revisions_board_id"),
        table_name="developer_control_plane_board_revisions",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_board_revisions_organization_id"),
        table_name="developer_control_plane_board_revisions",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_board_revisions_id"),
        table_name="developer_control_plane_board_revisions",
    )
    op.drop_table("developer_control_plane_board_revisions")