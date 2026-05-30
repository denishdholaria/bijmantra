#!/usr/bin/env python3
"""Report service migration pressure without reviving the old module target.

Flat ``backend/app/services`` and ``backend/app/modules`` are transitional
runtime surfaces. The canonical target for new domain behavior is
``backend/app/domains/<domain>`` using wrap/extract/drain migration.
"""

from __future__ import annotations

from pathlib import Path


CANONICAL_TARGET = "backend/app/domains/<domain>"
TRANSITIONAL_SURFACES = ("backend/app/services", "backend/app/modules")


def _count_python_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(
        1
        for source_path in path.rglob("*.py")
        if source_path.name != "__init__.py" and "__pycache__" not in source_path.parts
    )


def main() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    repo_root = backend_dir.parent

    print("Checking transitional service surfaces...")
    for relative_surface in TRANSITIONAL_SURFACES:
        surface = repo_root / relative_surface
        print(f"  {relative_surface}: {_count_python_files(surface)} Python files")

    print()
    print(f"Canonical target for new domain behavior: {CANONICAL_TARGET}")
    print("Migration policy: wrap existing behavior, extract one vertical path, then drain legacy code.")
    print("Status: advisory baseline passed.")


if __name__ == "__main__":
    main()
