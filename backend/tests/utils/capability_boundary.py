"""Reusable assertions for capability-pack import boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


def python_files(root: Path) -> list[Path]:
    """Return Python files under a root, excluding generated caches."""

    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def imported_modules(path: Path) -> set[str]:
    """Return imported module names from a Python source file."""

    tree = ast.parse(path.read_text(), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def assert_no_forbidden_imports(
    paths: list[Path],
    forbidden_prefixes: tuple[str, ...],
    *,
    repo_root: Path,
    boundary_name: str,
) -> None:
    """Assert that files do not import modules behind forbidden prefixes."""

    for path in paths:
        for imported_module in imported_modules(path):
            assert not imported_module.startswith(forbidden_prefixes), (
                f"{path.relative_to(repo_root)} imports {imported_module!r}, "
                f"which violates the {boundary_name} boundary"
            )
