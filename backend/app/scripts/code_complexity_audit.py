"""Compute a simple cyclomatic complexity estimate by Python file."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(__file__).resolve().parents[3] / "docs" / "development" / "CODE_COMPLEXITY_AUDIT.md"


COMPLEXITY_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.With,
    ast.AsyncWith,
    ast.BoolOp,
    ast.IfExp,
    ast.Match,
)


def file_complexity(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return 1 + sum(isinstance(node, COMPLEXITY_NODES) for node in ast.walk(tree))


def main() -> int:
    scores = []
    for py_file in ROOT.rglob("*.py"):
        try:
            score = file_complexity(py_file)
        except Exception:
            continue
        scores.append((score, py_file.relative_to(ROOT.parent)))

    scores.sort(reverse=True)
    lines = ["# Code Complexity Audit", "", "| File | Complexity |", "|---|---:|"]
    for score, path in scores[:200]:
        lines.append(f"| `{path}` | {score} |")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
