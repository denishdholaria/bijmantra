"""Migrate Integer identity keys to BigInteger for enterprise scale.

Revision ID: 20260506_0100
Revises: 20260430_0200
Create Date: 2026-05-06 01:00:00.000000

Rationale (ADR-018)
-------------------
Integer (INT4) primary keys cap at ~2.1 billion rows per table.
At enterprise scale — multi-tenant, multi-region, high-frequency
observation and telemetry data — this ceiling is reachable.

BigInteger (INT8 / BIGSERIAL) raises the ceiling to ~9.2 quintillion
rows, which is effectively unlimited, while preserving:
  - Sequential insert order (B-tree friendly, no index fragmentation)
  - Fast joins (8-byte integer, still the fastest FK type)
  - Full compatibility with existing queries and ORM code
  - PostgreSQL SEQUENCE semantics (no distributed coordination needed)

Strategy
--------
1. Collect ALL FK constraints and RLS policies
2. Drop all FK constraints
3. Drop all RLS policies (PostgreSQL blocks ALTER COLUMN on policy-referenced cols)
4. Widen all INTEGER primary-key and foreign-key identity columns to BIGINT
5. Widen backing sequences
6. Recreate all RLS policies
7. Recreate all FK constraints
"""

from contextlib import suppress

from alembic import op
import sqlalchemy as sa

revision = "20260506_0100"
down_revision = "20260430_0200"
branch_labels = None
depends_on = None


