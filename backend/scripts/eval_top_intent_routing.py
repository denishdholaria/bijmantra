"""Deterministic top-intent routing evaluator for REEVU FunctionCallingService.

This script runs a fixture of user prompts through pattern-based function routing
(no external API key required) and reports routing/parameter precision metrics.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure `app` imports resolve when run as a standalone script.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.modules.ai.services.function_calling_service import FunctionCallingService


@dataclass
class EvalCaseResult:
    case_id: str
    message: str
    expected_function: str | None
    predicted_function: str | None
    function_match: bool
    expected_params: dict[str, Any]
    predicted_params: dict[str, Any]
    params_match: bool


def _load_fixture(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _params_subset_match(expected: dict[str, Any], predicted: dict[str, Any]) -> bool:
    for key, expected_value in expected.items():
        if predicted.get(key) != expected_value:
            return False
    return True


async def _evaluate_cases(cases: list[dict[str, Any]]) -> list[EvalCaseResult]:
    service = FunctionCallingService(api_key=None)
    results: list[EvalCaseResult] = []

    for case in cases:
        detected = await service.detect_function_call(case["message"])
        predicted_function = detected.name if detected else None
        predicted_params = detected.parameters if detected else {}

        expected_function = case.get("expected_function")
        expected_params = case.get("expected_params", {})

        function_match = predicted_function == expected_function
        params_match = _params_subset_match(expected_params, predicted_params)

        results.append(
            EvalCaseResult(
                case_id=case["id"],
                message=case["message"],
                expected_function=expected_function,
                predicted_function=predicted_function,
                function_match=function_match,
                expected_params=expected_params,
                predicted_params=predicted_params,
                params_match=params_match,
            )
        )

    return results


def _build_summary(results: list[EvalCaseResult]) -> dict[str, Any]:
    total = len(results)
    function_matches = sum(1 for r in results if r.function_match)
    param_matches_on_function_match = sum(
        1 for r in results if r.function_match and r.params_match
    )

    expected_actionable = [r for r in results if r.expected_function is not None]
    predicted_actionable = [r for r in results if r.predicted_function is not None]
    actionable_function_matches = sum(
        1 for r in expected_actionable if r.function_match
    )

    failures = [
        {
            "id": r.case_id,
            "message": r.message,
            "expected_function": r.expected_function,
            "predicted_function": r.predicted_function,
            "expected_params": r.expected_params,
            "predicted_params": r.predicted_params,
            "function_match": r.function_match,
            "params_match": r.params_match,
        }
        for r in results
        if not r.function_match or not r.params_match
    ]

    return {
        "total_cases": total,
        "expected_actionable_cases": len(expected_actionable),
        "predicted_actionable_cases": len(predicted_actionable),
        "function_exact_match_count": function_matches,
        "function_exact_match_rate": round(function_matches / total, 4) if total else 0.0,
        "actionable_function_match_count": actionable_function_matches,
        "actionable_function_precision": (
            round(actionable_function_matches / len(expected_actionable), 4)
            if expected_actionable
            else 0.0
        ),
        "param_subset_match_count_when_function_matches": param_matches_on_function_match,
        "param_subset_match_rate_when_function_matches": (
            round(param_matches_on_function_match / function_matches, 4)
            if function_matches
            else 0.0
        ),
        "failures": failures,
    }


def _print_human_summary(summary: dict[str, Any]) -> None:
    print("REEVU Top-Intent Routing Eval")
    print(f"- total cases: {summary['total_cases']}")
    print(f"- function exact match: {summary['function_exact_match_count']} ({summary['function_exact_match_rate']:.2%})")
    print(
        "- actionable function precision: "
        f"{summary['actionable_function_match_count']}/{summary['expected_actionable_cases']} "
        f"({summary['actionable_function_precision']:.2%})"
    )
    print(
        "- parameter subset match (when function matches): "
        f"{summary['param_subset_match_count_when_function_matches']}/"
        f"{summary['function_exact_match_count']} "
        f"({summary['param_subset_match_rate_when_function_matches']:.2%})"
    )

    if summary["failures"]:
        print("- failing cases:")
        for failure in summary["failures"]:
            print(
                f"  - {failure['id']}: expected={failure['expected_function']} "
                f"predicted={failure['predicted_function']}"
            )


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate top-intent routing for REEVU.")
    parser.add_argument(
        "--fixture",
        default="tests/fixtures/reevu/top_intent_routing.json",
        help="Path to fixture JSON file",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional path to write JSON summary",
    )
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    cases = _load_fixture(fixture_path)
    results = await _evaluate_cases(cases)
    summary = _build_summary(results)

    _print_human_summary(summary)

    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"- wrote json summary: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
