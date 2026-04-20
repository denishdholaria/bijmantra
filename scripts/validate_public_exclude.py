#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_PRIVATE_PATTERNS = [
    ".github/copilot-instructions.md",
    ".github/agents/",
    ".ai/",
    ".agent/",
    ".kiro/",
]

LEGACY_PRIVATE_DOCS_PATTERN = "docs-private/"


def main() -> int:
    repo_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    exclude_path = repo_root / ".public-exclude"

    if not exclude_path.is_file():
        print(f"Missing {exclude_path}", file=sys.stderr)
        return 1

    patterns = {
        line.strip()
        for line in exclude_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    missing = [pattern for pattern in REQUIRED_PRIVATE_PATTERNS if pattern not in patterns]
    if missing:
        print("Required private exclusions are missing from .public-exclude:", file=sys.stderr)
        for pattern in missing:
            print(f"  - {pattern}", file=sys.stderr)
        return 1

    legacy_docs_path = repo_root / "docs-private"
    if legacy_docs_path.exists() and LEGACY_PRIVATE_DOCS_PATTERN not in patterns:
        print(
            "Legacy docs-private directory exists but is not excluded from public sync:",
            file=sys.stderr,
        )
        print(f"  - {LEGACY_PRIVATE_DOCS_PATTERN}", file=sys.stderr)
        return 1

    print("Required private exclusions are present in .public-exclude.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())