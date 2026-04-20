"""Generate the REEVU final acceptance pack.

This script compiles final operator evidence into:
- JSON acceptance pack in ``backend/test_reports``
- Markdown acceptance summary in ``backend/test_reports``
- Documentation summary under ``docs/development/reevu``

Usage:
    cd backend && uv run python scripts/generate_reevu_acceptance_pack.py
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _run_command(command: str, *, cwd: Path) -> dict[str, Any]:
    started = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    duration = round(time.perf_counter() - started, 3)
    return {
        "command": command,
        "status": "passed" if result.returncode == 0 else "failed",
        "return_code": result.returncode,
        "duration_seconds": duration,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _load_json_safe(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_git_commit(*, repo_root: Path) -> str:
    result = subprocess.run(
        "git rev-parse HEAD",
        cwd=repo_root,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _artifact_integrity(artifacts: dict[str, Path]) -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    for label, path in artifacts.items():
        status: dict[str, Any] = {
            "path": str(path),
            "exists": path.exists(),
            "valid": False,
            "details": "",
        }
        if not path.exists():
            status["details"] = "missing"
            statuses[label] = status
            continue

        try:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))
                status["valid"] = True
                status["details"] = "valid JSON"
            else:
                content = path.read_text(encoding="utf-8").strip()
                status["valid"] = bool(content)
                status["details"] = "non-empty text" if content else "empty file"
        except Exception as exc:  # pragma: no cover - defensive reporting
            status["details"] = f"invalid: {exc}"

        statuses[label] = status

    return {
        "all_valid": all(item["exists"] and item["valid"] for item in statuses.values()),
        "artifacts": statuses,
    }


def _compute_kpi_deltas(*, current_report: dict[str, Any] | None, comparator_report: dict[str, Any] | None) -> dict[str, Any]:
    if current_report is None:
        return {"status": "missing_current_report", "metrics": {}}

    current_checks = current_report.get("kpi_checks", {})
    comparator_checks = (comparator_report or {}).get("kpi_checks", {})

    metrics: dict[str, Any] = {}
    for metric_name, metric in current_checks.items():
        current_value = metric.get("value")
        comparator_value = comparator_checks.get(metric_name, {}).get("value")
        delta = None
        if isinstance(current_value, (int, float)) and isinstance(comparator_value, (int, float)):
            delta = current_value - comparator_value

        metrics[metric_name] = {
            "current": current_value,
            "comparator": comparator_value,
            "delta": delta,
            "floor": metric.get("floor"),
            "floor_met": metric.get("met"),
        }

    return {
        "status": "computed",
        "comparator_available": comparator_report is not None,
        "metrics": metrics,
    }


def _build_gate_commands(
    *,
    managed_base_url: str | None,
    managed_auth_token: str | None,
    python_command: str | None = None,
) -> tuple[list[str], list[str]]:
    interpreter_command = python_command or _resolve_gate_python_command()
    commands = [
        f"{interpreter_command} -m pytest tests/units/api/v2 -q",
        f"{interpreter_command} -m pytest tests/units/test_reevu_stage_c.py -q",
        f"{interpreter_command} -m pytest tests/units/test_reevu_metrics.py -q",
        f"{interpreter_command} scripts/eval_cross_domain_reasoning.py",
        f"{interpreter_command} scripts/eval_real_question_benchmark.py --runtime-path local --json-output test_reports/reevu_real_question_local.json --local-readiness-census-output test_reports/reevu_local_readiness_census.json --fail-on-failed-cases",
        f"{interpreter_command} scripts/generate_reevu_authority_gap_report.py --benchmark-artifact test_reports/reevu_real_question_local.json --readiness-census-artifact test_reports/reevu_local_readiness_census.json --json-output test_reports/reevu_authority_gap_report.json",
    ]
    required_runtime_paths = ["local"]

    if managed_base_url:
        managed_command = (
            f"{interpreter_command} scripts/eval_real_question_benchmark.py "
            "--runtime-path managed "
            f"--managed-base-url {shlex.quote(managed_base_url)} "
            "--json-output test_reports/reevu_real_question_managed.json "
            "--fail-on-failed-cases"
        )
        if managed_auth_token:
            managed_command += f" --managed-auth-token {shlex.quote(managed_auth_token)}"
        commands.append(managed_command)
        required_runtime_paths.append("managed")

    commands.append(f"{interpreter_command} scripts/generate_reevu_ops_report.py")
    commands.append(
        f"{interpreter_command} scripts/validate_reevu_artifacts.py --required-runtime-paths "
        + " ".join(required_runtime_paths)
    )

    return commands, required_runtime_paths


def _resolve_gate_python_command() -> str:
    current_python = Path(sys.executable)
    backend_root = Path(__file__).resolve().parents[1]
    venv_python = backend_root / "venv" / "bin" / "python"

    if sys.prefix != getattr(sys, "base_prefix", sys.prefix) and current_python.exists():
        return shlex.quote(str(current_python))

    if current_python.exists() and current_python.name.startswith("python"):
        current_parts = {part.name for part in current_python.parents}
        if "venv" in current_parts:
            return shlex.quote(str(current_python))

    if venv_python.exists():
        return shlex.quote(str(venv_python))

    return "uv run python"


def _build_artifact_map(reports_dir: Path, *, required_runtime_paths: list[str]) -> dict[str, Path]:
    artifacts = {
        "trace_completeness_baseline": reports_dir / "reevu_trace_completeness_baseline.json",
        "top_intent_routing_baseline": reports_dir / "reevu_top_intent_routing_baseline.json",
        "stage_a_kpi_report": reports_dir / "reevu_stage_a_kpi_report.json",
        "cross_domain_reasoning_baseline": reports_dir / "reevu_cross_domain_reasoning_baseline.json",
        "real_question_local": reports_dir / "reevu_real_question_local.json",
        "ops_report_json": reports_dir / "reevu_ops_report.json",
        "ops_report_markdown": reports_dir / "reevu_ops_report.md",
    }
    if "local" in required_runtime_paths:
        artifacts["local_readiness_census"] = reports_dir / "reevu_local_readiness_census.json"
        artifacts["authority_gap_report"] = reports_dir / "reevu_authority_gap_report.json"
    if "managed" in required_runtime_paths:
        artifacts["real_question_managed"] = reports_dir / "reevu_real_question_managed.json"
    return artifacts


def _build_local_readiness_census_summary(reports_dir: Path) -> dict[str, Any]:
    payload = _load_json_safe(reports_dir / "reevu_local_readiness_census.json")
    if payload is None:
        return {"present": False}

    organizations = payload.get("organizations") if isinstance(payload.get("organizations"), list) else []
    selected_local_organization_id = payload.get("selected_local_organization_id")
    selected_entry = next(
        (
            entry
            for entry in organizations
            if isinstance(entry, dict) and entry.get("organization_id") == selected_local_organization_id
        ),
        None,
    )
    ready_candidates = [
        {
            "organization_id": entry.get("organization_id"),
            "organization_name": entry.get("organization_name"),
            "organization_scope": entry.get("organization_scope"),
        }
        for entry in organizations
        if isinstance(entry, dict) and entry.get("runtime_status") == "ready"
    ]
    least_blocked_local_organization = (
        payload.get("least_blocked_local_organization")
        if isinstance(payload.get("least_blocked_local_organization"), dict)
        else None
    )

    selection = payload.get("local_organization_selection") or {}
    return {
        "present": True,
        "selection_mode": selection.get("mode"),
        "selected_local_organization_id": selected_local_organization_id,
        "selected_local_organization_name": selected_entry.get("organization_name") if isinstance(selected_entry, dict) else None,
        "selected_local_organization_scope": selected_entry.get("organization_scope") if isinstance(selected_entry, dict) else None,
        "selected_local_organization_runtime_status": selected_entry.get("runtime_status") if isinstance(selected_entry, dict) else None,
        "organizations_scanned": payload.get("organizations_scanned"),
        "benchmark_ready_organization_ids": payload.get("benchmark_ready_organization_ids", []),
        "benchmark_ready_demo_organization_ids": payload.get("benchmark_ready_demo_organization_ids", []),
        "benchmark_ready_non_demo_organization_ids": payload.get("benchmark_ready_non_demo_organization_ids", []),
        "blocked_organization_ids": payload.get("blocked_organization_ids", []),
        "policy_guidance": payload.get("policy_guidance", []),
        "selected_local_organization_remediation": payload.get(
            "selected_local_organization_remediation",
            [],
        ),
        "ready_candidates": ready_candidates,
        "least_blocked_local_organization": least_blocked_local_organization,
        "organizations": organizations,
    }


def _build_authority_gap_summary(reports_dir: Path) -> dict[str, Any]:
    payload = _load_json_safe(reports_dir / "reevu_authority_gap_report.json")
    if payload is None:
        return {"present": False}

    surface_gaps = payload.get("surface_gaps") if isinstance(payload.get("surface_gaps"), list) else []
    least_blocked_local_organization = (
        payload.get("least_blocked_local_organization")
        if isinstance(payload.get("least_blocked_local_organization"), dict)
        else None
    )
    return {
        "present": True,
        "overall_gap_status": payload.get("overall_gap_status"),
        "selected_local_organization_id": payload.get("selected_local_organization_id"),
        "organizations_scanned": payload.get("organizations_scanned"),
        "benchmark_ready_organization_ids": payload.get("benchmark_ready_organization_ids", []),
        "benchmark_ready_demo_organization_ids": payload.get("benchmark_ready_demo_organization_ids", []),
        "benchmark_ready_non_demo_organization_ids": payload.get("benchmark_ready_non_demo_organization_ids", []),
        "common_blockers_across_blocked_orgs": payload.get("common_blockers_across_blocked_orgs", []),
        "policy_guidance": payload.get("policy_guidance", []),
        "selected_local_organization_remediation": payload.get(
            "selected_local_organization_remediation",
            [],
        ),
        "least_blocked_local_organization": least_blocked_local_organization,
        "surface_gaps": surface_gaps,
    }


def _format_local_organization_label(organization: dict[str, Any]) -> str:
    organization_id = organization.get("organization_id") or "N/A"
    organization_name = organization.get("organization_name") or "unnamed"
    label = f"{organization_id} ({organization_name})"
    if organization.get("organization_scope") == "demo_dataset":
        return f"{label}, demo dataset"
    return label


def _format_failed_case_attribution(detail: dict[str, Any]) -> str:
    benchmark_id = detail.get("benchmark_id") or "unknown-case"
    source = detail.get("safe_failure_source") or "unknown-source"
    error_category = detail.get("safe_failure_error_category") or "unknown-category"
    missing = ", ".join(str(item) for item in (detail.get("safe_failure_missing") or []))
    searched = ", ".join(str(item) for item in (detail.get("safe_failure_searched") or []))
    failure_attribution_status = detail.get("failure_attribution_status")
    failure_attribution_reason = detail.get("failure_attribution_reason")
    relevant_blockers = ", ".join(
        str(item) for item in (detail.get("failure_attribution_relevant_blockers") or [])
    )
    relevant_warnings = ", ".join(
        str(item) for item in (detail.get("failure_attribution_relevant_warnings") or [])
    )

    parts = [f"{benchmark_id}: {source} / {error_category}"]
    if missing:
        parts.append(f"missing {missing}")
    if searched:
        parts.append(f"searched {searched}")
    if isinstance(failure_attribution_status, str) and failure_attribution_status:
        parts.append(f"attribution {failure_attribution_status}")
    if relevant_blockers:
        parts.append(f"relevant blockers {relevant_blockers}")
    if relevant_warnings:
        parts.append(f"relevant warnings {relevant_warnings}")
    if isinstance(failure_attribution_reason, str) and failure_attribution_reason:
        parts.append(failure_attribution_reason)
    return " ; ".join(parts)


def _build_real_question_readiness(
    reports_dir: Path,
    *,
    required_runtime_paths: list[str],
) -> dict[str, dict[str, Any]]:
    readiness: dict[str, dict[str, Any]] = {}
    for runtime_path in required_runtime_paths:
        payload = _load_json_safe(reports_dir / f"reevu_real_question_{runtime_path}.json")
        readiness[runtime_path] = {
            "present": payload is not None,
            "runtime_status": payload.get("runtime_status") if payload else None,
            "runtime_target": payload.get("runtime_target") if payload else None,
            "local_organization_id": payload.get("local_organization_id") if payload else None,
            "readiness_blockers": payload.get("readiness_blockers", []) if payload else [],
            "readiness_warnings": payload.get("readiness_warnings", []) if payload else [],
            "pass_rate": payload.get("pass_rate") if payload else None,
            "passed_cases": payload.get("passed_cases") if payload else None,
            "failed_cases": payload.get("failed_cases") if payload else None,
            "total_cases": payload.get("total_cases") if payload else None,
        }
    return readiness


def _find_gate_outcome(
    gate_outcomes: list[dict[str, Any]],
    *,
    command_fragment: str,
) -> dict[str, Any] | None:
    return next(
        (
            outcome
            for outcome in gate_outcomes
            if command_fragment in str(outcome.get("command") or "")
        ),
        None,
    )


def _build_managed_runtime_preflight(
    reports_dir: Path,
    *,
    managed_base_url: str | None,
    managed_auth_token: str | None,
    gate_outcomes: list[dict[str, Any]],
) -> dict[str, Any]:
    managed_payload = _load_json_safe(reports_dir / "reevu_real_question_managed.json")
    managed_gate_outcome = _find_gate_outcome(
        gate_outcomes,
        command_fragment="scripts/eval_real_question_benchmark.py --runtime-path managed",
    )

    status = "pending_configuration"
    summary = (
        "Managed runtime evaluation is pending configuration because no managed base URL "
        "was supplied for this acceptance run."
    )
    notes: list[str] = []

    managed_artifact_present = managed_payload is not None
    managed_artifact_target = managed_payload.get("runtime_target") if managed_payload else None
    managed_artifact_runtime_status = (
        managed_payload.get("runtime_status") if managed_payload else None
    )

    if managed_base_url:
        if not managed_auth_token:
            notes.append(
                "Managed auth token was not supplied for this acceptance run. "
                "Targets that require bearer auth may still reject the managed benchmark."
            )

        if (
            managed_artifact_present
            and managed_artifact_runtime_status == "evaluated"
            and managed_artifact_target == managed_base_url
        ):
            status = "evaluated"
            summary = (
                "Managed runtime evidence is available for the configured managed target."
            )
        elif managed_artifact_present and managed_artifact_runtime_status != "evaluated":
            status = "artifact_invalid"
            summary = (
                "Managed benchmark artifact is present, but it is not in the evaluated state "
                "required for final acceptance."
            )
        elif (
            managed_artifact_present
            and managed_artifact_runtime_status == "evaluated"
            and managed_artifact_target != managed_base_url
        ):
            status = "configured_target_mismatch"
            summary = (
                "Managed benchmark artifact targets a different managed runtime than the "
                "one configured for this acceptance run."
            )
        elif managed_gate_outcome and managed_gate_outcome.get("status") == "failed":
            status = "evaluation_failed"
            summary = (
                "Managed runtime evaluation failed before a matching evaluated artifact "
                "was available for final acceptance."
            )
        elif managed_gate_outcome and managed_gate_outcome.get("status") == "skipped":
            status = "ready_for_evaluation"
            summary = (
                "Managed runtime is configured, but the managed benchmark was not executed "
                "during this acceptance run."
            )
        else:
            status = "configured_missing_artifact"
            summary = (
                "Managed runtime is configured, but no matching evaluated managed benchmark "
                "artifact is available for final acceptance."
            )
    elif managed_artifact_present:
        notes.append(
            "Managed benchmark artifact exists on disk, but it is not counted for this "
            "acceptance run because no managed base URL was supplied."
        )

    return {
        "runtime_path": "managed",
        "status": status,
        "summary": summary,
        "counts_toward_final_acceptance": status == "evaluated",
        "managed_base_url": managed_base_url,
        "managed_base_url_supplied": bool(managed_base_url),
        "managed_auth_token_supplied": bool(managed_auth_token),
        "managed_gate_status": managed_gate_outcome.get("status") if managed_gate_outcome else "not_requested",
        "managed_gate_return_code": managed_gate_outcome.get("return_code") if managed_gate_outcome else None,
        "managed_artifact_present": managed_artifact_present,
        "managed_artifact_target": managed_artifact_target,
        "managed_artifact_runtime_status": managed_artifact_runtime_status,
        "notes": notes,
    }


def _collect_acceptance_blockers(
    *,
    gate_outcomes: list[dict[str, Any]],
    artifact_status: dict[str, Any],
    real_question_readiness: dict[str, dict[str, Any]],
    local_readiness_census: dict[str, Any] | None = None,
    managed_runtime_preflight: dict[str, Any] | None = None,
) -> list[str]:
    blockers: list[str] = []
    failed_gate = [item for item in gate_outcomes if item["status"] == "failed"]
    unexplained_failed_gate = [
        item
        for item in failed_gate
        if not _is_gate_failure_explained_by_readiness(
            item,
            real_question_readiness=real_question_readiness,
            managed_runtime_preflight=managed_runtime_preflight,
        )
    ]
    if unexplained_failed_gate:
        blockers.append("One or more gate commands failed.")
    if not artifact_status["all_valid"]:
        blockers.append("Artifact integrity checks reported missing/invalid files.")

    if isinstance(managed_runtime_preflight, dict):
        managed_status = managed_runtime_preflight.get("status")
        managed_target = managed_runtime_preflight.get("managed_base_url") or "the configured managed target"
        managed_artifact_target = managed_runtime_preflight.get("managed_artifact_target") or "N/A"

        if managed_status == "pending_configuration":
            blockers.append(
                "Managed runtime evaluation is pending configuration: supply a managed base URL "
                "and rerun the managed real-question benchmark before final acceptance."
            )
        elif managed_status in {"ready_for_evaluation", "configured_missing_artifact"}:
            blockers.append(
                f"Managed runtime is configured for {managed_target}, but no evaluated managed real-question artifact is available for final acceptance."
            )
        elif managed_status == "configured_target_mismatch":
            blockers.append(
                f"Managed runtime evidence targets {managed_artifact_target}, but this acceptance run is configured for {managed_target}; rerun the managed real-question benchmark for the configured target before final acceptance."
            )
        elif managed_status == "evaluation_failed":
            blockers.append(
                f"Managed runtime evaluation failed for {managed_target}; inspect the managed benchmark command output and rerun before final acceptance."
            )
        elif managed_status == "artifact_invalid":
            blockers.append(
                f"Managed benchmark artifact for {managed_target} is present but not in the evaluated state required for final acceptance."
            )

    for runtime_path, readiness in real_question_readiness.items():
        if not readiness["present"]:
            blockers.append(f"Real-question readiness artifact missing for runtime path: {runtime_path}.")
            continue

        if readiness.get("runtime_status") == "blocked":
            organization_id = readiness.get("local_organization_id")
            blocker_list = readiness.get("readiness_blockers") or []
            details = ", ".join(str(item) for item in blocker_list) or "unspecified readiness blockers"
            ready_candidates = []
            least_blocked_local_organization = None
            policy_guidance: list[str] = []
            remediation_guidance: list[str] = []
            if runtime_path == "local" and isinstance(local_readiness_census, dict):
                ready_candidates = local_readiness_census.get("ready_candidates") or []
                least_blocked_local_organization = (
                    local_readiness_census.get("least_blocked_local_organization")
                    if isinstance(local_readiness_census.get("least_blocked_local_organization"), dict)
                    else None
                )
                policy_guidance = [
                    guidance
                    for guidance in (local_readiness_census.get("policy_guidance") or [])
                    if isinstance(guidance, str) and guidance.strip()
                ]
                remediation_guidance = [
                    guidance
                    for guidance in (
                        local_readiness_census.get("selected_local_organization_remediation") or []
                    )
                    if isinstance(guidance, str) and guidance.strip()
                ]
            if runtime_path == "local" and isinstance(local_readiness_census, dict) and local_readiness_census.get("present"):
                if ready_candidates:
                    ready_candidate_label = ", ".join(
                        _format_local_organization_label(candidate)
                        for candidate in ready_candidates
                    )
                    blocker = (
                        f"Selected local runtime organization {organization_id} is not benchmark-ready: {details}. Benchmark-ready local organizations discovered: {ready_candidate_label}."
                    )
                    if policy_guidance:
                        blocker += " " + " ".join(policy_guidance)
                    if remediation_guidance:
                        blocker += " Recommended remediation: " + " ".join(remediation_guidance)
                    blockers.append(blocker)
                    continue

                if (
                    isinstance(least_blocked_local_organization, dict)
                    and least_blocked_local_organization.get("organization_id") != organization_id
                ):
                    least_blocked_id = least_blocked_local_organization.get("organization_id")
                    least_blocked_name = least_blocked_local_organization.get("organization_name") or "unnamed"
                    least_blocked_blockers = ", ".join(
                        str(item)
                        for item in (least_blocked_local_organization.get("readiness_blockers") or [])
                    ) or "unspecified readiness blockers"
                    blocker = (
                        f"No benchmark-ready local organizations were discovered. Selected organization {organization_id} is blocked: {details}. Least-blocked local organization is {least_blocked_id} ({least_blocked_name}): {least_blocked_blockers}."
                    )
                    if remediation_guidance:
                        blocker += " Recommended remediation: " + " ".join(remediation_guidance)
                    blockers.append(blocker)
                    continue

                blocker = (
                    f"No benchmark-ready local organizations were discovered. Selected organization {organization_id} is blocked: {details}."
                )
                if remediation_guidance:
                    blocker += " Recommended remediation: " + " ".join(remediation_guidance)
                blockers.append(blocker)
                continue

            blockers.append(
                f"Local runtime path is not benchmark-ready for organization {organization_id}: {details}."
            )
            continue

        if isinstance(readiness.get("failed_cases"), int) and readiness["failed_cases"] > 0:
            blockers.append(
                f"Real-question benchmark failures remain on runtime path: {runtime_path}."
            )

    return blockers


def _is_gate_failure_explained_by_readiness(
    gate_outcome: dict[str, Any],
    *,
    real_question_readiness: dict[str, dict[str, Any]],
    managed_runtime_preflight: dict[str, Any] | None,
) -> bool:
    command = str(gate_outcome.get("command") or "")

    if "scripts/eval_real_question_benchmark.py --runtime-path local" in command:
        local_readiness = real_question_readiness.get("local") or {}
        if local_readiness.get("runtime_status") == "blocked":
            return True
        failed_cases = local_readiness.get("failed_cases")
        if isinstance(failed_cases, int) and failed_cases > 0:
            return True

    if "scripts/eval_real_question_benchmark.py --runtime-path managed" in command:
        managed_status = (managed_runtime_preflight or {}).get("status")
        if managed_status in {
            "pending_configuration",
            "ready_for_evaluation",
            "configured_missing_artifact",
            "configured_target_mismatch",
            "evaluation_failed",
            "artifact_invalid",
        }:
            return True

    return False


def _format_percent(value: Any) -> str:
    return f"{value:.2%}" if isinstance(value, (int, float)) else "N/A"


def _format_signed_percent(value: Any) -> str:
    return f"{value:+.2%}" if isinstance(value, (int, float)) else "N/A"


def _generate_markdown(pack: dict[str, Any]) -> str:
    lines = [
        "# REEVU Final Acceptance Pack",
        "",
        f"**Generated at (UTC):** {pack['generated_at_utc']}  ",
        f"**Commit:** `{pack['commit_hash']}`  ",
        f"**Overall acceptance status:** **{pack['overall_status'].upper()}**",
        "",
        "## Gate Command Outcomes",
        "",
        "| Command | Status | Duration (s) | Return code |",
        "|---------|--------|--------------|-------------|",
    ]

    for outcome in pack["gate_outcomes"]:
        if outcome["status"] == "passed":
            status = "✅ passed"
        elif outcome["status"] == "skipped":
            status = "⏭ skipped"
        else:
            status = "❌ failed"
        return_code = outcome["return_code"] if outcome["return_code"] is not None else "N/A"
        lines.append(
            f"| `{outcome['command']}` | {status} | {outcome['duration_seconds']} | {return_code} |"
        )

    lines.extend([
        "",
        "## KPI Deltas vs Comparator",
        "",
        "| KPI | Current | Comparator | Delta | Floor | Floor met |",
        "|-----|---------|------------|-------|-------|-----------|",
    ])
    for metric_name, metric in pack["kpi_deltas"]["metrics"].items():
        floor_met = "✅" if metric.get("floor_met") else "❌"
        lines.append(
            f"| {metric_name} | {_format_percent(metric.get('current'))} | {_format_percent(metric.get('comparator'))} | {_format_signed_percent(metric.get('delta'))} | {_format_percent(metric.get('floor'))} | {floor_met} |"
        )

    lines.extend([
        "",
        "## Real-Question Readiness",
        "",
        "| Runtime path | Present | Status | Local org | Target | Passed | Failed | Total | Pass rate |",
        "|--------------|---------|--------|-----------|--------|--------|--------|-------|-----------|",
    ])
    for runtime_path, status in pack.get("real_question_readiness", {}).items():
        lines.append(
            f"| {runtime_path} | {'✅' if status['present'] else '❌'} | {status.get('runtime_status') or 'N/A'} | {status.get('local_organization_id') or 'N/A'} | {status.get('runtime_target') or 'N/A'} | {status.get('passed_cases', 'N/A')} | {status.get('failed_cases', 'N/A')} | {status.get('total_cases', 'N/A')} | {_format_percent(status.get('pass_rate'))} |"
        )

    readiness_notes: list[str] = []
    for runtime_path, status in pack.get("real_question_readiness", {}).items():
        blockers = status.get("readiness_blockers") or []
        warnings = status.get("readiness_warnings") or []
        if blockers:
            readiness_notes.append(f"- {runtime_path} blockers: {', '.join(str(item) for item in blockers)}")
        if warnings:
            readiness_notes.append(f"- {runtime_path} warnings: {', '.join(str(item) for item in warnings)}")
    if readiness_notes:
        lines.extend(["", "### Runtime Readiness Notes", "", *readiness_notes])

    managed_runtime_preflight = pack.get("managed_runtime_preflight", {})
    if managed_runtime_preflight:
        lines.extend(["", "## Managed Runtime Preflight", ""])
        lines.extend([
            f"**Status:** `{managed_runtime_preflight.get('status') or 'N/A'}`  ",
            f"**Counts toward final acceptance:** {'yes' if managed_runtime_preflight.get('counts_toward_final_acceptance') else 'no'}  ",
            f"**Managed target supplied:** {managed_runtime_preflight.get('managed_base_url') or 'not supplied'}  ",
            f"**Managed auth token supplied:** {'yes' if managed_runtime_preflight.get('managed_auth_token_supplied') else 'no'}  ",
            f"**Managed gate outcome:** `{managed_runtime_preflight.get('managed_gate_status') or 'N/A'}`  ",
            f"**Managed artifact present:** {'yes' if managed_runtime_preflight.get('managed_artifact_present') else 'no'}  ",
        ])
        if managed_runtime_preflight.get("managed_artifact_present"):
            lines.extend([
                f"**Managed artifact target:** {managed_runtime_preflight.get('managed_artifact_target') or 'N/A'}  ",
                f"**Managed artifact runtime status:** `{managed_runtime_preflight.get('managed_artifact_runtime_status') or 'N/A'}`  ",
            ])
        lines.extend(["", managed_runtime_preflight.get("summary") or "N/A"])
        if managed_runtime_preflight.get("notes"):
            lines.extend(["", "### Managed Preflight Notes", ""])
            lines.extend(
                f"- {note}" for note in managed_runtime_preflight.get("notes", [])
            )

    local_readiness_census = pack.get("local_readiness_census", {})
    lines.extend(["", "## Local Readiness Census", ""])
    if local_readiness_census.get("present"):
        ready_candidates = local_readiness_census.get("ready_candidates") or []
        least_blocked_local_organization = local_readiness_census.get("least_blocked_local_organization")
        ready_candidate_label = (
            ", ".join(
                _format_local_organization_label(candidate)
                for candidate in ready_candidates
            )
            if ready_candidates
            else "none"
        )
        lines.extend([
            f"**Selection mode:** `{local_readiness_census.get('selection_mode') or 'N/A'}`  ",
            f"**Selected local org:** {local_readiness_census.get('selected_local_organization_id') or 'N/A'}  ",
            f"**Organizations scanned:** {local_readiness_census.get('organizations_scanned', 'N/A')}  ",
            f"**Benchmark-ready local orgs:** {ready_candidate_label}",
        ])
        policy_guidance = [
            guidance
            for guidance in (local_readiness_census.get("policy_guidance") or [])
            if isinstance(guidance, str) and guidance.strip()
        ]
        remediation_guidance = [
            guidance
            for guidance in (local_readiness_census.get("selected_local_organization_remediation") or [])
            if isinstance(guidance, str) and guidance.strip()
        ]
        if isinstance(least_blocked_local_organization, dict):
            least_blocked_label = (
                f"{least_blocked_local_organization.get('organization_id') or 'N/A'} "
                f"({least_blocked_local_organization.get('organization_name') or 'unnamed'})"
            )
            least_blocked_blockers = ", ".join(
                str(item)
                for item in (least_blocked_local_organization.get('readiness_blockers') or [])
            )
            if least_blocked_blockers:
                least_blocked_label += f" — blockers: {least_blocked_blockers}"
            lines.append(f"**Least-blocked local org:** {least_blocked_label}")
        if policy_guidance:
            lines.extend(["", "### Local Selection Guidance", ""])
            lines.extend(f"- {guidance}" for guidance in policy_guidance)
        if remediation_guidance:
            lines.extend(["", "### Local Remediation Guidance", ""])
            lines.extend(f"- {guidance}" for guidance in remediation_guidance)
        lines.extend([
            "",
            "| Org ID | Name | Selected | Status | Blockers | Warnings |",
            "|--------|------|----------|--------|----------|----------|",
        ])
        for organization in local_readiness_census.get("organizations", []):
            lines.append(
                f"| {organization.get('organization_id', 'N/A')} | {organization.get('organization_name') or 'N/A'} | {'✅' if organization.get('selected') else ''} | {organization.get('runtime_status') or 'N/A'} | {', '.join(str(item) for item in organization.get('readiness_blockers') or []) or 'none'} | {', '.join(str(item) for item in organization.get('readiness_warnings') or []) or 'none'} |"
            )
    else:
        lines.append("Local readiness census artifact not present.")

    authority_gap_summary = pack.get("authority_gap_summary", {})
    lines.extend(["", "## Authority-Gap Report", ""])
    if authority_gap_summary.get("present"):
        least_blocked_local_organization = authority_gap_summary.get("least_blocked_local_organization")
        policy_guidance = [
            guidance
            for guidance in (authority_gap_summary.get("policy_guidance") or [])
            if isinstance(guidance, str) and guidance.strip()
        ]
        remediation_guidance = [
            guidance
            for guidance in (authority_gap_summary.get("selected_local_organization_remediation") or [])
            if isinstance(guidance, str) and guidance.strip()
        ]
        lines.extend([
            f"**Overall gap status:** `{authority_gap_summary.get('overall_gap_status') or 'N/A'}`  ",
            f"**Selected local org:** {authority_gap_summary.get('selected_local_organization_id') or 'N/A'}  ",
            f"**Organizations scanned:** {authority_gap_summary.get('organizations_scanned', 'N/A')}  ",
            f"**Common blockers across blocked orgs:** {', '.join(str(item) for item in authority_gap_summary.get('common_blockers_across_blocked_orgs') or []) or 'none'}",
        ])
        if isinstance(least_blocked_local_organization, dict):
            least_blocked_label = (
                f"{least_blocked_local_organization.get('organization_id') or 'N/A'} "
                f"({least_blocked_local_organization.get('organization_name') or 'unnamed'})"
            )
            least_blocked_blockers = ", ".join(
                str(item)
                for item in (least_blocked_local_organization.get('readiness_blockers') or [])
            )
            if least_blocked_blockers:
                least_blocked_label += f" — blockers: {least_blocked_blockers}"
            lines.append(f"**Least-blocked local org:** {least_blocked_label}")
        if policy_guidance:
            lines.extend(["", "### Authority-Gap Selection Guidance", ""])
            lines.extend(f"- {guidance}" for guidance in policy_guidance)
        if remediation_guidance:
            lines.extend(["", "### Authority-Gap Remediation Guidance", ""])
            lines.extend(f"- {guidance}" for guidance in remediation_guidance)
        lines.extend([
            "",
            "| Surface | Trust | Failed | Total | Gap status | Common blockers |",
            "|---------|-------|--------|-------|------------|-----------------|",
        ])
        for surface_gap in authority_gap_summary.get("surface_gaps", []):
            lines.append(
                f"| {surface_gap.get('surface_label') or 'N/A'} | {surface_gap.get('trust_status') or 'N/A'} | {surface_gap.get('failed_cases', 'N/A')} | {surface_gap.get('total_cases', 'N/A')} | {surface_gap.get('gap_status') or 'N/A'} | {', '.join(str(item) for item in surface_gap.get('common_blockers_across_blocked_orgs') or []) or 'none'} |"
            )

        failed_case_attributions = [
            (surface_gap.get("surface_label") or "N/A", detail)
            for surface_gap in authority_gap_summary.get("surface_gaps", [])
            for detail in (surface_gap.get("failed_case_details") or [])
            if isinstance(detail, dict)
        ]
        if failed_case_attributions:
            lines.extend(["", "### Failed Case Attribution", ""])
            for surface_label, detail in failed_case_attributions:
                lines.append(f"- {surface_label}: {_format_failed_case_attribution(detail)}")
    else:
        lines.append("Authority-gap report artifact not present.")

    lines.extend([
        "",
        "## Artifact Integrity",
        "",
        f"**All artifacts valid:** {'✅ yes' if pack['artifact_integrity']['all_valid'] else '❌ no'}",
        "",
        "| Artifact | Exists | Valid | Details |",
        "|----------|--------|-------|---------|",
    ])

    for label, status in pack["artifact_integrity"]["artifacts"].items():
        lines.append(
            f"| {label} | {'✅' if status['exists'] else '❌'} | {'✅' if status['valid'] else '❌'} | {status['details']} |"
        )

    blockers = pack.get("blockers", [])
    lines.extend(["", "## Explicit Blockers", ""])
    if blockers:
        lines.extend([f"- {item}" for item in blockers])
    else:
        lines.append("- None.")

    lines.extend([
        "",
        "## Risk Notes (Placeholder)",
        "",
        "- [ ] Add operational and release risk notes.",
        "",
        "## Rollback Checklist (Placeholder)",
        "",
        "- [ ] Revert `backend/scripts/generate_reevu_acceptance_pack.py` if acceptance format is unsuitable.",
        "- [ ] Revert generated acceptance artifacts under `backend/test_reports/`.",
        "- [ ] Revert generated summary doc under `docs/development/reevu/`.",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate REEVU final acceptance pack.")
    parser.add_argument(
        "--reports-dir",
        default="test_reports",
        help="Directory containing REEVU report artifacts (relative to backend).",
    )
    parser.add_argument(
        "--comparator",
        default="test_reports/reevu_ops_report_baseline.json",
        help="Comparator REEVU ops report JSON path (relative to backend).",
    )
    parser.add_argument(
        "--json-output",
        default="test_reports/reevu_acceptance_pack.json",
        help="Output path for acceptance JSON (relative to backend).",
    )
    parser.add_argument(
        "--md-output",
        default="test_reports/reevu_acceptance_pack.md",
        help="Output path for acceptance markdown (relative to backend).",
    )
    parser.add_argument(
        "--summary-doc",
        default="../docs/development/reevu/reevu-final-acceptance-pack.md",
        help="Output path for docs summary markdown (relative to backend).",
    )
    parser.add_argument(
        "--skip-gate",
        action="store_true",
        help="Skip execution of gate commands and mark them as skipped.",
    )
    parser.add_argument(
        "--managed-base-url",
        default="",
        help="Optional managed REEVU base URL for acceptance-time runtime-path evaluation.",
    )
    parser.add_argument(
        "--managed-auth-token",
        default="",
        help="Optional managed REEVU bearer token for acceptance-time runtime-path evaluation.",
    )
    args = parser.parse_args()

    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent

    gate_commands, required_runtime_paths = _build_gate_commands(
        managed_base_url=args.managed_base_url or None,
        managed_auth_token=args.managed_auth_token or None,
    )

    if args.skip_gate:
        gate_outcomes = [
            {
                "command": command,
                "status": "skipped",
                "return_code": None,
                "duration_seconds": 0,
                "stdout": "",
                "stderr": "",
            }
            for command in gate_commands
        ]
    else:
        gate_outcomes = [_run_command(command, cwd=backend_dir) for command in gate_commands]

    reports_dir = backend_dir / args.reports_dir
    current_report = _load_json_safe(reports_dir / "reevu_ops_report.json")
    comparator_report = _load_json_safe(backend_dir / args.comparator)
    real_question_readiness = _build_real_question_readiness(
        reports_dir,
        required_runtime_paths=required_runtime_paths,
    )
    local_readiness_census = _build_local_readiness_census_summary(reports_dir)
    authority_gap_summary = _build_authority_gap_summary(reports_dir)
    managed_runtime_preflight = _build_managed_runtime_preflight(
        reports_dir,
        managed_base_url=args.managed_base_url or None,
        managed_auth_token=args.managed_auth_token or None,
        gate_outcomes=gate_outcomes,
    )

    artifact_status = _artifact_integrity(
        _build_artifact_map(reports_dir, required_runtime_paths=required_runtime_paths)
    )

    kpi_deltas = _compute_kpi_deltas(current_report=current_report, comparator_report=comparator_report)

    blockers = _collect_acceptance_blockers(
        gate_outcomes=gate_outcomes,
        artifact_status=artifact_status,
        real_question_readiness=real_question_readiness,
        local_readiness_census=local_readiness_census,
        managed_runtime_preflight=managed_runtime_preflight,
    )

    pack = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit_hash": _resolve_git_commit(repo_root=repo_root),
        "overall_status": "passed" if not blockers else "blocked",
        "gate_outcomes": gate_outcomes,
        "kpi_deltas": kpi_deltas,
        "required_runtime_paths": required_runtime_paths,
        "real_question_readiness": real_question_readiness,
        "managed_runtime_preflight": managed_runtime_preflight,
        "local_readiness_census": local_readiness_census,
        "authority_gap_summary": authority_gap_summary,
        "artifact_integrity": artifact_status,
        "blockers": blockers,
        "risk_notes": [
            "Placeholder: add release and production risk notes before final sign-off.",
        ],
        "rollback_checklist": [
            "Revert backend/scripts/generate_reevu_acceptance_pack.py if format is unsuitable.",
            "Revert generated acceptance artifacts under backend/test_reports/.",
            "Revert generated summary doc under docs/development/reevu/.",
        ],
    }

    json_output = backend_dir / args.json_output
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(pack, indent=2), encoding="utf-8")

    markdown = _generate_markdown(pack)
    md_output = backend_dir / args.md_output
    md_output.write_text(markdown, encoding="utf-8")

    summary_doc = (backend_dir / args.summary_doc).resolve()
    summary_doc.parent.mkdir(parents=True, exist_ok=True)
    summary_doc.write_text(markdown, encoding="utf-8")

    print("REEVU acceptance pack generated")
    print(f"  JSON: {json_output}")
    print(f"  Markdown: {md_output}")
    print(f"  Summary doc: {summary_doc}")
    print(f"  Overall status: {pack['overall_status']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
