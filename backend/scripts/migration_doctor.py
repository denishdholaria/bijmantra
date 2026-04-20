#!/usr/bin/env python3
"""Diagnose local Alembic revision and schema-drift issues for BijMantra."""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
VERSIONS_DIR = BACKEND_DIR / "alembic" / "versions"
REVISION_RE = re.compile(r'^revision\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
DOWN_REVISION_RE = re.compile(r"^down_revision\s*=\s*(.+)$", re.MULTILINE)
MISSING_REVISION_RE = re.compile(r"Can't locate revision identified by ['\"]([^'\"]+)['\"]")
IGNORED_DATABASE_TABLES = {"spatial_ref_sys"}


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _icon(status: str) -> str:
    return {
        "PASS": "[PASS]",
        "WARN": "[WARN]",
        "FAIL": "[FAIL]",
        "SKIP": "[SKIP]",
    }.get(status, "[INFO]")


def print_result(result: CheckResult) -> None:
    print(f"{_icon(result.status)} {result.name}: {result.detail}")


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", ".")
    env.setdefault("POSTGRES_SERVER", "localhost")
    env.setdefault("POSTGRES_PORT", "5432")
    env.setdefault("POSTGRES_USER", "bijmantra_user")
    env.setdefault("POSTGRES_PASSWORD", "changeme_in_production")
    env.setdefault("POSTGRES_DB", "bijmantra_db")
    return subprocess.run(command, cwd=BACKEND_DIR, env=env, capture_output=True, text=True, check=False)


def parse_down_revision(raw_value: str) -> list[str]:
    cleaned = raw_value.split("#", 1)[0].strip()
    try:
        value = ast.literal_eval(cleaned)
    except Exception:
        return []
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item]
    return [str(value)]


def collect_local_revisions() -> tuple[dict[str, Path], dict[str, list[str]], list[CheckResult]]:
    results: list[CheckResult] = []
    revisions: dict[str, Path] = {}
    parents: dict[str, list[str]] = {}
    duplicate_ids: list[str] = []

    if not VERSIONS_DIR.exists():
        results.append(CheckResult("Local revision files", "FAIL", "Missing backend/alembic/versions directory"))
        return revisions, parents, results

    files = sorted(VERSIONS_DIR.glob("*.py"))
    if not files:
        results.append(CheckResult("Local revision files", "FAIL", "No Alembic revision files found"))
        return revisions, parents, results

    for path in files:
        text = path.read_text(encoding="utf-8")
        revision_match = REVISION_RE.search(text)
        if not revision_match:
            results.append(CheckResult("Local revision files", "WARN", f"Could not parse revision id from {path.name}"))
            continue

        revision_id = revision_match.group(1)
        if revision_id in revisions:
            duplicate_ids.append(revision_id)
        revisions[revision_id] = path

        down_revision_match = DOWN_REVISION_RE.search(text)
        parents[revision_id] = parse_down_revision(down_revision_match.group(1)) if down_revision_match else []

    if duplicate_ids:
        results.append(CheckResult("Local revision files", "FAIL", "Duplicate revision ids: " + ", ".join(sorted(set(duplicate_ids)))))
    else:
        results.append(CheckResult("Local revision files", "PASS", f"Parsed {len(revisions)} revision files"))

    missing_parents: list[str] = []
    for revision_id, parent_ids in parents.items():
        for parent_id in parent_ids:
            if parent_id not in revisions:
                missing_parents.append(f"{revision_id} -> {parent_id}")

    if missing_parents:
        results.append(CheckResult("Local revision graph", "FAIL", "Missing parent revisions: " + "; ".join(sorted(missing_parents))))
    else:
        referenced = {parent for parent_ids in parents.values() for parent in parent_ids}
        heads = sorted(revision_id for revision_id in revisions if revision_id not in referenced)
        if len(heads) == 1:
            results.append(CheckResult("Local revision graph", "PASS", f"Single local head detected: {heads[0]}"))
        else:
            results.append(CheckResult("Local revision graph", "WARN", f"Multiple local heads detected: {', '.join(heads)}"))

    return revisions, parents, results