def _exec_safe(conn, sql: str) -> bool:
    """Execute optional DDL without poisoning the rest of the migration.

    Earlier extension migrations can leave PostgreSQL outside an explicit
    transaction even when SQLAlchemy still reports an active transaction. Use
    database-level savepoints directly so optional drops/recreates can fail
    safely in either state.
    """
    savepoint_name = "bijmantra_bigint_migration_sp"
    try:
        conn.exec_driver_sql(f"SAVEPOINT {savepoint_name}")
    except Exception:
        with suppress(Exception):
            conn.exec_driver_sql("BEGIN")
        try:
            conn.exec_driver_sql(f"SAVEPOINT {savepoint_name}")
        except Exception:
            with suppress(Exception):
                conn.rollback()
            return False

    try:
        conn.execute(sa.text(sql))
        conn.exec_driver_sql(f"RELEASE SAVEPOINT {savepoint_name}")
        return True
    except Exception:
        with suppress(Exception):
            conn.exec_driver_sql(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
        with suppress(Exception):
            conn.exec_driver_sql(f"RELEASE SAVEPOINT {savepoint_name}")
        return False


def _get_all_fk_constraints(conn) -> list[dict]:
    """Return ALL FK constraints in the public schema."""
    result = conn.execute(sa.text("""
        SELECT
            tc.constraint_name,
            tc.table_name        AS fk_table,
            kcu.column_name      AS fk_col,
            ccu.table_name       AS ref_table,
            ccu.column_name      AS ref_col,
            rc.delete_rule       AS on_delete,
            rc.update_rule       AS on_update
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema   = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema   = tc.table_schema
        JOIN information_schema.referential_constraints rc
            ON rc.constraint_name    = tc.constraint_name
            AND rc.constraint_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema    = 'public'
        ORDER BY tc.table_name, kcu.column_name
    """))
    return [dict(r._mapping) for r in result.fetchall()]


def _get_all_rls_policies(conn) -> list[dict]:
    """Return ALL RLS policies in the public schema."""
    result = conn.execute(sa.text("""
        SELECT
            tablename,
            policyname,
            permissive,
            roles,
            cmd,
            qual,
            with_check
        FROM pg_policies
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname
    """))
    return [dict(r._mapping) for r in result.fetchall()]


def _get_blocking_views(conn) -> list[dict]:
    """
    Return views in non-system schemas that reference public.organizations
    or public.users (the two tables whose id columns are blocked by views).
    """
    result = conn.execute(sa.text("""
        SELECT schemaname, viewname, definition
        FROM pg_views
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema',
                                  '_timescaledb_config', '_timescaledb_internal',
                                  'timescaledb_experimental', 'timescaledb_information')
          AND (definition ILIKE '%FROM organizations%'
               OR definition ILIKE '%FROM users%'
               OR definition ILIKE '% organizations %'
               OR definition ILIKE '% users %')
        ORDER BY schemaname, viewname
    """))
    return [dict(r._mapping) for r in result.fetchall()]


def _get_identity_columns(conn, data_type: str) -> list[tuple[str, str]]:
    """Primary-key and foreign-key identity columns with the requested type."""
    pg_type = {
        "integer": "int4",
        "bigint": "int8",
    }[data_type]

    result = conn.execute(sa.text("""
        SELECT DISTINCT
            cls.relname AS table_name,
            att.attname AS column_name
        FROM pg_attribute att
        JOIN pg_class cls
          ON cls.oid = att.attrelid
        JOIN pg_namespace nsp
          ON nsp.oid = cls.relnamespace
        JOIN pg_type typ
          ON typ.oid = att.atttypid
        LEFT JOIN pg_constraint con
          ON con.conrelid = cls.oid
         AND att.attnum = ANY(con.conkey)
         AND con.contype IN ('p', 'f')
        WHERE nsp.nspname = 'public'
          AND cls.relkind IN ('r', 'p')
          AND att.attnum > 0
          AND NOT att.attisdropped
          AND typ.typname = :pg_type
          AND (
                att.attname IN ('id', 'organization_id', 'user_id')
             OR con.oid IS NOT NULL
          )
        ORDER BY cls.relname, att.attname
    """), {"pg_type": pg_type})
    return result.fetchall()


def _get_integer_columns(conn) -> list[tuple[str, str]]:
    return _get_identity_columns(conn, "integer")


def _get_bigint_columns(conn) -> list[tuple[str, str]]:
    return _get_identity_columns(conn, "bigint")


def _recreate_policy(conn, p: dict) -> bool:
    """Recreate a single RLS policy from its pg_policies row."""
    permissive = "PERMISSIVE" if p["permissive"] == "PERMISSIVE" else "RESTRICTIVE"
    cmd = p["cmd"] if p["cmd"] != "ALL" else "ALL"

    # roles: pg_policies returns a list like {public} or {app_user,readonly}
    roles_raw = p["roles"]
    if isinstance(roles_raw, list):
        roles = ", ".join(roles_raw)
    else:
        # strip braces from string representation
        roles = str(roles_raw).strip("{}")

    sql = (
        f'CREATE POLICY "{p["policyname"]}" ON "{p["tablename"]}" '
        f"AS {permissive} FOR {cmd} TO {roles}"
    )
    if p["qual"]:
        sql += f" USING ({p['qual']})"
    if p["with_check"]:
        sql += f" WITH CHECK ({p['with_check']})"

    return _exec_safe(conn, sql)


def upgrade() -> None:
    conn = op.get_bind()

    # ── Step 1: Snapshot all FK constraints, RLS policies, and views ──────
    all_fks = _get_all_fk_constraints(conn)
    all_policies = _get_all_rls_policies(conn)
    blocking_views = _get_blocking_views(conn)
    cols = _get_integer_columns(conn)

    # ── Step 2: Drop blocking views ───────────────────────────────────────
    # Views referencing organizations/users block ALTER COLUMN on those tables.
    for v in blocking_views:
        _exec_safe(
            conn,
            f'DROP VIEW IF EXISTS "{v["schemaname"]}"."{v["viewname"]}" CASCADE'
        )

    # ── Step 3: Drop all FK constraints ───────────────────────────────────
    for fk in all_fks:
        _exec_safe(
            conn,
            f'ALTER TABLE "{fk["fk_table"]}" '
            f'DROP CONSTRAINT IF EXISTS "{fk["constraint_name"]}"'
        )

    # ── Step 4: Drop all RLS policies ─────────────────────────────────────
    for p in all_policies:
        _exec_safe(
            conn,
            f'DROP POLICY IF EXISTS "{p["policyname"]}" ON "{p["tablename"]}"'
        )

    # Step 5: Widen integer PK/FK identity columns.
    widened = 0
    for table, column in cols:
        ok = _exec_safe(
            conn,
            f'ALTER TABLE "{table}" ALTER COLUMN "{column}" TYPE BIGINT'
        )
        if ok:
            widened += 1

    # ── Step 6: Widen backing sequences ───────────────────────────────────
    id_tables = [t for t, c in cols if c == "id"]
    for table in id_tables:
        _exec_safe(conn, f"ALTER SEQUENCE IF EXISTS {table}_id_seq AS BIGINT")

    # ── Step 7: Recreate all RLS policies ─────────────────────────────────
    rls_recreated = sum(_recreate_policy(conn, p) for p in all_policies)

    # ── Step 8: Recreate all FK constraints ───────────────────────────────
    fk_recreated = 0
    for fk in all_fks:
        on_delete = fk["on_delete"].replace("_", " ")
        on_update = fk["on_update"].replace("_", " ")
        ok = _exec_safe(
            conn,
            f'ALTER TABLE "{fk["fk_table"]}" '
            f'ADD CONSTRAINT "{fk["constraint_name"]}" '
            f'FOREIGN KEY ("{fk["fk_col"]}") '
            f'REFERENCES "{fk["ref_table"]}" ("{fk["ref_col"]}") '
            f'ON DELETE {on_delete} ON UPDATE {on_update}'
        )
        if ok:
            fk_recreated += 1

    # ── Step 9: Recreate blocking views ───────────────────────────────────
    views_recreated = 0
    for v in blocking_views:
        # Normalize the definition: pg_views stores it without CREATE VIEW header
        defn = v["definition"].strip().rstrip(";")
        ok = _exec_safe(
            conn,
            f'CREATE OR REPLACE VIEW "{v["schemaname"]}"."{v["viewname"]}" AS {defn}'
        )
        if ok:
            views_recreated += 1

    print(
        f"  BigInt migration: {widened} columns widened | "
        f"{len(all_fks)} FKs dropped → {fk_recreated} recreated | "
        f"{len(all_policies)} RLS policies dropped → {rls_recreated} recreated | "
        f"{len(blocking_views)} views dropped → {views_recreated} recreated"
    )


def downgrade() -> None:
    conn = op.get_bind()

    all_fks = _get_all_fk_constraints(conn)
    all_policies = _get_all_rls_policies(conn)
    blocking_views = _get_blocking_views(conn)
    cols = _get_bigint_columns(conn)

    for v in blocking_views:
        _exec_safe(
            conn,
            f'DROP VIEW IF EXISTS "{v["schemaname"]}"."{v["viewname"]}" CASCADE'
        )

    for fk in all_fks:
        _exec_safe(
            conn,
            f'ALTER TABLE "{fk["fk_table"]}" '
            f'DROP CONSTRAINT IF EXISTS "{fk["constraint_name"]}"'
        )

    for p in all_policies:
        _exec_safe(
            conn,
            f'DROP POLICY IF EXISTS "{p["policyname"]}" ON "{p["tablename"]}"'
        )

    for table, column in cols:
        _exec_safe(
            conn,
            f'ALTER TABLE "{table}" ALTER COLUMN "{column}" TYPE INTEGER'
        )

    id_tables = [t for t, c in cols if c == "id"]
    for table in id_tables:
        _exec_safe(conn, f"ALTER SEQUENCE IF EXISTS {table}_id_seq AS INTEGER")

    for p in all_policies:
        _recreate_policy(conn, p)

    for fk in all_fks:
        on_delete = fk["on_delete"].replace("_", " ")
        on_update = fk["on_update"].replace("_", " ")
        _exec_safe(
            conn,
            f'ALTER TABLE "{fk["fk_table"]}" '
            f'ADD CONSTRAINT "{fk["constraint_name"]}" '
            f'FOREIGN KEY ("{fk["fk_col"]}") '
            f'REFERENCES "{fk["ref_table"]}" ("{fk["ref_col"]}") '
            f'ON DELETE {on_delete} ON UPDATE {on_update}'
        )

    for v in blocking_views:
        defn = v["definition"].strip().rstrip(";")
        _exec_safe(
            conn,
            f'CREATE OR REPLACE VIEW "{v["schemaname"]}"."{v["viewname"]}" AS {defn}'
        )
