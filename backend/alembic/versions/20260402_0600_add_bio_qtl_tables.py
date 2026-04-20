"""Add bio QTL persistence tables.

Revision ID: 20260402_0600
Revises: 20260331_1500
Create Date: 2026-04-02 06:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

from app.core.rls import generate_rls_policy_sql


revision = "20260402_0600"
down_revision = "20260331_1500"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bio_qtls",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("qtl_db_id", sa.String(length=255), nullable=True),
        sa.Column("qtl_name", sa.String(length=255), nullable=True),
        sa.Column("trait", sa.String(length=255), nullable=False),
        sa.Column("population", sa.String(length=255), nullable=True),
        sa.Column("method", sa.String(length=50), nullable=True),
        sa.Column("chromosome", sa.String(length=50), nullable=False),
        sa.Column("start_position", sa.Float(), nullable=True),
        sa.Column("end_position", sa.Float(), nullable=True),
        sa.Column("peak_position", sa.Float(), nullable=True),
        sa.Column("lod", sa.Float(), nullable=True),
        sa.Column("lod_score", sa.Float(), nullable=True),
        sa.Column("pve", sa.Float(), nullable=True),
        sa.Column("add_effect", sa.Float(), nullable=True),
        sa.Column("dom_effect", sa.Float(), nullable=True),
        sa.Column("marker_name", sa.String(length=255), nullable=True),
        sa.Column("confidence_interval_low", sa.Float(), nullable=True),
        sa.Column("confidence_interval_high", sa.Float(), nullable=True),
        sa.Column("analysis_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("candidate_genes", sa.JSON(), nullable=True),
        sa.Column("additional_info", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bio_qtls_id"), "bio_qtls", ["id"], unique=False)
    op.create_index(
        op.f("ix_bio_qtls_organization_id"),
        "bio_qtls",
        ["organization_id"],
        unique=False,
    )
    op.create_index(op.f("ix_bio_qtls_qtl_db_id"), "bio_qtls", ["qtl_db_id"], unique=True)
    op.create_index(op.f("ix_bio_qtls_qtl_name"), "bio_qtls", ["qtl_name"], unique=False)
    op.create_index(op.f("ix_bio_qtls_trait"), "bio_qtls", ["trait"], unique=False)
    op.create_index(op.f("ix_bio_qtls_chromosome"), "bio_qtls", ["chromosome"], unique=False)

    op.create_table(
        "bio_candidate_genes",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("qtl_id", sa.Integer(), nullable=False),
        sa.Column("gene_id", sa.String(length=255), nullable=False),
        sa.Column("gene_name", sa.String(length=255), nullable=True),
        sa.Column("chromosome", sa.String(length=50), nullable=True),
        sa.Column("start_position", sa.Integer(), nullable=True),
        sa.Column("end_position", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("go_terms", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["qtl_id"], ["bio_qtls.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_bio_candidate_genes_id"),
        "bio_candidate_genes",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bio_candidate_genes_organization_id"),
        "bio_candidate_genes",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bio_candidate_genes_qtl_id"),
        "bio_candidate_genes",
        ["qtl_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bio_candidate_genes_gene_id"),
        "bio_candidate_genes",
        ["gene_id"],
        unique=False,
    )

    op.execute(generate_rls_policy_sql("bio_qtls"))
    op.execute(generate_rls_policy_sql("bio_candidate_genes"))


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS bio_candidate_genes_tenant_isolation ON bio_candidate_genes;")
    op.execute("DROP POLICY IF EXISTS bio_qtls_tenant_isolation ON bio_qtls;")
    op.drop_index(
        op.f("ix_bio_candidate_genes_gene_id"),
        table_name="bio_candidate_genes",
    )
    op.drop_index(
        op.f("ix_bio_candidate_genes_qtl_id"),
        table_name="bio_candidate_genes",
    )
    op.drop_index(
        op.f("ix_bio_candidate_genes_organization_id"),
        table_name="bio_candidate_genes",
    )
    op.drop_index(
        op.f("ix_bio_candidate_genes_id"),
        table_name="bio_candidate_genes",
    )
    op.drop_table("bio_candidate_genes")

    op.drop_index(op.f("ix_bio_qtls_chromosome"), table_name="bio_qtls")
    op.drop_index(op.f("ix_bio_qtls_trait"), table_name="bio_qtls")
    op.drop_index(op.f("ix_bio_qtls_qtl_name"), table_name="bio_qtls")
    op.drop_index(op.f("ix_bio_qtls_qtl_db_id"), table_name="bio_qtls")
    op.drop_index(op.f("ix_bio_qtls_organization_id"), table_name="bio_qtls")
    op.drop_index(op.f("ix_bio_qtls_id"), table_name="bio_qtls")
    op.drop_table("bio_qtls")