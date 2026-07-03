"""Add reevu_domain_prototypes table for semantic domain detection.

Revision ID: 20260430_0200
Revises: 20260430_0100
Create Date: 2026-04-30 02:00:00.000000

Purpose
-------
Stores pre-computed prototype embeddings for each REEVU domain.
At startup, DomainEmbeddingService embeds all domain corpus examples,
computes the mean embedding per domain, and upserts into this table.

At query time, the user message is embedded and compared against all
domain prototypes using cosine similarity via pgvector. Domains with
similarity >= threshold are included in the execution plan.

The IVFFlat index (lists=10) is sized for the 13 registered domains.
IVFFlat requires at least `lists` rows to be useful; 10 is appropriate
for a small, fixed-size prototype table.
"""

import sqlalchemy as sa
from alembic import op


revision = "20260430_0200"
down_revision = "20260430_0100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgvector extension is available (idempotent — already enabled by 003)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "reevu_domain_prototypes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("example_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain", name="uq_reevu_domain_prototypes_domain"),
    )

    # Add pgvector column — must be done via raw SQL (same pattern as 003_add_vector_store.py)
    op.execute(
        "ALTER TABLE reevu_domain_prototypes ADD COLUMN embedding vector(384) NOT NULL"
    )

    # IVFFlat index for cosine similarity search.
    # lists=10 is appropriate for 13 domains (one prototype per domain).
    op.execute(
        """
        CREATE INDEX ix_reevu_domain_prototypes_embedding
        ON reevu_domain_prototypes
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10)
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_reevu_domain_prototypes_embedding"
    )
    op.drop_table("reevu_domain_prototypes")
    # Note: pgvector extension is not dropped — other tables depend on it
