"""Add active developer control-plane board persistence.

Revision ID: 20260318_1300
Revises: 20260315_0300
Create Date: 2026-03-18 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_1300"
down_revision = "20260315_0300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "developer_control_plane_active_boards",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("board_id", sa.String(length=255), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("visibility", sa.String(length=64), nullable=False),
        sa.Column("canonical_board_json", sa.Text(), nullable=False),
        sa.Column("canonical_board_hash", sa.String(length=64), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("save_source", sa.String(length=64), nullable=False),
        sa.Column("summary_metadata", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "board_id",
            name="uq_developer_control_plane_active_board_org_board",
        ),
    )
    op.create_index(
        op.f("ix_developer_control_plane_active_boards_id"),
        "developer_control_plane_active_boards",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_active_boards_organization_id"),
        "developer_control_plane_active_boards",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_active_boards_board_id"),
        "developer_control_plane_active_boards",
        ["board_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_active_boards_canonical_board_hash"),
        "developer_control_plane_active_boards",
        ["canonical_board_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_active_boards_updated_by_user_id"),
        "developer_control_plane_active_boards",
        ["updated_by_user_id"],
        unique=False,
    )

    op.execute(
        """
        ALTER TABLE developer_control_plane_active_boards ENABLE ROW LEVEL SECURITY;
        ALTER TABLE developer_control_plane_active_boards FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS developer_control_plane_active_boards_tenant_isolation ON developer_control_plane_active_boards;
        CREATE POLICY developer_control_plane_active_boards_tenant_isolation ON developer_control_plane_active_boards
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS developer_control_plane_active_boards_tenant_isolation ON developer_control_plane_active_boards;"
    )
    op.drop_index(
        op.f("ix_developer_control_plane_active_boards_updated_by_user_id"),
        table_name="developer_control_plane_active_boards",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_active_boards_canonical_board_hash"),
        table_name="developer_control_plane_active_boards",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_active_boards_board_id"),
        table_name="developer_control_plane_active_boards",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_active_boards_organization_id"),
        table_name="developer_control_plane_active_boards",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_active_boards_id"),
        table_name="developer_control_plane_active_boards",
    )
    op.drop_table("developer_control_plane_active_boards")