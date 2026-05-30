"""Add Plant Vision dataset governance and model lifecycle metadata.

Revision ID: 20260508_0100
Revises: 20260506_0100
Create Date: 2026-05-08 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260508_0100"
down_revision = "20260506_0100"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _column_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    if not _table_exists(table_name):
        return set()
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


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


def _ensure_model_lifecycle_columns() -> None:
    _add_column_if_missing(
        "vision_models",
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False, server_default="candidate"),
    )
    _add_column_if_missing("vision_models", sa.Column("artifact_checksum", sa.String(length=128), nullable=True))
    _add_column_if_missing(
        "vision_models",
        sa.Column("label_mapping", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    _add_column_if_missing(
        "vision_models",
        sa.Column("preprocessing_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    _add_column_if_missing(
        "vision_models",
        sa.Column("training_provenance", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    _add_column_if_missing(
        "vision_models",
        sa.Column("readiness_score", sa.Float(), nullable=False, server_default="0"),
    )
    _add_column_if_missing("vision_models", sa.Column("approved_by", sa.String(), nullable=True))
    _add_column_if_missing("vision_models", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("vision_models", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))


def _create_dataset_versions_table() -> None:
    op.create_table(
        "vision_dataset_versions",
        sa.Column("version_code", sa.String(length=64), nullable=False),
        sa.Column("dataset_id", sa.BigInteger(), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("source_slug", sa.String(length=128), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_license", sa.String(length=128), nullable=False),
        sa.Column("source_license_url", sa.Text(), nullable=True),
        sa.Column("license_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_version", sa.String(length=128), nullable=False, server_default="manual-export"),
        sa.Column("raw_root_uri", sa.Text(), nullable=False),
        sa.Column("source_checksum", sa.String(length=128), nullable=False),
        sa.Column("manifest_checksum", sa.String(length=128), nullable=False),
        sa.Column("preprocessing_version", sa.String(length=128), nullable=False),
        sa.Column("split_seed", sa.Integer(), nullable=False),
        sa.Column("image_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("class_distribution", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("split_distribution", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("canonical_taxonomy", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dataset_id"], ["vision_datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def _create_dataset_audit_logs_table() -> None:
    op.create_table(
        "vision_dataset_audit_logs",
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("dataset_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["dataset_id"], ["vision_datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def _ensure_indexes() -> None:
    indexes = _index_names("vision_dataset_versions")
    if "ix_vision_dataset_versions_version_code" not in indexes:
        op.create_index(
            "ix_vision_dataset_versions_version_code",
            "vision_dataset_versions",
            ["version_code"],
            unique=True,
        )
    if "ix_vision_dataset_versions_dataset_id" not in indexes:
        op.create_index("ix_vision_dataset_versions_dataset_id", "vision_dataset_versions", ["dataset_id"])
    if "ix_vision_dataset_versions_organization_id" not in indexes:
        op.create_index(
            "ix_vision_dataset_versions_organization_id",
            "vision_dataset_versions",
            ["organization_id"],
        )
    if "ix_vision_dataset_versions_source_slug" not in indexes:
        op.create_index("ix_vision_dataset_versions_source_slug", "vision_dataset_versions", ["source_slug"])

    audit_indexes = _index_names("vision_dataset_audit_logs")
    if "ix_vision_dataset_audit_logs_organization_id" not in audit_indexes:
        op.create_index(
            "ix_vision_dataset_audit_logs_organization_id",
            "vision_dataset_audit_logs",
            ["organization_id"],
        )
    if "ix_vision_dataset_audit_logs_dataset_id" not in audit_indexes:
        op.create_index("ix_vision_dataset_audit_logs_dataset_id", "vision_dataset_audit_logs", ["dataset_id"])
    if "ix_vision_dataset_audit_logs_event_type" not in audit_indexes:
        op.create_index("ix_vision_dataset_audit_logs_event_type", "vision_dataset_audit_logs", ["event_type"])


def upgrade() -> None:
    _ensure_model_lifecycle_columns()
    if not _table_exists("vision_dataset_versions"):
        _create_dataset_versions_table()
    if not _table_exists("vision_dataset_audit_logs"):
        _create_dataset_audit_logs_table()
    _ensure_indexes()
    _enable_tenant_rls("vision_dataset_versions")
    _enable_tenant_rls("vision_dataset_audit_logs")


def downgrade() -> None:
    _disable_tenant_rls("vision_dataset_audit_logs")
    _disable_tenant_rls("vision_dataset_versions")
    if _table_exists("vision_dataset_audit_logs"):
        op.drop_table("vision_dataset_audit_logs")
    if _table_exists("vision_dataset_versions"):
        op.drop_table("vision_dataset_versions")
    for column_name in [
        "archived_at",
        "approved_at",
        "approved_by",
        "readiness_score",
        "training_provenance",
        "preprocessing_config",
        "label_mapping",
        "artifact_checksum",
        "lifecycle_state",
    ]:
        if column_name in _column_names("vision_models"):
            op.drop_column("vision_models", column_name)
