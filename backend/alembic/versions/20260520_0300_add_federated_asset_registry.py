"""Add federated asset registry dry-run tables.

Revision ID: 20260520_0300
Revises: 20260520_0200
Create Date: 2026-05-20 03:00:00.000000
"""

import sqlalchemy as sa

from alembic import op


revision = "20260520_0300"
down_revision = "20260520_0200"
branch_labels = None
depends_on = None


TABLES = (
    "federated_asset_connectors",
    "federated_asset_records",
    "federated_asset_sync_receipts",
)


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _enable_tenant_rls(table_name: str) -> None:
    if not _is_postgresql():
        return
    op.execute(
        f"""
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
        """
    )


def _disable_tenant_rls(table_name: str) -> None:
    if not _is_postgresql():
        return
    op.execute(
        f"""
        DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name};
        ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;
        """
    )


def upgrade() -> None:
    op.create_table(
        "federated_asset_connectors",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("connector_key", sa.String(length=128), nullable=False),
        sa.Column("connector_type", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("endpoint_url", sa.String(length=1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("auth_mode", sa.String(length=64), nullable=False, server_default="none"),
        sa.Column("capabilities", sa.JSON(), nullable=True),
        sa.Column("standards", sa.JSON(), nullable=True),
        sa.Column("governance", sa.JSON(), nullable=True),
        sa.Column(
            "schema_version",
            sa.String(length=32),
            nullable=False,
            server_default="federated_connector.v1",
        ),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "connector_key",
            name="uq_federated_asset_connectors_org_key",
        ),
    )
    op.create_index(
        op.f("ix_federated_asset_connectors_organization_id"),
        "federated_asset_connectors",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_connectors_connector_key"),
        "federated_asset_connectors",
        ["connector_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_connectors_connector_type"),
        "federated_asset_connectors",
        ["connector_type"],
        unique=False,
    )
    op.create_index(
        "ix_federated_asset_connectors_org_type",
        "federated_asset_connectors",
        ["organization_id", "connector_type"],
        unique=False,
    )
    op.create_index(
        "ix_federated_asset_connectors_org_enabled",
        "federated_asset_connectors",
        ["organization_id", "enabled"],
        unique=False,
    )

    op.create_table(
        "federated_asset_records",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("connector_id", sa.Integer(), nullable=False),
        sa.Column("registry_asset_id", sa.String(length=128), nullable=False),
        sa.Column("external_asset_id", sa.String(length=512), nullable=False),
        sa.Column("asset_kind", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_uri", sa.String(length=1000), nullable=True),
        sa.Column("source_digest", sa.String(length=128), nullable=True),
        sa.Column("license", sa.String(length=255), nullable=True),
        sa.Column("data_standard", sa.String(length=255), nullable=True),
        sa.Column("standards_mappings", sa.JSON(), nullable=True),
        sa.Column("fair_metadata_id", sa.Integer(), nullable=True),
        sa.Column("asset_metadata", sa.JSON(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column(
            "schema_version",
            sa.String(length=32),
            nullable=False,
            server_default="federated_asset_record.v1",
        ),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["fair_metadata_id"], ["fair_asset_metadata.id"]),
        sa.ForeignKeyConstraint(["connector_id"], ["federated_asset_connectors.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "connector_id",
            "external_asset_id",
            name="uq_federated_asset_records_org_connector_external",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "registry_asset_id",
            name="uq_federated_asset_records_org_registry_id",
        ),
    )
    op.create_index(
        op.f("ix_federated_asset_records_organization_id"),
        "federated_asset_records",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_records_connector_id"),
        "federated_asset_records",
        ["connector_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_records_registry_asset_id"),
        "federated_asset_records",
        ["registry_asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_records_external_asset_id"),
        "federated_asset_records",
        ["external_asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_records_asset_kind"),
        "federated_asset_records",
        ["asset_kind"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_records_source_digest"),
        "federated_asset_records",
        ["source_digest"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_records_fair_metadata_id"),
        "federated_asset_records",
        ["fair_metadata_id"],
        unique=False,
    )
    op.create_index(
        "ix_federated_asset_records_org_kind",
        "federated_asset_records",
        ["organization_id", "asset_kind"],
        unique=False,
    )
    op.create_index(
        "ix_federated_asset_records_org_connector",
        "federated_asset_records",
        ["organization_id", "connector_id"],
        unique=False,
    )

    op.create_table(
        "federated_asset_sync_receipts",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("connector_id", sa.Integer(), nullable=False),
        sa.Column("receipt_id", sa.String(length=128), nullable=False),
        sa.Column("run_mode", sa.String(length=32), nullable=False, server_default="dry_run"),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("source_digest", sa.String(length=128), nullable=True),
        sa.Column("discovered_asset_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("registered_asset_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_asset_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.Column("manifest_snapshot", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "schema_version",
            sa.String(length=32),
            nullable=False,
            server_default="federated_sync_receipt.v1",
        ),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["connector_id"], ["federated_asset_connectors.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "receipt_id",
            name="uq_federated_asset_sync_receipts_org_receipt",
        ),
    )
    op.create_index(
        op.f("ix_federated_asset_sync_receipts_organization_id"),
        "federated_asset_sync_receipts",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_sync_receipts_connector_id"),
        "federated_asset_sync_receipts",
        ["connector_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_sync_receipts_receipt_id"),
        "federated_asset_sync_receipts",
        ["receipt_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_sync_receipts_status"),
        "federated_asset_sync_receipts",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_federated_asset_sync_receipts_source_digest"),
        "federated_asset_sync_receipts",
        ["source_digest"],
        unique=False,
    )
    op.create_index(
        "ix_federated_asset_sync_receipts_org_connector",
        "federated_asset_sync_receipts",
        ["organization_id", "connector_id"],
        unique=False,
    )
    op.create_index(
        "ix_federated_asset_sync_receipts_org_created",
        "federated_asset_sync_receipts",
        ["organization_id", "created_at"],
        unique=False,
    )

    for table_name in TABLES:
        _enable_tenant_rls(table_name)


def downgrade() -> None:
    for table_name in reversed(TABLES):
        _disable_tenant_rls(table_name)

    op.drop_index(
        "ix_federated_asset_sync_receipts_org_created",
        table_name="federated_asset_sync_receipts",
    )
    op.drop_index(
        "ix_federated_asset_sync_receipts_org_connector",
        table_name="federated_asset_sync_receipts",
    )
    op.drop_index(
        op.f("ix_federated_asset_sync_receipts_source_digest"),
        table_name="federated_asset_sync_receipts",
    )
    op.drop_index(
        op.f("ix_federated_asset_sync_receipts_status"),
        table_name="federated_asset_sync_receipts",
    )
    op.drop_index(
        op.f("ix_federated_asset_sync_receipts_receipt_id"),
        table_name="federated_asset_sync_receipts",
    )
    op.drop_index(
        op.f("ix_federated_asset_sync_receipts_connector_id"),
        table_name="federated_asset_sync_receipts",
    )
    op.drop_index(
        op.f("ix_federated_asset_sync_receipts_organization_id"),
        table_name="federated_asset_sync_receipts",
    )
    op.drop_table("federated_asset_sync_receipts")

    op.drop_index("ix_federated_asset_records_org_connector", table_name="federated_asset_records")
    op.drop_index("ix_federated_asset_records_org_kind", table_name="federated_asset_records")
    op.drop_index(
        op.f("ix_federated_asset_records_fair_metadata_id"),
        table_name="federated_asset_records",
    )
    op.drop_index(op.f("ix_federated_asset_records_source_digest"), table_name="federated_asset_records")
    op.drop_index(op.f("ix_federated_asset_records_asset_kind"), table_name="federated_asset_records")
    op.drop_index(
        op.f("ix_federated_asset_records_external_asset_id"),
        table_name="federated_asset_records",
    )
    op.drop_index(
        op.f("ix_federated_asset_records_registry_asset_id"),
        table_name="federated_asset_records",
    )
    op.drop_index(op.f("ix_federated_asset_records_connector_id"), table_name="federated_asset_records")
    op.drop_index(
        op.f("ix_federated_asset_records_organization_id"),
        table_name="federated_asset_records",
    )
    op.drop_table("federated_asset_records")

    op.drop_index(
        "ix_federated_asset_connectors_org_enabled",
        table_name="federated_asset_connectors",
    )
    op.drop_index(
        "ix_federated_asset_connectors_org_type",
        table_name="federated_asset_connectors",
    )
    op.drop_index(
        op.f("ix_federated_asset_connectors_connector_type"),
        table_name="federated_asset_connectors",
    )
    op.drop_index(
        op.f("ix_federated_asset_connectors_connector_key"),
        table_name="federated_asset_connectors",
    )
    op.drop_index(
        op.f("ix_federated_asset_connectors_organization_id"),
        table_name="federated_asset_connectors",
    )
    op.drop_table("federated_asset_connectors")