def summarize_command_output(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[0] if lines else "No output"


def summarize_names(names: set[str], limit: int = 6) -> str:
    ordered = sorted(names)
    if not ordered:
        return ""
    visible = ordered[:limit]
    remainder = len(ordered) - len(visible)
    suffix = f", +{remainder} more" if remainder > 0 else ""
    return ", ".join(visible) + suffix


def collect_schema_drift_summary() -> str:
    try:
        from alembic.autogenerate import compare_metadata
        from alembic.migration import MigrationContext
        from sqlalchemy import create_engine
        from sqlalchemy.exc import SAWarning

        from app.core.config import settings
        from app.core.database import Base
        import app.models  # noqa: F401
    except Exception as exc:
        return f"Detailed drift summary unavailable: {exc}"

    add_tables: set[str] = set()
    remove_tables: set[str] = set()
    changed_tables: dict[str, set[str]] = defaultdict(set)

    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            warnings.filterwarnings("ignore", category=SAWarning)
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                diffs = compare_metadata(context, Base.metadata)
    except Exception as exc:
        return f"Detailed drift summary unavailable: {exc}"
    finally:
        engine.dispose()

    for diff in diffs:
        if isinstance(diff, list):
            for nested in diff:
                tag = nested[0]
                if tag.startswith("modify_"):
                    changed_tables[str(nested[2])].add(tag)
            continue

        tag = diff[0]
        if tag == "add_table":
            add_tables.add(diff[1].name)
            continue
        if tag == "remove_table":
            table_name = diff[1].name
            if table_name not in IGNORED_DATABASE_TABLES:
                remove_tables.add(table_name)
            continue

        if tag in {"add_column", "remove_column"}:
            changed_tables[str(diff[2])].add(tag)
            continue

        if tag in {"add_index", "remove_index", "add_fk", "remove_fk", "add_constraint", "remove_constraint"}:
            table = getattr(diff[1], "table", None)
            table_name = getattr(table, "name", None)
            if table_name:
                changed_tables[str(table_name)].add(tag)

    details: list[str] = []
    if add_tables:
        details.append(f"model tables without migrations: {summarize_names(add_tables)}")
    if remove_tables:
        details.append(f"database tables without active ORM models: {summarize_names(remove_tables)}")
    if changed_tables:
        details.append(f"column/index/type drift on: {summarize_names(set(changed_tables))}")

    if details:
        return "; ".join(details)
    return "Detailed diff summary unavailable despite reported drift"


def check_alembic_heads() -> CheckResult:
    result = run_command(["venv/bin/python", "-m", "alembic", "heads"])
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        return CheckResult("Alembic heads", "FAIL", summarize_command_output(output))
    return CheckResult("Alembic heads", "PASS", summarize_command_output(output))


def check_alembic_current() -> CheckResult:
    result = run_command(["venv/bin/python", "-m", "alembic", "current"])
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        missing_revision = MISSING_REVISION_RE.search(output)
        if missing_revision:
            revision_id = missing_revision.group(1)
            return CheckResult(
                "Database revision state",
                "FAIL",
                f"Database references missing revision {revision_id}; align the local migration chain or repair alembic_version safely",
            )
        return CheckResult("Database revision state", "FAIL", summarize_command_output(output))
    return CheckResult("Database revision state", "PASS", summarize_command_output(output))


def check_schema_sync() -> CheckResult:
    result = run_command(["venv/bin/alembic", "check"])
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        if "New upgrade operations detected" in output:
            drift_summary = collect_schema_drift_summary()
            return CheckResult(
                "Schema sync",
                "WARN",
                "Model metadata differs from the current database state; " + drift_summary,
            )
        return CheckResult("Schema sync", "WARN", summarize_command_output(output))
    return CheckResult("Schema sync", "PASS", summarize_command_output(output))


def run_doctor(strict: bool) -> int:
    venv_python = BACKEND_DIR / "venv" / "bin" / "python"
    if not venv_python.exists():
        print_result(CheckResult("Backend virtualenv", "FAIL", "Missing backend/venv; run 'bash ./setup.sh' or 'make install' first"))
        return 1 if strict else 0

    _, _, graph_results = collect_local_revisions()
    command_results = [check_alembic_heads(), check_alembic_current(), check_schema_sync()]
    results = graph_results + command_results

    has_fail = False
    has_warn = False
    for result in results:
        print_result(result)
        has_fail = has_fail or result.status == "FAIL"
        has_warn = has_warn or result.status == "WARN"

    print()
    if has_fail:
        print("Migration doctor found blocking issues. Apply an additive migration fix, then rerun 'make migration-doctor'.")
    elif has_warn:
        print("Migration doctor found non-blocking drift or schema warnings. Review before merging or restarting the stack.")
    else:
        print("Migration doctor found no obvious Alembic or schema-drift issues.")

    if strict and has_fail:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose local Alembic revision and schema-drift issues.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when blocking migration issues are found")
    args = parser.parse_args()
    return run_doctor(strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())