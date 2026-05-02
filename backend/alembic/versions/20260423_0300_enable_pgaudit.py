"""Enable pgaudit extension and create bijmantra_auditor role with grants on sensitive tables.

Revision ID: 20260423_0300
Revises: 20260423_0200
Create Date: 2026-04-23 03:00:00.000000

Enables the pgaudit extension (requires shared_preload_libraries = 'pgaudit' in
postgresql.conf, already set in Task 1.2). Creates the bijmantra_auditor role used
by pgaudit.role for object-level auditing, and grants SELECT/INSERT/UPDATE/DELETE
on sensitive tables so pgaudit logs all DML on those tables regardless of which
user or application executes the query.

Audited tables:
  - users              — identity and authentication data
  - organizations      — tenant root; mutations here affect all RLS policies
  - role_permissions   — privilege escalation surface
  - security_audit_log — tamper-resistance: log mutations to the audit log itself
  - audit_logs         — application-level audit trail
"""

from alembic import op


revision = "20260423_0300"
down_revision = "20260423_0200"
branch_labels = None
depends_on = None

AUDITED_TABLES = (
    "users",
    "organizations",
    "role_permissions",
    "security_audit_log",
    "audit_logs",
)


def upgrade() -> None:
    # Enable pgaudit extension
    op.execute("CREATE EXTENSION IF NOT EXISTS pgaudit;")

    # Create the audit role used by pgaudit.role in postgresql.conf.
    # pgaudit will log all DML on tables granted to this role, regardless
    # of which session user performs the operation.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bijmantra_auditor') THEN
                CREATE ROLE bijmantra_auditor;
            END IF;
        END $$;
    """)

    # Grant DML privileges on sensitive tables to the audit role.
    # pgaudit intercepts these grants to determine which object-level
    # operations to log — the role itself never connects to the database.
    for table_name in AUDITED_TABLES:
        _grant_if_table_exists(table_name)

    # Set pgaudit.role via ALTER SYSTEM so it persists across restarts.
    # This must happen AFTER the role is created above.
    with op.get_context().autocommit_block():
        op.execute("ALTER SYSTEM SET pgaudit.role = 'bijmantra_auditor';")
    # Reload config so the setting takes effect immediately
    op.execute("SELECT pg_reload_conf();")


def downgrade() -> None:
    # Reset pgaudit.role before dropping the role
    with op.get_context().autocommit_block():
        op.execute("ALTER SYSTEM RESET pgaudit.role;")
    op.execute("SELECT pg_reload_conf();")

    # Revoke all grants before dropping the role
    for table_name in AUDITED_TABLES:
        _revoke_if_table_exists(table_name)

    # Drop the audit role
    op.execute("DROP ROLE IF EXISTS bijmantra_auditor;")

    # Drop the extension
    op.execute("DROP EXTENSION IF EXISTS pgaudit;")


def _grant_if_table_exists(table_name: str) -> None:
    op.execute(f"""
        DO $$
        BEGIN
            IF to_regclass('public.{table_name}') IS NOT NULL THEN
                GRANT SELECT, INSERT, UPDATE, DELETE
                ON TABLE public.{table_name}
                TO bijmantra_auditor;
            END IF;
        END $$;
    """)


def _revoke_if_table_exists(table_name: str) -> None:
    op.execute(f"""
        DO $$
        BEGIN
            IF to_regrole('bijmantra_auditor') IS NOT NULL
               AND to_regclass('public.{table_name}') IS NOT NULL THEN
                REVOKE ALL
                ON TABLE public.{table_name}
                FROM bijmantra_auditor;
            END IF;
        END $$;
    """)
