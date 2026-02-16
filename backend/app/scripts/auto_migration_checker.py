"""Warn when model/schema changes are detected without a migration update."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def changed_files() -> list[str]:
    cmd = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    files = changed_files()
    model_changes = [f for f in files if f.startswith("backend/app/models/") or f.startswith("backend/app/schemas/")]
    migration_changes = [f for f in files if f.startswith("backend/alembic/versions/")]

    if model_changes and not migration_changes:
        print("Potential migration required: model/schema changed but no migration file updated.")
        for item in model_changes:
            print(f" - {item}")
        return 1

    print("Migration check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
