"""Validate REEVU report artifacts for integrity and reproducibility.

Checks performed:
1. Required artifacts exist.
2. Required keys exist in each JSON artifact.
3. KPI rates are numeric and in [0, 1].
4. Timestamp/order sanity: ops report `generated_at` should be newest artifact from a run.

Exit code:
- 0: all integrity checks pass.
- 1: one or more integrity violations found.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArtifactSpec:
    required_keys: tuple[str, ...]
    bounded_rate_keys: tuple[str, ...]


ARTIFACT_SPECS: dict[str, ArtifactSpec] = {
    "reevu_trace_completeness_baseline.json": ArtifactSpec(
        required_keys=("total_cases", "complete_cases", "trace_completeness_rate", "meets_floor"),
        bounded_rate_keys=("trace_completeness_rate", "kpi_floor"),
    ),
    "reevu_top_intent_routing_baseline.json": ArtifactSpec(
        required_keys=(
            "total_cases",
            "function_exact_match_rate",
            "actionable_function_precision",
            "param_subset_match_rate_when_function_matches",
        ),
        bounded_rate_keys=(
            "function_exact_match_rate",
            "actionable_function_precision",
            "param_subset_match_rate_when_function_matches",
        ),
    ),
    "reevu_stage_a_kpi_report.json": ArtifactSpec(
        required_keys=("stage", "kpi_targets", "kpi_values", "status", "sources"),
        bounded_rate_keys=(
            "kpi_values.tool_call_precision",
            "kpi_values.trace_completeness",
            "kpi_targets.tool_call_precision_floor",
            "kpi_targets.trace_completeness_floor",
        ),
    ),
    "reevu_cross_domain_reasoning_baseline.json": ArtifactSpec(
        required_keys=(
            "total_prompts",
            "domain_detection_accuracy",
            "compound_classification_accuracy",
            "step_adequacy_rate",
        ),
        bounded_rate_keys=(
            "domain_detection_accuracy",
            "compound_classification_accuracy",
            "step_adequacy_rate",
        ),
    ),
    "reevu_ops_report.json": ArtifactSpec(
        required_keys=("generated_at", "stages_evaluated", "kpi_checks", "overall_floor_met", "sources"),
        bounded_rate_keys=(
            "kpi_checks.trace_completeness.value",
            "kpi_checks.trace_completeness.floor",
            "kpi_checks.tool_call_precision.value",
            "kpi_checks.tool_call_precision.floor",
            "kpi_checks.domain_detection_accuracy.value",
            "kpi_checks.domain_detection_accuracy.floor",
            "kpi_checks.compound_classification.value",
            "kpi_checks.compound_classification.floor",
            "kpi_checks.step_adequacy.value",
            "kpi_checks.step_adequacy.floor",
        ),
    ),
}


def _nested_get(payload: dict[str, Any], key_path: str) -> Any:
    current: Any = payload
    for part in key_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(key_path)
        current = current[part]
    return current


def _is_rate_in_range(value: Any) -> bool:
    if not isinstance(value, (int, float)):
        return False
    return 0.0 <= float(value) <= 1.0


def _parse_iso_ts(raw: str) -> datetime:
    # Support the common `Z` suffix and explicit offsets.
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def validate_artifacts(reports_dir: Path) -> tuple[bool, list[str], list[str]]:
    violations: list[str] = []
    info: list[str] = []
    mtimes: dict[str, float] = {}

    for filename, spec in ARTIFACT_SPECS.items():
        path = reports_dir / filename

        if not path.exists():
            violations.append(f"missing required artifact: {filename}")
            continue

        mtimes[filename] = path.stat().st_mtime

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            violations.append(f"invalid JSON in {filename}: {exc}")
            continue

        for key in spec.required_keys:
            try:
                _nested_get(payload, key)
            except KeyError:
                violations.append(f"{filename}: missing required key `{key}`")

        for rate_key in spec.bounded_rate_keys:
            try:
                value = _nested_get(payload, rate_key)
            except KeyError:
                violations.append(f"{filename}: missing KPI key `{rate_key}`")
                continue
            if not _is_rate_in_range(value):
                violations.append(
                    f"{filename}: `{rate_key}` must be numeric in [0,1], got {value!r}"
                )

    ops_name = "reevu_ops_report.json"
    if ops_name in mtimes:
        ops_path = reports_dir / ops_name
        try:
            ops_payload = json.loads(ops_path.read_text(encoding="utf-8"))
            generated_at = _parse_iso_ts(ops_payload["generated_at"]).timestamp()
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            violations.append(f"{ops_name}: invalid generated_at timestamp: {exc}")
        else:
            newest_file = max(mtimes, key=mtimes.get)
            if newest_file != ops_name:
                violations.append(
                    f"artifact ordering mismatch: newest file is {newest_file}, expected {ops_name}"
                )
            info.append(f"newest artifact: {newest_file}")

    return (len(violations) == 0), violations, info


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate REEVU report artifacts integrity.")
    parser.add_argument(
        "--reports-dir",
        default="test_reports",
        help="Directory containing REEVU report artifacts",
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    ok, violations, info = validate_artifacts(reports_dir)

    print("REEVU Artifact Integrity Summary")
    print(f"  reports_dir: {reports_dir}")
    print(f"  artifacts_expected: {len(ARTIFACT_SPECS)}")
    print(f"  integrity_status: {'PASS' if ok else 'FAIL'}")
    for message in sorted(info):
        print(f"  info: {message}")

    if violations:
        print("  violations:")
        for violation in sorted(violations):
            print(f"    - {violation}")
        return 1

    print("  violations: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
