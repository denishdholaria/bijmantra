#!/usr/bin/env python3
"""Fail-fast drift guard for tenant Row-Level Security coverage.

This script checks the live PostgreSQL catalog for every public table with an
``organization_id`` column. Those tables must have RLS enabled, RLS forced, and
be registered in ``app.core.rls.RLS_ENABLED_TABLES`` so generated policy SQL does
not silently fall behind the schema.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import psycopg2


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.rls import RLS_ENABLED_TABLES  # noqa: E402


@dataclass(frozen=True)
class RlsTableState:
    table_name: str
    rls_enabled: bool
    rls_forced: bool


@dataclass(frozen=True)
class RlsDriftReport:
    tenant_tables: int
    registered_tables: int
    missing_rls_enabled: list[str]
    missing_rls_forced: list[str]
    unregistered_tenant_tables: list[str]
    registered_tables_missing_from_db: list[str]

    @property
    def has_failures(self) -> bool:
        return bool(
            self.missing_rls_enabled or self.missing_rls_forced or self.unregistered_tenant_tables
        )


def get_dsn() -> str:
    dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    if not dsn:
        raise RuntimeError("Set DATABASE_URL or POSTGRES_DSN before running check_rls_drift.py")
    return dsn


def fetch_tenant_table_states(conn) -> list[RlsTableState]:
    query = """
    SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r', 'p')
      AND EXISTS (
          SELECT 1
          FROM information_schema.columns col
          WHERE col.table_schema = 'public'
            AND col.table_name = c.relname
            AND col.column_name = 'organization_id'
      )
    ORDER BY c.relname;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return [
            RlsTableState(
                table_name=str(row[0]),
                rls_enabled=bool(row[1]),
                rls_forced=bool(row[2]),
            )
            for row in cur.fetchall()
        ]


def classify_rls_drift(
    table_states: Iterable[RlsTableState],
    registered_tables: Iterable[str] = RLS_ENABLED_TABLES,
) -> RlsDriftReport:
    states = list(table_states)
    tenant_table_names = {state.table_name for state in states}
    registered_table_names = set(registered_tables)

    return RlsDriftReport(
        tenant_tables=len(tenant_table_names),
        registered_tables=len(registered_table_names),
        missing_rls_enabled=sorted(state.table_name for state in states if not state.rls_enabled),
        missing_rls_forced=sorted(state.table_name for state in states if not state.rls_forced),
        unregistered_tenant_tables=sorted(tenant_table_names - registered_table_names),
        registered_tables_missing_from_db=sorted(registered_table_names - tenant_table_names),
    )


def render_report(report: RlsDriftReport) -> str:
    lines = [
        "[RLS] Tenant table drift guard",
        f"  tenant tables in DB: {report.tenant_tables}",
        f"  registered RLS tables: {report.registered_tables}",
    ]

    failures = [
        ("RLS disabled", report.missing_rls_enabled),
        ("RLS not forced", report.missing_rls_forced),
        ("tenant tables missing from RLS registry", report.unregistered_tenant_tables),
    ]
    warnings = [
        (
            "registered tables missing from current DB",
            report.registered_tables_missing_from_db,
        )
    ]

    for title, items in failures:
        lines.append(f"  {title}: {len(items)}")
        for item in items[:50]:
            lines.append(f"    - {item}")
        if len(items) > 50:
            lines.append(f"    - ... {len(items) - 50} more")

    for title, items in warnings:
        lines.append(f"  warning - {title}: {len(items)}")
        for item in items[:25]:
            lines.append(f"    - {item}")
        if len(items) > 25:
            lines.append(f"    - ... {len(items) - 25} more")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    with psycopg2.connect(get_dsn()) as conn:
        report = classify_rls_drift(fetch_tenant_table_states(conn))

    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(render_report(report))

    return 1 if report.has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
