# BIJMANTRA JULES JOB CARD: D01
"""
REEVU Domain Accuracy Matrix Evaluator.

This script evaluates the domain classification accuracy of the REEVU Planner
using a fixture of cross-domain prompts. It calculates a co-occurrence confusion
matrix and per-domain Precision, Recall, and F1 scores.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure `app` imports resolve when run as a standalone script.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.reevu.planner import ReevuPlanner

DOMAINS = ["analytics", "breeding", "genomics", "trials", "weather"]


@dataclass
class EvalDomainResult:
    case_id: str
    query: str
    expected_domains: list[str]
    predicted_domains: list[str]
    is_compound: bool


def _load_fixture(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _evaluate_cases(cases: list[dict[str, Any]]) -> list[EvalDomainResult]:
    planner = ReevuPlanner()
    results: list[EvalDomainResult] = []

    for case in cases:
        # Check if this case is relevant (has expected_domains)
        if "expected_domains" not in case:
            continue

        plan = planner.build_plan(case["query"])

        results.append(
            EvalDomainResult(
                case_id=case.get("prompt_id", "unknown"),
                query=case["query"],
                expected_domains=case["expected_domains"],
                predicted_domains=plan.domains_involved,
                is_compound=case.get("is_compound", False),
            )
        )

    return results


def _compute_metrics(results: list[EvalDomainResult]) -> dict[str, Any]:
    # Co-occurrence Confusion Matrix: Rows=Expected, Cols=Predicted
    # matrix[expected][predicted] = count
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    # Initialize matrix with 0s for all pairs
    for d1 in DOMAINS:
        for d2 in DOMAINS:
            matrix[d1][d2] = 0

    # Per-domain TP, FP, FN
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)

    # Track unknown domains
    unknown_domains = set()

    for res in results:
        expected = set(res.expected_domains)
        predicted = set(res.predicted_domains)

        # Check for unknown predicted domains
        for p in predicted:
            if p not in DOMAINS:
                unknown_domains.add(p)

        # Update Matrix
        # For every expected domain, log what was predicted.
        # This shows "When X was expected, Y was predicted".
        # If multiple expected or predicted, we log all pairs.
        if not expected:
             # Case: No domains expected.
             for p in predicted:
                 matrix["(none)"][p] += 1
        else:
            for e in expected:
                if not predicted:
                    matrix[e]["(none)"] += 1
                else:
                    for p in predicted:
                        matrix[e][p] += 1

        # Update TP, FP, FN
        for d in DOMAINS:
            if d in expected and d in predicted:
                tp[d] += 1
            elif d not in expected and d in predicted:
                fp[d] += 1
            elif d in expected and d not in predicted:
                fn[d] += 1

    # Calculate Precision, Recall, F1
    domain_scores = {}
    for d in DOMAINS:
        t = tp[d]
        f_p = fp[d]
        f_n = fn[d]

        precision = t / (t + f_p) if (t + f_p) > 0 else 0.0
        recall = t / (t + f_n) if (t + f_n) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        domain_scores[d] = {
            "tp": t,
            "fp": f_p,
            "fn": f_n,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4)
        }

    return {
        "matrix": dict(matrix),
        "domain_scores": domain_scores,
        "total_cases": len(results),
        "unknown_domains": sorted(list(unknown_domains)),
    }


def _print_human_summary(summary: dict[str, Any]) -> None:
    print("\nREEVU Domain Accuracy Matrix Evaluation")
    print("=======================================\n")
    print(f"Total Cases: {summary['total_cases']}")
    if summary.get("unknown_domains"):
        print(f"Unknown Domains Detected: {', '.join(summary['unknown_domains'])}")
    print("\n")

    print("Per-Domain Performance Scores:")
    print("-" * 65)
    print(f"{'Domain':<15} {'Prec':>8} {'Recall':>8} {'F1':>8} {'TP':>4} {'FP':>4} {'FN':>4}")
    print("-" * 65)

    scores = summary["domain_scores"]
    for d in DOMAINS:
        s = scores.get(d, {"precision": 0, "recall": 0, "f1": 0, "tp": 0, "fp": 0, "fn": 0})
        print(f"{d:<15} {s['precision']:>8.4f} {s['recall']:>8.4f} {s['f1']:>8.4f} {s['tp']:>4} {s['fp']:>4} {s['fn']:>4}")
    print("-" * 65)
    print("\n")

    print("Co-occurrence Confusion Matrix (Rows=Expected, Cols=Predicted):")
    # Header
    headers = [d[:4] for d in DOMAINS] # Shorten for display
    print(" " * 12 + " ".join([f"{h:>5}" for h in headers]))

    matrix = summary["matrix"]
    for row_d in DOMAINS:
        row_str = f"{row_d:<10} |"
        for col_d in DOMAINS:
            val = matrix.get(row_d, {}).get(col_d, 0)
            row_str += f"{val:>5} "
        print(row_str)
    print("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate domain accuracy for REEVU.")
    parser.add_argument(
        "--fixture",
        default="tests/fixtures/reevu/cross_domain_prompts.json",
        help="Path to fixture JSON file (relative to backend root)",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional path to write JSON summary",
    )
    args = parser.parse_args()

    # Locate fixture relative to project root if not absolute
    fixture_path = Path(args.fixture)
    if not fixture_path.is_absolute():
        fixture_path = PROJECT_ROOT / fixture_path

    if not fixture_path.exists():
        print(f"Error: Fixture not found at {fixture_path}")
        return 1

    cases = _load_fixture(fixture_path)
    results = _evaluate_cases(cases)
    summary = _compute_metrics(results)

    _print_human_summary(summary)

    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"- wrote json summary: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
