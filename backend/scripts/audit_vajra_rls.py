#!/usr/bin/env python3
"""VAJRA RLS audit helper.

Checks:
1) Potential recursive view dependencies.
2) Tenant-isolation coverage for tables containing organization_id.
3) Potential bypass markers in SQL functions/views.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import psycopg


REPO_ROOT = Path(__file__).resolve().parents[2]


def get_conn() -> psycopg.Connection:
    dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    if not dsn:
        raise RuntimeError("Set DATABASE_URL or POSTGRES_DSN before running audit_vajra_rls.py")
    return psycopg.connect(dsn)


def recursive_view_candidates(conn: psycopg.Connection) -> list[tuple[str, str]]:
    query = """
    SELECT v.viewname, pg_get_viewdef(format('%I.%I', v.schemaname, v.viewname)::regclass, true)
    FROM pg_catalog.pg_views v
    WHERE v.schemaname = 'public';
    """
    rows: list[tuple[str, str]] = []
    with conn.cursor() as cur:
        cur.execute(query)
        for viewname, definition in cur.fetchall():
            if re.search(rf"\b{re.escape(viewname)}\b", definition, flags=re.IGNORECASE):
                rows.append((viewname, "self-reference in definition"))
    return rows


def tenant_coverage(conn: psycopg.Connection) -> tuple[int, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*)
            FROM information_schema.columns
            WHERE table_schema='public' AND column_name='organization_id'
            """
        )
        total = int(cur.fetchone()[0])

        cur.execute(
            """
            SELECT count(*)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity = true
            AND EXISTS (
                SELECT 1 FROM information_schema.columns i
                WHERE i.table_schema='public' AND i.table_name=c.relname AND i.column_name='organization_id'
            )
            """
        )
        covered = int(cur.fetchone()[0])
    return covered, total


def bypass_markers() -> list[str]:
    patterns = [r"bypass[_ ]rls", r"SET\s+ROLE\s+postgres", r"SECURITY\s+DEFINER"]
    files = []
    for path in REPO_ROOT.rglob("*.sql"):
        text = path.read_text(errors="ignore")
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            files.append(str(path.relative_to(REPO_ROOT)))
    return sorted(files)


def main() -> None:
    with get_conn() as conn:
        recursive = recursive_view_candidates(conn)
        covered, total = tenant_coverage(conn)

    print("[VAJRA] Recursive view dependency candidates:")
    if not recursive:
        print("  - none detected by heuristic")
    else:
        for view, reason in recursive:
            print(f"  - {view}: {reason}")

    print(f"[VAJRA] Tenant isolation coverage: {covered}/{total} tables with organization_id have RLS enabled")

    markers = bypass_markers()
    print("[VAJRA] Potential bypass markers in SQL files:")
    if not markers:
        print("  - none")
    else:
        for file in markers:
            print(f"  - {file}")


if __name__ == "__main__":
    main()
