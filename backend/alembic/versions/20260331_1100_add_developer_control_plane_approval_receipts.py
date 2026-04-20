"""Add developer control-plane approval receipt ledger.

Revision ID: 20260331_1100
Revises: 20260328_1600
Create Date: 2026-03-31 11:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260331_1100"
down_revision = "20260328_1600"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "developer_control_plane_approval_receipts",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("authority_actor_user_id", sa.Integer(), nullable=False),
        sa.Column("authority_actor_email", sa.String(length=320), nullable=True),
        sa.Column("authority_source", sa.String(length=64), nullable=False),
        sa.Column("board_id", sa.String(length=255), nullable=False),
        sa.Column("source_board_concurrency_token", sa.String(length=64), nullable=True),
        sa.Column("resulting_board_concurrency_token", sa.String(length=64), nullable=True),
        sa.Column("source_lane_id", sa.String(length=128), nullable=True),
        sa.Column("queue_job_id", sa.String(length=256), nullable=True),
        sa.Column("expected_queue_sha256", sa.String(length=128), nullable=True),
        sa.Column("resulting_queue_sha256", sa.String(length=128), nullable=True),
        sa.Column("target_revision_id", sa.Integer(), nullable=True),
        sa.Column("previous_active_concurrency_token", sa.String(length=64), nullable=True),
        sa.Column("linked_mission_id", sa.String(length=256), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["authority_actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_developer_control_plane_approval_receipts_id"),
        "developer_control_plane_approval_receipts",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_approval_receipts_organization_id"),
        "developer_control_plane_approval_receipts",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_approval_receipts_action_type"),
        "developer_control_plane_approval_receipts",
        ["action_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_approval_receipts_authority_actor_user_id"),
        "developer_control_plane_approval_receipts",
        ["authority_actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_approval_receipts_board_id"),
        "developer_control_plane_approval_receipts",
        ["board_id"],
        unique=False,
    )
    op.create_index(
        "ix_dcp_approval_receipts_org_action_created",
        "developer_control_plane_approval_receipts",
        ["organization_id", "action_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_dcp_approval_receipts_org_board_lane_created",
        "developer_control_plane_approval_receipts",
        ["organization_id", "board_id", "source_lane_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_dcp_approval_receipts_org_queue_job_created",
        "developer_control_plane_approval_receipts",
        ["organization_id", "queue_job_id", "created_at"],
        unique=False,
    )

    op.execute(
        """
        ALTER TABLE developer_control_plane_approval_receipts ENABLE ROW LEVEL SECURITY;
        ALTER TABLE developer_control_plane_approval_receipts FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS developer_control_plane_approval_receipts_tenant_isolation ON developer_control_plane_approval_receipts;
        CREATE POLICY developer_control_plane_approval_receipts_tenant_isolation ON developer_control_plane_approval_receipts
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS developer_control_plane_approval_receipts_tenant_isolation ON developer_control_plane_approval_receipts;"
    )
    op.drop_index(
        "ix_dcp_approval_receipts_org_queue_job_created",
        table_name="developer_control_plane_approval_receipts",
    )
    op.drop_index(
        "ix_dcp_approval_receipts_org_board_lane_created",
        table_name="developer_control_plane_approval_receipts",
    )
    op.drop_index(
        "ix_dcp_approval_receipts_org_action_created",
        table_name="developer_control_plane_approval_receipts",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_approval_receipts_board_id"),
        table_name="developer_control_plane_approval_receipts",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_approval_receipts_authority_actor_user_id"),
        table_name="developer_control_plane_approval_receipts",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_approval_receipts_action_type"),
        table_name="developer_control_plane_approval_receipts",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_approval_receipts_organization_id"),
        table_name="developer_control_plane_approval_receipts",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_approval_receipts_id"),
        table_name="developer_control_plane_approval_receipts",
    )
    op.drop_table("developer_control_plane_approval_receipts")
