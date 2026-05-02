#!/usr/bin/env python3
"""Audit historical legacy references inside the .ai evidence trail."""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from private_docs_paths import display_path, resolve_confidential_docs_root


ROOT = Path(__file__).resolve().parents[1]
AI_ROOT = ROOT / ".ai"
HISTORICAL_DIRS = ["decisions", "proposals", "reviews", "tasks"]

PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "legacy-private-docs-path",
        re.compile(r"docs-private/[^\s`)]*"),
        "Historical reference to the retired in-repo private-docs path.",
    ),
    (
        "legacy-kiro-steering-reference",
        re.compile(r"\.kiro/steering/[^\s`)]*"),
        "Historical reference to the older Kiro steering authority surface.",
    ),
]


def default_output_path() -> Path:
    docs_root = resolve_confidential_docs_root()
    stamp = datetime.now(UTC).date().isoformat()
    return docs_root / "reference" / f"{stamp}-ai-control-surface-legacy-reference-audit.md"


def collect_matches() -> list[dict[str, str | int]]:
    matches: list[dict[str, str | int]] = []
    for folder in HISTORICAL_DIRS:
        for path in sorted((AI_ROOT / folder).rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                for category, pattern, description in PATTERNS:
                    for match in pattern.finditer(line):
                        matches.append(
                            {
                                "category": category,
                                "description": description,
                                "path": str(path.relative_to(ROOT)),
                                "line": line_number,
                                "value": match.group(0),
                                "directory": folder,
                            }
                        )
    return matches


def build_report(matches: list[dict[str, str | int]]) -> str:
    generated_at = datetime.now(UTC).isoformat()
    counts_by_category = Counter(str(item["category"]) for item in matches)
    counts_by_directory = Counter(str(item["directory"]) for item in matches)
    grouped: dict[str, list[dict[str, str | int]]] = defaultdict(list)
    for item in matches:
        grouped[str(item["category"])].append(item)

    lines = [
        "# AI Control-Surface Legacy Reference Audit",
        "",
        f"Generated at: {generated_at}",
        f"Repository root: {ROOT}",
        f"Audit scope: {', '.join(f'.ai/{folder}' for folder in HISTORICAL_DIRS)}",
        "",
        "## Purpose",
        "",
        "This report inventories legacy path and authority references that remain inside the historical `.ai` evidence trail.",
        "",
        "These references are not automatically treated as bugs because proposals, decisions, reviews, and task records preserve repo history. The goal is visibility, not blanket rewrite.",
        "",
        "## Summary",
        "",
        f"- Total matches: {len(matches)}",
        f"- Category counts: {', '.join(f'{key}={counts_by_category[key]}' for key in sorted(counts_by_category)) or 'none'}",
        f"- Directory counts: {', '.join(f'{key}={counts_by_directory[key]}' for key in sorted(counts_by_directory)) or 'none'}",
        "",
        "## Interpretation",
        "",
        "- Historical references in `.ai/tasks/`, `.ai/proposals/`, `.ai/reviews/`, and `.ai/decisions/` usually preserve the state of the repo at the time the artifact was written.",
        "- Do not mass-rewrite these records only to modernize paths.",
        "- Update a historical artifact only if it is being substantively revised or if a stale reference blocks comprehension during active work.",
        "- Active control surfaces are validated separately by `make control-surfaces-check`.",
        "",
    ]

    for category in sorted(grouped):
        samples = grouped[category]
        lines.extend(
            [
                f"## {category}",
                "",
                f"{samples[0]['description']}",
                "",
            ]
        )
        for item in samples:
            lines.append(
                f"- {item['path']}:{item['line']} -> `{item['value']}`"
            )
        lines.append("")

    lines.extend(
        [
            "## Current Active Authorities",
            "",
            "- `AGENTS.md`",
            "- `.github/copilot-instructions.md`",
            "- `.ai/README.md`",
            "- `.ai/AGENT_COORDINATION_PROTOCOL.md`",
            "- `.agent/jobs/README.md`",
            "- `.agent/jobs/overnight-queue.json`",
            "- `.github/agents/`",
            f"- `{display_path(resolve_confidential_docs_root(), ROOT)}` when private documentation context is required",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the markdown report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    matches = collect_matches()
    report = build_report(matches)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())