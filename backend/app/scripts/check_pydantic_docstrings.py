"""Custom lint check: every Pydantic model must have a class docstring."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _inherits_base_model(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "BaseModel":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
            return True
    return False


def main() -> int:
    violations: list[str] = []
    for py_file in ROOT.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in tree.body:
            if (
                isinstance(node, ast.ClassDef)
                and _inherits_base_model(node)
                and ast.get_docstring(node) is None
            ):
                violations.append(f"{py_file.relative_to(ROOT)}:{node.lineno} {node.name}")

    if violations:
        print("Pydantic docstring violations:")
        print("\n".join(violations))
        return 1

    print("All Pydantic models include docstrings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
