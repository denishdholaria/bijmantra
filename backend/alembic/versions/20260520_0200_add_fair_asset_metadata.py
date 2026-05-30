"""Add FAIR asset metadata sidecar.

Revision ID: 20260520_0200
Revises: 20260520_0100
Create Date: 2026-05-20 02:00:00.000000
"""

import sqlalchemy as sa

from alembic import op


revision = "20260520_0200"
down_revision = "20260520_0100"
branch_labels = None
depends_on = None


def _is_postgresql() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _enable_tenant_rls() -> None:
    if not _is_postgresql():
        return
    op.execute(
        """
        ALTER TABLE fair_asset_metadata ENABLE ROW LEVEL SECURITY;
        ALTER TABLE fair_asset_metadata FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS fair_asset_metadata_tenant_isolation ON fair_asset_metadata;
        CREATE POLICY fair_asset_metadata_tenant_isolation ON fair_asset_metadata
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
        """
        DROP POLICY IF EXISTS fair_asset_metadata_tenant_isolation ON fair_asset_metadata;
        ALTER TABLE fair_asset_metadata DISABLE ROW LEVEL SECURITY;
        """
    )


def upgrade() -> None:
    op.create_table(
        "fair_asset_metadata",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("asset_db_id", sa.String(length=255), nullable=False),
        sa.Column("persistent_identifier", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("access_rights", sa.String(length=100), nullable=True),
        sa.Column("license", sa.String(length=255), nullable=True),
        sa.Column("data_standard", sa.String(length=255), nullable=True),
        sa.Column("ontology_terms", sa.JSON(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(length=255), nullable=True),
        sa.Column("contributors", sa.JSON(), nullable=True),
        sa.Column("funding_acknowledgements", sa.JSON(), nullable=True),
        sa.Column("external_references", sa.JSON(), nullable=True),
        sa.Column("evidence_refs", sa.JSON(), nullable=True),
        sa.Column(
            "schema_version",
            sa.String(length=32),
            nullable=False,
            server_default="fair_asset_metadata.v1",
        ),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "asset_type",
            "asset_db_id",
            name="uq_fair_asset_metadata_org_asset",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "persistent_identifier",
            name="uq_fair_asset_metadata_org_pid",
        ),
    )
    op.create_index(
        op.f("ix_fair_asset_metadata_organization_id"),
        "fair_asset_metadata",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fair_asset_metadata_asset_type"),
        "fair_asset_metadata",
        ["asset_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fair_asset_metadata_asset_db_id"),
        "fair_asset_metadata",
        ["asset_db_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fair_asset_metadata_persistent_identifier"),
        "fair_asset_metadata",
        ["persistent_identifier"],
        unique=False,
    )
    op.create_index(
        "ix_fair_asset_metadata_org_type",
        "fair_asset_metadata",
        ["organization_id", "asset_type"],
        unique=False,
    )
    op.create_index(
        "ix_fair_asset_metadata_org_created",
        "fair_asset_metadata",
        ["organization_id", "created_at"],
        unique=False,
    )
    _enable_tenant_rls()


def downgrade() -> None:
    _disable_tenant_rls()
    op.drop_index("ix_fair_asset_metadata_org_created", table_name="fair_asset_metadata")
    op.drop_index("ix_fair_asset_metadata_org_type", table_name="fair_asset_metadata")
    op.drop_index(
        op.f("ix_fair_asset_metadata_persistent_identifier"),
        table_name="fair_asset_metadata",
    )
    op.drop_index(op.f("ix_fair_asset_metadata_asset_db_id"), table_name="fair_asset_metadata")
    op.drop_index(op.f("ix_fair_asset_metadata_asset_type"), table_name="fair_asset_metadata")
    op.drop_index(op.f("ix_fair_asset_metadata_organization_id"), table_name="fair_asset_metadata")
    op.drop_table("fair_asset_metadata")
