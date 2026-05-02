"""Create integrations table with pgcrypto-encrypted credential storage.

Revision ID: 20260423_0200
Revises: 20260423_0100
Create Date: 2026-04-23 02:00:00.000000

This migration creates the `integrations` table for the IntegrationHubService,
which previously used in-memory storage. Credentials are stored as bytea using
pgp_sym_encrypt() — the encryption key is injected as a PostgreSQL session
variable (app.encryption_key) at connection time via a SQLAlchemy event listener.

No data migration is required: the service was in-memory, so there are no
existing rows to carry over.
"""

from alembic import op
import sqlalchemy as sa

from app.core.rls import generate_rls_policy_sql


revision = "20260423_0200"
down_revision = "20260423_0100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("integration_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        # bytea column — stores pgp_sym_encrypt() output
        sa.Column("credentials_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="pending"),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Single-column indexes
    op.create_index(
        op.f("ix_integrations_id"),
        "integrations",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integrations_organization_id"),
        "integrations",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integrations_user_id"),
        "integrations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integrations_integration_type"),
        "integrations",
        ["integration_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_integrations_status"),
        "integrations",
        ["status"],
        unique=False,
    )

    # Composite indexes for common query patterns
    op.create_index(
        "ix_integrations_org_user",
        "integrations",
        ["organization_id", "user_id"],
        unique=False,
    )
    op.create_index(
        "ix_integrations_org_type",
        "integrations",
        ["organization_id", "integration_type"],
        unique=False,
    )

    # Row-level security — tenant isolation by organization_id
    op.execute(generate_rls_policy_sql("integrations"))


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS integrations_tenant_isolation ON integrations;")

    op.drop_index("ix_integrations_org_type", table_name="integrations")
    op.drop_index("ix_integrations_org_user", table_name="integrations")
    op.drop_index(op.f("ix_integrations_status"), table_name="integrations")
    op.drop_index(op.f("ix_integrations_integration_type"), table_name="integrations")
    op.drop_index(op.f("ix_integrations_user_id"), table_name="integrations")
    op.drop_index(op.f("ix_integrations_organization_id"), table_name="integrations")
    op.drop_index(op.f("ix_integrations_id"), table_name="integrations")

    op.drop_table("integrations")
