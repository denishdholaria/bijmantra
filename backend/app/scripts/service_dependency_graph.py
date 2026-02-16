"""Generate a service dependency graph from import relationships."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parents[3] / "docs" / "development" / "SERVICE_DEPENDENCY_GRAPH.md"


def module_name(path: Path) -> str:
    return ".".join(path.with_suffix("").relative_to(ROOT).parts)


def main() -> int:
    edges: set[tuple[str, str]] = set()
    for py_file in ROOT.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        source = module_name(py_file)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name.startswith("app."):
                        edges.add((source, name.name))
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
                edges.add((source, node.module))

    lines = ["# Service Dependency Graph", "", "```mermaid", "graph LR"]
    for left, right in sorted(edges):
        lines.append(f"  {left.replace('.', '_')}[{left}] --> {right.replace('.', '_')}[{right}]")
    lines.extend(["```", ""])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
