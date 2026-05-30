"""Add external authentication identity mappings.

Revision ID: 20260514_0100
Revises: 20260512_0100
Create Date: 2026-05-14 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260514_0100"
down_revision = "20260512_0100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_identities",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(length=50), server_default="keycloak", nullable=False),
        sa.Column("issuer", sa.String(length=512), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("email_at_login", sa.String(length=255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "issuer",
            "subject",
            name="uq_auth_identities_provider_issuer_subject",
        ),
    )
    op.create_index(op.f("ix_auth_identities_id"), "auth_identities", ["id"], unique=False)
    op.create_index(
        op.f("ix_auth_identities_organization_id"),
        "auth_identities",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_identities_provider"),
        "auth_identities",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_identities_user_id"),
        "auth_identities",
        ["user_id"],
        unique=False,
    )
    op.execute(
        """
        ALTER TABLE auth_identities ENABLE ROW LEVEL SECURITY;
        ALTER TABLE auth_identities FORCE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS auth_identities_tenant_isolation ON auth_identities;
        CREATE POLICY auth_identities_tenant_isolation ON auth_identities
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


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS auth_identities_tenant_isolation ON auth_identities;")
    op.drop_index(op.f("ix_auth_identities_user_id"), table_name="auth_identities")
    op.drop_index(op.f("ix_auth_identities_provider"), table_name="auth_identities")
    op.drop_index(op.f("ix_auth_identities_organization_id"), table_name="auth_identities")
    op.drop_index(op.f("ix_auth_identities_id"), table_name="auth_identities")
    op.drop_table("auth_identities")
