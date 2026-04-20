#!/usr/bin/env python3
"""Fail if public docs contain accidental internal markers."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MARKERS = ["internal only", "TODO(internal)", "do not publish"]


def main() -> int:
    hits: list[str] = []
    for md_file in DOCS.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="ignore").lower()
        for marker in MARKERS:
            if marker in text:
                hits.append(f"{md_file.relative_to(ROOT)}: {marker}")

    if hits:
        print("Potential internal markers found:")
        print("\n".join(hits))
        return 1

    print("No internal markers found in docs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
