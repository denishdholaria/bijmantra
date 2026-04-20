"""Add developer control-plane learning ledger.

Revision ID: 20260331_1500
Revises: 20260331_1100
Create Date: 2026-03-31 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260331_1500"
down_revision = "20260331_1100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "developer_control_plane_learning_entries",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("entry_type", sa.String(length=64), nullable=False),
        sa.Column("source_classification", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("recorded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("recorded_by_email", sa.String(length=320), nullable=True),
        sa.Column("board_id", sa.String(length=255), nullable=True),
        sa.Column("source_lane_id", sa.String(length=128), nullable=True),
        sa.Column("queue_job_id", sa.String(length=256), nullable=True),
        sa.Column("linked_mission_id", sa.String(length=256), nullable=True),
        sa.Column("approval_receipt_id", sa.Integer(), nullable=True),
        sa.Column("source_reference", sa.String(length=512), nullable=True),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["approval_receipt_id"],
            ["developer_control_plane_approval_receipts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_developer_control_plane_learning_entries_id"),
        "developer_control_plane_learning_entries",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_learning_entries_organization_id"),
        "developer_control_plane_learning_entries",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_learning_entries_entry_type"),
        "developer_control_plane_learning_entries",
        ["entry_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_learning_entries_source_classification"),
        "developer_control_plane_learning_entries",
        ["source_classification"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_learning_entries_recorded_by_user_id"),
        "developer_control_plane_learning_entries",
        ["recorded_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_learning_entries_board_id"),
        "developer_control_plane_learning_entries",
        ["board_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_developer_control_plane_learning_entries_approval_receipt_id"),
        "developer_control_plane_learning_entries",
        ["approval_receipt_id"],
        unique=False,
    )
    op.create_index(
        "ix_dcp_learning_entries_org_entry_type_created",
        "developer_control_plane_learning_entries",
        ["organization_id", "entry_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_dcp_learning_entries_org_src_class_created",
        "developer_control_plane_learning_entries",
        ["organization_id", "source_classification", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_dcp_learning_entries_org_board_lane_created",
        "developer_control_plane_learning_entries",
        ["organization_id", "board_id", "source_lane_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_dcp_learning_entries_org_queue_job_created",
        "developer_control_plane_learning_entries",
        ["organization_id", "queue_job_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_dcp_learning_entries_org_mission_created",
        "developer_control_plane_learning_entries",
        ["organization_id", "linked_mission_id", "created_at"],
        unique=False,
    )

    op.execute(
        """
        ALTER TABLE developer_control_plane_learning_entries ENABLE ROW LEVEL SECURITY;
        ALTER TABLE developer_control_plane_learning_entries FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS developer_control_plane_learning_entries_tenant_isolation ON developer_control_plane_learning_entries;
        CREATE POLICY developer_control_plane_learning_entries_tenant_isolation ON developer_control_plane_learning_entries
            FOR ALL
            USING (organization_id = current_organization_id() OR current_organization_id() = 0)
            WITH CHECK (organization_id = current_organization_id() OR current_organization_id() = 0);
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS developer_control_plane_learning_entries_tenant_isolation ON developer_control_plane_learning_entries;"
    )
    op.drop_index(
        "ix_dcp_learning_entries_org_mission_created",
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        "ix_dcp_learning_entries_org_queue_job_created",
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        "ix_dcp_learning_entries_org_board_lane_created",
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        "ix_dcp_learning_entries_org_src_class_created",
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        "ix_dcp_learning_entries_org_entry_type_created",
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_learning_entries_approval_receipt_id"),
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_learning_entries_board_id"),
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_learning_entries_recorded_by_user_id"),
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_learning_entries_source_classification"),
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_learning_entries_entry_type"),
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_learning_entries_organization_id"),
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_index(
        op.f("ix_developer_control_plane_learning_entries_id"),
        table_name="developer_control_plane_learning_entries",
    )
    op.drop_table("developer_control_plane_learning_entries")