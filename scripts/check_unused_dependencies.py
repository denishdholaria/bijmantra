#!/usr/bin/env python3
"""Lightweight unused dependency report for backend/frontend manifests."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def check_requirements() -> list[str]:
    req_file = ROOT / "backend" / "requirements.txt"
    py_files = list((ROOT / "backend" / "app").rglob("*.py"))
    all_content = "\n".join(_read(p) for p in py_files)
    maybe_unused = []
    for line in _read(req_file).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = re.split(r"[<>=\[]", line, 1)[0].replace("-", "_")
        if pkg and pkg not in all_content:
            maybe_unused.append(line)
    return maybe_unused


def check_package_json() -> list[str]:
    package = json.loads(_read(ROOT / "frontend" / "package.json"))
    deps = package.get("dependencies", {})
    ts_files = list((ROOT / "frontend" / "src").rglob("*.ts")) + list((ROOT / "frontend" / "src").rglob("*.tsx"))
    content = "\n".join(_read(p) for p in ts_files)
    maybe_unused = []
    for dep in deps:
        token = dep.split("/")[-1]
        if token not in content:
            maybe_unused.append(dep)
    return maybe_unused


def main() -> int:
    py_unused = check_requirements()
    js_unused = check_package_json()

    print("Potentially unused Python dependencies:")
    for item in py_unused:
        print(f" - {item}")

    print("\nPotentially unused frontend dependencies:")
    for item in js_unused:
        print(f" - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
