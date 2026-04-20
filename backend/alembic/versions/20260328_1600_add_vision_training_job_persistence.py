"""Add persisted vision training job and log tables.

Revision ID: 20260328_1600
Revises: 20260328_1200
Create Date: 2026-03-28 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260328_1600"
down_revision = "20260328_1200"
branch_labels = None
depends_on = None


training_backend_enum = postgresql.ENUM(
    "BROWSER",
    "SERVER",
    "CLOUD",
    name="visiontrainingbackend",
    create_type=False,
)
training_status_enum = postgresql.ENUM(
    "QUEUED",
    "PREPARING",
    "TRAINING",
    "VALIDATING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    name="visiontrainingstatus",
    create_type=False,
)


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _index_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)
    }


def _create_vision_training_jobs_table() -> None:
    op.create_table(
        "vision_training_jobs",
        sa.Column("job_code", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_model", sa.String(length=128), nullable=False),
        sa.Column("backend", training_backend_enum, nullable=False),
        sa.Column("status", training_status_enum, nullable=False, server_default="QUEUED"),
        sa.Column("hyperparameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("current_epoch", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_epochs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("model_id", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dataset_id"], ["vision_datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def _ensure_vision_training_jobs_indexes() -> None:
    index_names = _index_names("vision_training_jobs")
    if op.f("ix_vision_training_jobs_id") not in index_names:
        op.create_index(op.f("ix_vision_training_jobs_id"), "vision_training_jobs", ["id"], unique=False)
    if "ix_vision_training_jobs_job_code" not in index_names:
        op.create_index("ix_vision_training_jobs_job_code", "vision_training_jobs", ["job_code"], unique=True)
    if "ix_vision_training_jobs_organization_id" not in index_names:
        op.create_index("ix_vision_training_jobs_organization_id", "vision_training_jobs", ["organization_id"], unique=False)
    if "ix_vision_training_jobs_dataset_id" not in index_names:
        op.create_index("ix_vision_training_jobs_dataset_id", "vision_training_jobs", ["dataset_id"], unique=False)
    if "ix_vision_training_jobs_status" not in index_names:
        op.create_index("ix_vision_training_jobs_status", "vision_training_jobs", ["status"], unique=False)


def _create_vision_training_logs_table() -> None:
    op.create_table(
        "vision_training_logs",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", training_status_enum, nullable=True),
        sa.Column("epoch", sa.Integer(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["vision_training_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def _ensure_vision_training_logs_indexes() -> None:
    index_names = _index_names("vision_training_logs")
    if op.f("ix_vision_training_logs_id") not in index_names:
        op.create_index(op.f("ix_vision_training_logs_id"), "vision_training_logs", ["id"], unique=False)
    if "ix_vision_training_logs_organization_id" not in index_names:
        op.create_index("ix_vision_training_logs_organization_id", "vision_training_logs", ["organization_id"], unique=False)
    if "ix_vision_training_logs_job_id" not in index_names:
        op.create_index("ix_vision_training_logs_job_id", "vision_training_logs", ["job_id"], unique=False)
    if "ix_vision_training_logs_event_type" not in index_names:
        op.create_index("ix_vision_training_logs_event_type", "vision_training_logs", ["event_type"], unique=False)


def _enable_tenant_rls(table_name: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
                AND column_name = 'organization_id'
            ) THEN
                ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
                ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;
                DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name};
                CREATE POLICY {table_name}_tenant_isolation ON {table_name}
                    FOR ALL
                    USING (
                        current_organization_id() = 0
                        OR organization_id = current_organization_id()
                    )
                    WITH CHECK (
                        current_organization_id() = 0
                        OR organization_id = current_organization_id()
                    );
            END IF;
        END $$;
        """
    )


def _disable_tenant_rls(table_name: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
            ) THEN
                DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name};
                ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    training_backend_enum.create(op.get_bind(), checkfirst=True)
    training_status_enum.create(op.get_bind(), checkfirst=True)

    if not _table_exists("vision_training_jobs"):
        _create_vision_training_jobs_table()
    _ensure_vision_training_jobs_indexes()

    if not _table_exists("vision_training_logs"):
        _create_vision_training_logs_table()
    _ensure_vision_training_logs_indexes()

    _enable_tenant_rls("vision_training_jobs")
    _enable_tenant_rls("vision_training_logs")


def downgrade() -> None:
    _disable_tenant_rls("vision_training_logs")
    _disable_tenant_rls("vision_training_jobs")

    op.drop_index("ix_vision_training_logs_event_type", table_name="vision_training_logs")
    op.drop_index("ix_vision_training_logs_job_id", table_name="vision_training_logs")
    op.drop_index("ix_vision_training_logs_organization_id", table_name="vision_training_logs")
    op.drop_index(op.f("ix_vision_training_logs_id"), table_name="vision_training_logs")
    op.drop_table("vision_training_logs")

    op.drop_index("ix_vision_training_jobs_status", table_name="vision_training_jobs")
    op.drop_index("ix_vision_training_jobs_dataset_id", table_name="vision_training_jobs")
    op.drop_index("ix_vision_training_jobs_organization_id", table_name="vision_training_jobs")
    op.drop_index("ix_vision_training_jobs_job_code", table_name="vision_training_jobs")
    op.drop_index(op.f("ix_vision_training_jobs_id"), table_name="vision_training_jobs")
    op.drop_table("vision_training_jobs")

    training_status_enum.drop(op.get_bind(), checkfirst=True)