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


BASE_ARTIFACT_SPECS: dict[str, ArtifactSpec] = {
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

RUNTIME_ARTIFACT_SPECS: dict[str, tuple[tuple[str, ArtifactSpec], ...]] = {
    "local": (
        (
            "reevu_real_question_local.json",
            ArtifactSpec(
                required_keys=(
                    "generated_at",
                    "fixture_path",
                    "runtime_path",
                    "runtime_target",
                    "runtime_status",
                    "local_organization_id",
                    "local_organization_selection.mode",
                    "local_organization_selection.requested_organization_id",
                    "local_organization_selection.effective_organization_id",
                    "readiness_blockers",
                    "readiness_warnings",
                    "runtime_readiness",
                    "total_cases",
                    "passed_cases",
                    "pass_rate",
                    "failed_cases",
                    "question_family_summary",
                    "results",
                ),
                bounded_rate_keys=("pass_rate",),
            ),
        ),
        (
            "reevu_local_readiness_census.json",
            ArtifactSpec(
                required_keys=(
                    "generated_at",
                    "runtime_path",
                    "local_organization_selection.mode",
                    "local_organization_selection.requested_organization_id",
                    "local_organization_selection.effective_organization_id",
                    "selected_local_organization_id",
                    "organizations_scanned",
                    "benchmark_ready_organization_ids",
                    "benchmark_ready_demo_organization_ids",
                    "benchmark_ready_non_demo_organization_ids",
                    "blocked_organization_ids",
                    "policy_guidance",
                    "selected_local_organization_remediation",
                    "organizations",
                ),
                bounded_rate_keys=(),
            ),
        ),
        (
            "reevu_authority_gap_report.json",
            ArtifactSpec(
                required_keys=(
                    "generated_at",
                    "runtime_path",
                    "overall_gap_status",
                    "selected_local_organization_id",
                    "local_organization_selection.mode",
                    "local_organization_selection.requested_organization_id",
                    "local_organization_selection.effective_organization_id",
                    "organizations_scanned",
                    "benchmark_ready_organization_ids",
                    "benchmark_ready_demo_organization_ids",
                    "benchmark_ready_non_demo_organization_ids",
                    "blocked_organization_ids",
                    "common_blockers_across_blocked_orgs",
                    "policy_guidance",
                    "surface_gaps",
                ),
                bounded_rate_keys=(),
            ),
        ),
    ),
    "managed": (
        (
            "reevu_real_question_managed.json",
            ArtifactSpec(
                required_keys=(
                    "generated_at",
                    "fixture_path",
                    "runtime_path",
                    "runtime_target",
                    "runtime_status",
                    "total_cases",
                    "passed_cases",
                    "pass_rate",
                    "failed_cases",
                    "question_family_summary",
                    "results",
                ),
                bounded_rate_keys=("pass_rate",),
            ),
        ),
    ),
}


def build_artifact_specs(
    required_runtime_paths: tuple[str, ...] | list[str] = ("local", "managed"),
) -> dict[str, ArtifactSpec]:
    specs = dict(BASE_ARTIFACT_SPECS)
    for runtime_path in required_runtime_paths:
        for filename, spec in RUNTIME_ARTIFACT_SPECS[runtime_path]:
            specs[filename] = spec
    return specs


def _validate_local_organization_selection(
    *,
    payload: dict[str, Any],
    filename: str,
    violations: list[str],
) -> None:
    selection = payload.get("local_organization_selection")
    if not isinstance(selection, dict):
        violations.append(f"{filename}: `local_organization_selection` must be an object")
        return

    mode = selection.get("mode")
    if mode not in {"default", "env", "cli"}:
        violations.append(
            f"{filename}: `local_organization_selection.mode` must be one of default/env/cli, got {mode!r}"
        )

    for key in ("requested_organization_id", "effective_organization_id"):
        value = selection.get(key)
        if not isinstance(value, int) or value <= 0:
            violations.append(
                f"{filename}: `local_organization_selection.{key}` must be a positive integer, got {value!r}"
            )


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


def _validate_ops_report_runtime_readiness(
    *,
    payload: dict[str, Any],
    filename: str,
    violations: list[str],
) -> None:
    runtime_readiness = payload.get("runtime_readiness")
    if runtime_readiness is None:
        return
    if not isinstance(runtime_readiness, dict):
        violations.append(f"{filename}: `runtime_readiness` must be an object when present")
        return

    for runtime_path in ("local", "managed"):
        runtime_payload = runtime_readiness.get(runtime_path)
        if not isinstance(runtime_payload, dict):
            violations.append(
                f"{filename}: `runtime_readiness.{runtime_path}` must be an object"
            )
            continue

        artifact_present = runtime_payload.get("artifact_present")
        if not isinstance(artifact_present, bool):
            violations.append(
                f"{filename}: `runtime_readiness.{runtime_path}.artifact_present` must be a boolean"
            )

        pass_rate = runtime_payload.get("pass_rate")
        if pass_rate is not None and not _is_rate_in_range(pass_rate):
            violations.append(
                f"{filename}: `runtime_readiness.{runtime_path}.pass_rate` must be numeric in [0,1] or null, got {pass_rate!r}"
            )

        for list_key in (
            "readiness_blockers",
            "readiness_warnings",
            "benchmark_ready_organization_ids",
            "benchmark_ready_demo_organization_ids",
            "benchmark_ready_non_demo_organization_ids",
            "policy_guidance",
            "selected_local_organization_remediation",
            "common_blockers_across_blocked_orgs",
        ):
            if list_key not in runtime_payload:
                continue
            list_value = runtime_payload.get(list_key)
            if not isinstance(list_value, list):
                violations.append(
                    f"{filename}: `runtime_readiness.{runtime_path}.{list_key}` must be a list"
                )
                continue
            if list_key.endswith("organization_ids"):
                for organization_id in list_value:
                    if not isinstance(organization_id, int) or organization_id <= 0:
                        violations.append(
                            f"{filename}: `runtime_readiness.{runtime_path}.{list_key}` entries must be positive integers, got {organization_id!r}"
                        )
            else:
                for index, item in enumerate(list_value):
                    if not isinstance(item, str) or not item.strip():
                        violations.append(
                            f"{filename}: `runtime_readiness.{runtime_path}.{list_key}[{index}]` must be a non-empty string"
                        )

        least_blocked_local_organization = runtime_payload.get(
            "least_blocked_local_organization"
        )
        if least_blocked_local_organization is not None and not isinstance(
            least_blocked_local_organization, dict
        ):
            violations.append(
                f"{filename}: `runtime_readiness.{runtime_path}.least_blocked_local_organization` must be an object or null"
            )


def _ready_organization_ids(payload: dict[str, Any] | None) -> set[int]:
    if not isinstance(payload, dict):
        return set()

    organizations = payload.get("organizations")
    if not isinstance(organizations, list):
        return set()

    ready_ids: set[int] = set()
    for organization in organizations:
        if not isinstance(organization, dict):
            continue
        if organization.get("runtime_status") != "ready":
            continue
        organization_id = organization.get("organization_id")
        if isinstance(organization_id, int) and organization_id > 0:
            ready_ids.add(organization_id)

    return ready_ids


def _positive_organization_ids(value: Any) -> set[int]:
    if not isinstance(value, list):
        return set()

    return {
        organization_id
        for organization_id in value
        if isinstance(organization_id, int) and organization_id > 0
    }


def validate_artifacts(
    reports_dir: Path,
    required_runtime_paths: tuple[str, ...] | list[str] = ("local", "managed"),
) -> tuple[bool, list[str], list[str]]:
    violations: list[str] = []
    info: list[str] = []
    mtimes: dict[str, float] = {}
    payloads: dict[str, dict[str, Any]] = {}
    artifact_specs = build_artifact_specs(required_runtime_paths)

    for filename, spec in artifact_specs.items():
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

        if not isinstance(payload, dict):
            violations.append(f"{filename}: top-level JSON payload must be an object")
            continue

        payloads[filename] = payload

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

        if filename == "reevu_real_question_local.json":
            runtime_status = payload.get("runtime_status")
            if runtime_status not in {"ready", "blocked"}:
                violations.append(
                    f"{filename}: `runtime_status` must be `ready` or `blocked`, got {runtime_status!r}"
                )

            _validate_local_organization_selection(
                payload=payload,
                filename=filename,
                violations=violations,
            )

            local_organization_id = payload.get("local_organization_id")
            if not isinstance(local_organization_id, int) or local_organization_id <= 0:
                violations.append(
                    f"{filename}: `local_organization_id` must be a positive integer, got {local_organization_id!r}"
                )

            for list_key in ("readiness_blockers", "readiness_warnings"):
                if not isinstance(payload.get(list_key), list):
                    violations.append(f"{filename}: `{list_key}` must be a list")

            if not isinstance(payload.get("runtime_readiness"), dict):
                violations.append(f"{filename}: `runtime_readiness` must be an object")

            results = payload.get("results")
            if not isinstance(results, list):
                violations.append(f"{filename}: `results` must be a list")
            else:
                for index, result in enumerate(results):
                    if not isinstance(result, dict):
                        violations.append(f"{filename}: `results[{index}]` must be an object")
                        continue

                    for required_key in ("safe_failure_source", "safe_failure_payload"):
                        if required_key not in result:
                            violations.append(
                                f"{filename}: `results[{index}].{required_key}` is required"
                            )

                    safe_failure_source = result.get("safe_failure_source")
                    if safe_failure_source is not None and not isinstance(safe_failure_source, str):
                        violations.append(
                            f"{filename}: `results[{index}].safe_failure_source` must be a string or null"
                        )

                    safe_failure_payload = result.get("safe_failure_payload")
                    if safe_failure_payload is not None and not isinstance(safe_failure_payload, dict):
                        violations.append(
                            f"{filename}: `results[{index}].safe_failure_payload` must be an object or null"
                        )

                    failure_attribution = result.get("failure_attribution")
                    if failure_attribution is not None:
                        if not isinstance(failure_attribution, dict):
                            violations.append(
                                f"{filename}: `results[{index}].failure_attribution` must be an object or null"
                            )
                        else:
                            status = failure_attribution.get("status")
                            if status is not None and not isinstance(status, str):
                                violations.append(
                                    f"{filename}: `results[{index}].failure_attribution.status` must be a string or null"
                                )

                            reason = failure_attribution.get("reason")
                            if reason is not None and not isinstance(reason, str):
                                violations.append(
                                    f"{filename}: `results[{index}].failure_attribution.reason` must be a string or null"
                                )

                            for list_key in (
                                "relevant_blockers",
                                "relevant_warnings",
                                "unmapped_expected_domains",
                            ):
                                if list_key in failure_attribution and not isinstance(
                                    failure_attribution.get(list_key), list
                                ):
                                    violations.append(
                                        f"{filename}: `results[{index}].failure_attribution.{list_key}` must be a list when present"
                                    )

        if filename == "reevu_ops_report.json":
            _validate_ops_report_runtime_readiness(
                payload=payload,
                filename=filename,
                violations=violations,
            )

        if filename == "reevu_local_readiness_census.json":
            if payload.get("runtime_path") != "local":
                violations.append(
                    f"{filename}: `runtime_path` must be `local`, got {payload.get('runtime_path')!r}"
                )

            _validate_local_organization_selection(
                payload=payload,
                filename=filename,
                violations=violations,
            )

            selected_local_organization_id = payload.get("selected_local_organization_id")
            if not isinstance(selected_local_organization_id, int) or selected_local_organization_id <= 0:
                violations.append(
                    f"{filename}: `selected_local_organization_id` must be a positive integer, got {selected_local_organization_id!r}"
                )

            organizations_scanned = payload.get("organizations_scanned")
            if not isinstance(organizations_scanned, int) or organizations_scanned < 0:
                violations.append(
                    f"{filename}: `organizations_scanned` must be a non-negative integer, got {organizations_scanned!r}"
                )

            for list_key in (
                "benchmark_ready_organization_ids",
                "benchmark_ready_demo_organization_ids",
                "benchmark_ready_non_demo_organization_ids",
                "blocked_organization_ids",
                "organizations",
                "policy_guidance",
                "selected_local_organization_remediation",
            ):
                if not isinstance(payload.get(list_key), list):
                    violations.append(f"{filename}: `{list_key}` must be a list")

            for org_id_key in (
                "benchmark_ready_organization_ids",
                "benchmark_ready_demo_organization_ids",
                "benchmark_ready_non_demo_organization_ids",
                "blocked_organization_ids",
            ):
                for organization_id in payload.get(org_id_key, []):
                    if not isinstance(organization_id, int) or organization_id <= 0:
                        violations.append(
                            f"{filename}: `{org_id_key}` entries must be positive integers, got {organization_id!r}"
                        )

            for index, guidance in enumerate(payload.get("policy_guidance", [])):
                if not isinstance(guidance, str) or not guidance.strip():
                    violations.append(
                        f"{filename}: `policy_guidance[{index}]` must be a non-empty string"
                    )

            for index, guidance in enumerate(payload.get("selected_local_organization_remediation", [])):
                if not isinstance(guidance, str) or not guidance.strip():
                    violations.append(
                        f"{filename}: `selected_local_organization_remediation[{index}]` must be a non-empty string"
                    )

            for index, organization in enumerate(payload.get("organizations", [])):
                if not isinstance(organization, dict):
                    violations.append(f"{filename}: `organizations[{index}]` must be an object")
                    continue

                organization_id = organization.get("organization_id")
                if not isinstance(organization_id, int) or organization_id <= 0:
                    violations.append(
                        f"{filename}: `organizations[{index}].organization_id` must be a positive integer, got {organization_id!r}"
                    )

                runtime_status = organization.get("runtime_status")
                if runtime_status not in {"ready", "blocked"}:
                    violations.append(
                        f"{filename}: `organizations[{index}].runtime_status` must be `ready` or `blocked`, got {runtime_status!r}"
                    )

                organization_scope = organization.get("organization_scope")
                if organization_scope not in {"demo_dataset", "non_demo", "unknown"}:
                    violations.append(
                        f"{filename}: `organizations[{index}].organization_scope` must be demo_dataset/non_demo/unknown, got {organization_scope!r}"
                    )

                for list_key in ("readiness_blockers", "readiness_warnings"):
                    if not isinstance(organization.get(list_key), list):
                        violations.append(
                            f"{filename}: `organizations[{index}].{list_key}` must be a list"
                        )

            least_blocked_local_organization = payload.get("least_blocked_local_organization")
            if least_blocked_local_organization is not None:
                if not isinstance(least_blocked_local_organization, dict):
                    violations.append(
                        f"{filename}: `least_blocked_local_organization` must be an object or null"
                    )
                else:
                    for key in ("organization_id", "organization_name", "runtime_status"):
                        if key not in least_blocked_local_organization:
                            violations.append(
                                f"{filename}: `least_blocked_local_organization.{key}` is required when present"
                            )
                    organization_scope = least_blocked_local_organization.get("organization_scope")
                    if organization_scope not in {"demo_dataset", "non_demo", "unknown"}:
                        violations.append(
                            f"{filename}: `least_blocked_local_organization.organization_scope` must be demo_dataset/non_demo/unknown, got {organization_scope!r}"
                        )

            benchmark_ready_ids = _positive_organization_ids(
                payload.get("benchmark_ready_organization_ids")
            )
            benchmark_ready_demo_ids = _positive_organization_ids(
                payload.get("benchmark_ready_demo_organization_ids")
            )
            benchmark_ready_non_demo_ids = _positive_organization_ids(
                payload.get("benchmark_ready_non_demo_organization_ids")
            )
            ready_ids_from_entries = _ready_organization_ids(payload)
            if benchmark_ready_ids != ready_ids_from_entries:
                violations.append(
                    f"{filename}: `benchmark_ready_organization_ids` {sorted(benchmark_ready_ids)} must match ready organizations {sorted(ready_ids_from_entries)}"
                )
            if not benchmark_ready_demo_ids.issubset(benchmark_ready_ids):
                violations.append(
                    f"{filename}: `benchmark_ready_demo_organization_ids` {sorted(benchmark_ready_demo_ids)} must be a subset of `benchmark_ready_organization_ids` {sorted(benchmark_ready_ids)}"
                )
            if not benchmark_ready_non_demo_ids.issubset(benchmark_ready_ids):
                violations.append(
                    f"{filename}: `benchmark_ready_non_demo_organization_ids` {sorted(benchmark_ready_non_demo_ids)} must be a subset of `benchmark_ready_organization_ids` {sorted(benchmark_ready_ids)}"
                )
            if benchmark_ready_demo_ids & benchmark_ready_non_demo_ids:
                violations.append(
                    f"{filename}: `benchmark_ready_demo_organization_ids` and `benchmark_ready_non_demo_organization_ids` must not overlap, got {sorted(benchmark_ready_demo_ids & benchmark_ready_non_demo_ids)}"
                )

        if filename == "reevu_authority_gap_report.json":
            if payload.get("runtime_path") != "local":
                violations.append(
                    f"{filename}: `runtime_path` must be `local`, got {payload.get('runtime_path')!r}"
                )

            _validate_local_organization_selection(
                payload=payload,
                filename=filename,
                violations=violations,
            )

            if not isinstance(payload.get("surface_gaps"), list):
                violations.append(f"{filename}: `surface_gaps` must be a list")
            if not isinstance(payload.get("common_blockers_across_blocked_orgs"), list):
                violations.append(
                    f"{filename}: `common_blockers_across_blocked_orgs` must be a list"
                )
            for list_key in (
                "benchmark_ready_demo_organization_ids",
                "benchmark_ready_non_demo_organization_ids",
                "policy_guidance",
            ):
                if not isinstance(payload.get(list_key), list):
                    violations.append(f"{filename}: `{list_key}` must be a list")

            for org_id_key in (
                "benchmark_ready_organization_ids",
                "benchmark_ready_demo_organization_ids",
                "benchmark_ready_non_demo_organization_ids",
                "blocked_organization_ids",
            ):
                for organization_id in payload.get(org_id_key, []):
                    if not isinstance(organization_id, int) or organization_id <= 0:
                        violations.append(
                            f"{filename}: `{org_id_key}` entries must be positive integers, got {organization_id!r}"
                        )

            for index, guidance in enumerate(payload.get("policy_guidance", [])):
                if not isinstance(guidance, str) or not guidance.strip():
                    violations.append(
                        f"{filename}: `policy_guidance[{index}]` must be a non-empty string"
                    )

            overall_gap_status = payload.get("overall_gap_status")
            if overall_gap_status not in {
                "clear",
                "no_benchmark_ready_local_org",
                "selected_local_org_blocked",
                "surface_failures_present",
            }:
                violations.append(
                    f"{filename}: `overall_gap_status` has unexpected value {overall_gap_status!r}"
                )

            for index, surface_gap in enumerate(payload.get("surface_gaps", [])):
                if not isinstance(surface_gap, dict):
                    violations.append(f"{filename}: `surface_gaps[{index}]` must be an object")
                    continue

                for required_key in (
                    "surface_key",
                    "surface_label",
                    "trust_status",
                    "total_cases",
                    "failed_cases",
                    "pass_rate",
                    "gap_status",
                    "benchmark_ids",
                    "failed_benchmark_ids",
                    "failed_checks",
                    "safe_failure_sources",
                    "safe_failure_error_categories",
                    "failed_case_details",
                    "common_blockers_across_blocked_orgs",
                ):
                    if required_key not in surface_gap:
                        violations.append(
                            f"{filename}: `surface_gaps[{index}].{required_key}` is required"
                        )

                if surface_gap.get("trust_status") not in {"trusted", "partial"}:
                    violations.append(
                        f"{filename}: `surface_gaps[{index}].trust_status` must be `trusted` or `partial`, got {surface_gap.get('trust_status')!r}"
                    )

                gap_status = surface_gap.get("gap_status")
                if gap_status not in {
                    "clear",
                    "blocked_no_benchmark_ready_local_org",
                    "blocked_selected_local_org",
                    "failing_with_ready_local_org_available",
                }:
                    violations.append(
                        f"{filename}: `surface_gaps[{index}].gap_status` has unexpected value {gap_status!r}"
                    )

                if not _is_rate_in_range(surface_gap.get("pass_rate")):
                    violations.append(
                        f"{filename}: `surface_gaps[{index}].pass_rate` must be numeric in [0,1], got {surface_gap.get('pass_rate')!r}"
                    )

                for list_key in (
                    "benchmark_ids",
                    "failed_benchmark_ids",
                    "failed_checks",
                    "safe_failure_sources",
                    "safe_failure_error_categories",
                    "failed_case_details",
                    "common_blockers_across_blocked_orgs",
                ):
                    if not isinstance(surface_gap.get(list_key), list):
                        violations.append(
                            f"{filename}: `surface_gaps[{index}].{list_key}` must be a list"
                        )

                if "failure_attribution_statuses" in surface_gap and not isinstance(
                    surface_gap.get("failure_attribution_statuses"), list
                ):
                    violations.append(
                        f"{filename}: `surface_gaps[{index}].failure_attribution_statuses` must be a list when present"
                    )

                if "failure_attribution_summary" in surface_gap and not isinstance(
                    surface_gap.get("failure_attribution_summary"), dict
                ):
                    violations.append(
                        f"{filename}: `surface_gaps[{index}].failure_attribution_summary` must be an object when present"
                    )

                for detail_index, failed_case_detail in enumerate(surface_gap.get("failed_case_details", [])):
                    if not isinstance(failed_case_detail, dict):
                        violations.append(
                            f"{filename}: `surface_gaps[{index}].failed_case_details[{detail_index}]` must be an object"
                        )
                        continue

                    failure_attribution_status = failed_case_detail.get("failure_attribution_status")
                    if failure_attribution_status is not None and not isinstance(
                        failure_attribution_status, str
                    ):
                        violations.append(
                            f"{filename}: `surface_gaps[{index}].failed_case_details[{detail_index}].failure_attribution_status` must be a string or null"
                        )

                    failure_attribution_reason = failed_case_detail.get("failure_attribution_reason")
                    if failure_attribution_reason is not None and not isinstance(
                        failure_attribution_reason, str
                    ):
                        violations.append(
                            f"{filename}: `surface_gaps[{index}].failed_case_details[{detail_index}].failure_attribution_reason` must be a string or null"
                        )

                    for list_key in (
                        "failure_attribution_relevant_blockers",
                        "failure_attribution_relevant_warnings",
                        "failure_attribution_unmapped_expected_domains",
                    ):
                        if list_key in failed_case_detail and not isinstance(
                            failed_case_detail.get(list_key), list
                        ):
                            violations.append(
                                f"{filename}: `surface_gaps[{index}].failed_case_details[{detail_index}].{list_key}` must be a list when present"
                            )

        if filename == "reevu_real_question_managed.json":
            runtime_status = payload.get("runtime_status")
            if runtime_status != "evaluated":
                violations.append(
                    f"{filename}: `runtime_status` must be `evaluated`, got {runtime_status!r}"
                )

    local_readiness_payload = payloads.get("reevu_local_readiness_census.json")
    authority_gap_payload = payloads.get("reevu_authority_gap_report.json")
    default_ready_ids = _ready_organization_ids(local_readiness_payload)

    if isinstance(authority_gap_payload, dict):
        authority_gap_ready_ids = _positive_organization_ids(
            authority_gap_payload.get("benchmark_ready_organization_ids")
        )
        if authority_gap_ready_ids != default_ready_ids:
            violations.append(
                "reevu_authority_gap_report.json: `benchmark_ready_organization_ids` "
                f"{sorted(authority_gap_ready_ids)} must match default readiness census ready organizations {sorted(default_ready_ids)}"
            )

        if default_ready_ids and authority_gap_payload.get("overall_gap_status") == "no_benchmark_ready_local_org":
            violations.append(
                "reevu_authority_gap_report.json: `overall_gap_status` cannot be `no_benchmark_ready_local_org` when the default readiness census includes benchmark-ready organizations"
            )

    supplementary_ready_ids: set[int] = set()
    for supplemental_path in sorted(reports_dir.glob("reevu_local_readiness_census_org*.json")):
        try:
            supplemental_payload = json.loads(supplemental_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            violations.append(f"invalid JSON in {supplemental_path.name}: {exc}")
            continue

        if not isinstance(supplemental_payload, dict):
            violations.append(
                f"{supplemental_path.name}: top-level JSON payload must be an object"
            )
            continue

        supplementary_ready_ids.update(_ready_organization_ids(supplemental_payload))

    missing_ready_ids = sorted(supplementary_ready_ids - default_ready_ids)
    if missing_ready_ids:
        violations.append(
            "reevu_local_readiness_census.json: missing benchmark-ready organization ids present in supplementary readiness artifacts: "
            f"{missing_ready_ids}"
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
    parser.add_argument(
        "--required-runtime-paths",
        nargs="+",
        choices=("local", "managed"),
        default=["local", "managed"],
        help="Runtime-path benchmark artifacts that must be present for this validation run.",
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    ok, violations, info = validate_artifacts(
        reports_dir,
        required_runtime_paths=tuple(args.required_runtime_paths),
    )

    print("REEVU Artifact Integrity Summary")
    print(f"  reports_dir: {reports_dir}")
    print(f"  artifacts_expected: {len(build_artifact_specs(tuple(args.required_runtime_paths)))}")
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
