"""Add agricultural knowledge graph edge table.

Revision ID: 20260520_0400
Revises: 20260520_0300
Create Date: 2026-05-20 04:00:00.000000
"""

import sqlalchemy as sa

from alembic import op


revision = "20260520_0400"
down_revision = "20260520_0300"
branch_labels = None
depends_on = None


TABLE_NAME = "agricultural_knowledge_graph_edges"


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
        TABLE_NAME,
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("edge_id", sa.String(length=128), nullable=False),
        sa.Column("source_asset_type", sa.String(length=64), nullable=False),
        sa.Column("source_asset_id", sa.String(length=255), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("target_asset_type", sa.String(length=64), nullable=False),
        sa.Column("target_asset_id", sa.String(length=255), nullable=False),
        sa.Column("evidence_refs", sa.JSON(), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("derivation_method", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column(
            "schema_version",
            sa.String(length=32),
            nullable=False,
            server_default="agricultural_knowledge_graph_edge.v1",
        ),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "edge_id",
            name="uq_ag_kg_edges_org_edge_id",
        ),
        sa.UniqueConstraint(
            "organization_id",
            "source_asset_type",
            "source_asset_id",
            "relationship_type",
            "target_asset_type",
            "target_asset_id",
            name="uq_ag_kg_edges_org_relationship",
        ),
    )
    op.create_index(
        op.f("ix_agricultural_knowledge_graph_edges_organization_id"),
        TABLE_NAME,
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agricultural_knowledge_graph_edges_edge_id"),
        TABLE_NAME,
        ["edge_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agricultural_knowledge_graph_edges_source_asset_type"),
        TABLE_NAME,
        ["source_asset_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agricultural_knowledge_graph_edges_source_asset_id"),
        TABLE_NAME,
        ["source_asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agricultural_knowledge_graph_edges_relationship_type"),
        TABLE_NAME,
        ["relationship_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agricultural_knowledge_graph_edges_target_asset_type"),
        TABLE_NAME,
        ["target_asset_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agricultural_knowledge_graph_edges_target_asset_id"),
        TABLE_NAME,
        ["target_asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_ag_kg_edges_org_source",
        TABLE_NAME,
        ["organization_id", "source_asset_type", "source_asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_ag_kg_edges_org_target",
        TABLE_NAME,
        ["organization_id", "target_asset_type", "target_asset_id"],
        unique=False,
    )
    op.create_index(
        "ix_ag_kg_edges_org_relationship",
        TABLE_NAME,
        ["organization_id", "relationship_type"],
        unique=False,
    )
    _enable_tenant_rls(TABLE_NAME)


def downgrade() -> None:
    _disable_tenant_rls(TABLE_NAME)
    op.drop_index("ix_ag_kg_edges_org_relationship", table_name=TABLE_NAME)
    op.drop_index("ix_ag_kg_edges_org_target", table_name=TABLE_NAME)
    op.drop_index("ix_ag_kg_edges_org_source", table_name=TABLE_NAME)
    op.drop_index(op.f("ix_agricultural_knowledge_graph_edges_target_asset_id"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_agricultural_knowledge_graph_edges_target_asset_type"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_agricultural_knowledge_graph_edges_relationship_type"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_agricultural_knowledge_graph_edges_source_asset_id"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_agricultural_knowledge_graph_edges_source_asset_type"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_agricultural_knowledge_graph_edges_edge_id"), table_name=TABLE_NAME)
    op.drop_index(op.f("ix_agricultural_knowledge_graph_edges_organization_id"), table_name=TABLE_NAME)
    op.drop_table(TABLE_NAME)
