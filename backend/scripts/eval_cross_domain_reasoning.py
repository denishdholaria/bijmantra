"""Evaluate REEVU Stage C cross-domain reasoning quality.

Scores the multi-domain planner against the fixture set of compound prompts:
  • domain detection accuracy — do we find the expected domains?
  • compound classification — is_compound correctly identified?
  • step count adequacy — at least expected_min_steps produced?

Usage:
    cd backend && uv run python scripts/eval_cross_domain_reasoning.py \
        --json-output test_reports/reevu_cross_domain_reasoning_baseline.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# ── allow running from repo root or backend/ ─────────────────────────
import sys
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.modules.ai.services.reevu import ReevuPlanner  # noqa: E402


def _load_fixtures(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    planner = ReevuPlanner()

    total = len(fixtures)
    domain_correct = 0
    compound_correct = 0
    step_adequate = 0
    
    # Strict metrics
    exact_domain_match_count = 0
    sum_precision = 0.0
    sum_recall = 0.0
    sum_f1 = 0.0
    
    details: list[dict[str, Any]] = []

    for fx in fixtures:
        plan = planner.build_plan(fx["query"])

        expected_domains = set(fx["expected_domains"])
        detected_domains = set(plan.domains_involved)
        
        # Original logic (backward compatible subset rule)
        # Note: if expected is empty, issubset is trivially True regardless of detected_domains.
        # We now fix empty expected domain handling for the pure subset rule too:
        if not expected_domains and detected_domains:
            domain_match = False
        else:
            domain_match = expected_domains.issubset(detected_domains)
            
        if domain_match:
            domain_correct += 1

        # Strict metric logic (Precision, Recall, F1)
        if not expected_domains and not detected_domains:
            precision, recall, f1 = 1.0, 1.0, 1.0
        elif not expected_domains and detected_domains:
            precision, recall, f1 = 0.0, 0.0, 0.0
        elif expected_domains and not detected_domains:
            precision, recall, f1 = 0.0, 0.0, 0.0
        else:
            intersection = expected_domains.intersection(detected_domains)
            precision = len(intersection) / len(detected_domains)
            recall = len(intersection) / len(expected_domains)
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        if expected_domains == detected_domains:
            exact_domain_match_count += 1
            
        sum_precision += precision
        sum_recall += recall
        sum_f1 += f1
        
        # Compound classification.
        compound_match = plan.is_compound == fx["is_compound"]
        if compound_match:
            compound_correct += 1

        # Step count.
        step_ok = plan.total_steps >= fx["expected_min_steps"]
        if step_ok:
            step_adequate += 1

        details.append({
            "prompt_id": fx["prompt_id"],
            "domain_match": domain_match,
            "expected_domains": sorted(expected_domains),
            "detected_domains": sorted(detected_domains),
            "compound_match": compound_match,
            "step_ok": step_ok,
            "step_count": plan.total_steps,
            "expected_min_steps": fx["expected_min_steps"],
            "strict_metrics": {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
            }
        })

    return {
        "total_prompts": total,
        
        # Original backward-compatible fields
        "domain_detection_accuracy": round(domain_correct / total, 4) if total else 0.0,
        "compound_classification_accuracy": round(compound_correct / total, 4) if total else 0.0,
        "step_adequacy_rate": round(step_adequate / total, 4) if total else 0.0,
        "domain_correct": domain_correct,
        "compound_correct": compound_correct,
        "step_adequate": step_adequate,
        
        # New strict fields
        "exact_domain_match_rate": round(exact_domain_match_count / total, 4) if total else 0.0,
        "domain_precision": round(sum_precision / total, 4) if total else 0.0,
        "domain_recall": round(sum_recall / total, 4) if total else 0.0,
        "domain_f1": round(sum_f1 / total, 4) if total else 0.0,
        
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate REEVU Stage C cross-domain reasoning quality."
    )
    parser.add_argument(
        "--fixtures",
        default="tests/fixtures/reevu/cross_domain_prompts.json",
        help="Path to cross-domain prompt fixture file",
    )
    parser.add_argument(
        "--json-output",
        default="test_reports/reevu_cross_domain_reasoning_baseline.json",
        help="Path to write evaluation results JSON",
    )
    args = parser.parse_args()

    fixtures = _load_fixtures(Path(args.fixtures))
    results = evaluate(fixtures)

    output_path = Path(args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("REEVU Stage C Cross-Domain Reasoning Evaluation")
    print(f"  prompts evaluated: {results['total_prompts']}")
    print(f"  domain detection accuracy (subset): {results['domain_detection_accuracy']:.2%}")
    print(f"  compound classification: {results['compound_classification_accuracy']:.2%}")
    print(f"  step adequacy: {results['step_adequacy_rate']:.2%}")
    print("  -- Strict Metrics --")
    print(f"  exact match rate: {results['exact_domain_match_rate']:.2%}")
    print(f"  precision: {results['domain_precision']:.2%}")
    print(f"  recall: {results['domain_recall']:.2%}")
    print(f"  F1 score: {results['domain_f1']:.2%}")
    print(f"  wrote: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
