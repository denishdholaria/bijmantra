"""Generate consolidated REEVU ops report from all available eval baselines.

Aggregates KPI baselines from Stage A/B/C evaluation harnesses into one
JSON + markdown report artifact for CI portability and ops review.

Usage:
    cd backend && uv run python scripts/generate_reevu_ops_report.py
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json_safe(path: Path) -> dict[str, Any] | None:
    """Load a JSON file if it exists, else return None."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _pct(value: float | None) -> str:
    return f"{value:.2%}" if value is not None else "N/A"


def _bool_status(met: bool | None) -> str:
    if met is None:
        return "⬜ not evaluated"
    return "✅ met" if met else "❌ not met"


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value.strip()]


def _int_list(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, int) and value > 0]


def _dict_or_none(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _build_local_runtime_readiness(baselines_dir: Path) -> dict[str, Any]:
    benchmark_payload = _load_json_safe(baselines_dir / "reevu_real_question_local.json")
    readiness_payload = _load_json_safe(baselines_dir / "reevu_local_readiness_census.json")
    authority_gap_payload = _load_json_safe(baselines_dir / "reevu_authority_gap_report.json")

    least_blocked_local_organization = _dict_or_none(
        (readiness_payload or {}).get("least_blocked_local_organization")
    )
    if least_blocked_local_organization is None:
        least_blocked_local_organization = _dict_or_none(
            (authority_gap_payload or {}).get("least_blocked_local_organization")
        )

    policy_guidance = _string_list((readiness_payload or {}).get("policy_guidance"))
    if not policy_guidance:
        policy_guidance = _string_list((authority_gap_payload or {}).get("policy_guidance"))

    remediation_guidance = _string_list(
        (readiness_payload or {}).get("selected_local_organization_remediation")
    )
    if not remediation_guidance:
        remediation_guidance = _string_list(
            (authority_gap_payload or {}).get("selected_local_organization_remediation")
        )

    benchmark_ready_organization_ids = _int_list(
        (readiness_payload or {}).get("benchmark_ready_organization_ids")
    )
    if not benchmark_ready_organization_ids:
        benchmark_ready_organization_ids = _int_list(
            (authority_gap_payload or {}).get("benchmark_ready_organization_ids")
        )

    benchmark_ready_demo_organization_ids = _int_list(
        (readiness_payload or {}).get("benchmark_ready_demo_organization_ids")
    )
    if not benchmark_ready_demo_organization_ids:
        benchmark_ready_demo_organization_ids = _int_list(
            (authority_gap_payload or {}).get("benchmark_ready_demo_organization_ids")
        )

    benchmark_ready_non_demo_organization_ids = _int_list(
        (readiness_payload or {}).get("benchmark_ready_non_demo_organization_ids")
    )
    if not benchmark_ready_non_demo_organization_ids:
        benchmark_ready_non_demo_organization_ids = _int_list(
            (authority_gap_payload or {}).get("benchmark_ready_non_demo_organization_ids")
        )

    selected_local_organization_id = None
    if benchmark_payload is not None:
        selected_local_organization_id = benchmark_payload.get("local_organization_id")
    if selected_local_organization_id is None and readiness_payload is not None:
        selected_local_organization_id = readiness_payload.get("selected_local_organization_id")
    if selected_local_organization_id is None and authority_gap_payload is not None:
        selected_local_organization_id = authority_gap_payload.get("selected_local_organization_id")

    return {
        "artifact_present": benchmark_payload is not None,
        "readiness_census_present": readiness_payload is not None,
        "authority_gap_report_present": authority_gap_payload is not None,
        "runtime_status": benchmark_payload.get("runtime_status") if benchmark_payload else None,
        "runtime_target": benchmark_payload.get("runtime_target") if benchmark_payload else None,
        "selected_local_organization_id": selected_local_organization_id,
        "pass_rate": benchmark_payload.get("pass_rate") if benchmark_payload else None,
        "passed_cases": benchmark_payload.get("passed_cases") if benchmark_payload else None,
        "failed_cases": benchmark_payload.get("failed_cases") if benchmark_payload else None,
        "total_cases": benchmark_payload.get("total_cases") if benchmark_payload else None,
        "readiness_blockers": _string_list(
            benchmark_payload.get("readiness_blockers") if benchmark_payload else []
        ),
        "readiness_warnings": _string_list(
            benchmark_payload.get("readiness_warnings") if benchmark_payload else []
        ),
        "benchmark_ready_organization_ids": benchmark_ready_organization_ids,
        "benchmark_ready_demo_organization_ids": benchmark_ready_demo_organization_ids,
        "benchmark_ready_non_demo_organization_ids": benchmark_ready_non_demo_organization_ids,
        "policy_guidance": policy_guidance,
        "selected_local_organization_remediation": remediation_guidance,
        "least_blocked_local_organization": least_blocked_local_organization,
        "authority_gap_status": authority_gap_payload.get("overall_gap_status")
        if authority_gap_payload
        else None,
        "common_blockers_across_blocked_orgs": _string_list(
            authority_gap_payload.get("common_blockers_across_blocked_orgs")
            if authority_gap_payload
            else []
        ),
    }


def _build_managed_runtime_readiness(baselines_dir: Path) -> dict[str, Any]:
    payload = _load_json_safe(baselines_dir / "reevu_real_question_managed.json")
    return {
        "artifact_present": payload is not None,
        "runtime_status": payload.get("runtime_status") if payload else None,
        "runtime_target": payload.get("runtime_target") if payload else None,
        "pass_rate": payload.get("pass_rate") if payload else None,
        "passed_cases": payload.get("passed_cases") if payload else None,
        "failed_cases": payload.get("failed_cases") if payload else None,
        "total_cases": payload.get("total_cases") if payload else None,
        "readiness_blockers": _string_list(payload.get("readiness_blockers") if payload else []),
        "readiness_warnings": _string_list(payload.get("readiness_warnings") if payload else []),
    }


def build_report(
    baselines_dir: Path,
    *,
    trace_floor: float = 0.99,
    intent_floor: float = 0.92,
    domain_detection_floor: float = 0.85,
    compound_floor: float = 0.80,
    step_adequacy_floor: float = 0.85,
    calibration_start_date: str | None = None,
) -> dict[str, Any]:
    """Build the consolidated report dict."""

    # Stage A baselines.
    trace = _load_json_safe(baselines_dir / "reevu_trace_completeness_baseline.json")
    intent = _load_json_safe(baselines_dir / "reevu_top_intent_routing_baseline.json")
    stage_a_kpi = _load_json_safe(baselines_dir / "reevu_stage_a_kpi_report.json")

    # Stage C baseline.
    cross_domain = _load_json_safe(baselines_dir / "reevu_cross_domain_reasoning_baseline.json")

    # Extract values.
    trace_val = float(trace.get("trace_completeness_rate", 0)) if trace else None
    intent_val = float(intent.get("actionable_function_precision", 0)) if intent else None
    domain_val = float(cross_domain.get("domain_detection_accuracy", 0)) if cross_domain else None
    compound_val = float(cross_domain.get("compound_classification_accuracy", 0)) if cross_domain else None
    step_val = float(cross_domain.get("step_adequacy_rate", 0)) if cross_domain else None

    # Floor checks.
    checks = {
        "trace_completeness": {
            "value": trace_val,
            "floor": trace_floor,
            "met": trace_val is not None and trace_val >= trace_floor,
        },
        "tool_call_precision": {
            "value": intent_val,
            "floor": intent_floor,
            "met": intent_val is not None and intent_val >= intent_floor,
        },
        "domain_detection_accuracy": {
            "value": domain_val,
            "floor": domain_detection_floor,
            "met": domain_val is not None and domain_val >= domain_detection_floor,
        },
        "compound_classification": {
            "value": compound_val,
            "floor": compound_floor,
            "met": compound_val is not None and compound_val >= compound_floor,
        },
        "step_adequacy": {
            "value": step_val,
            "floor": step_adequacy_floor,
            "met": step_val is not None and step_val >= step_adequacy_floor,
        },
    }

    all_met = all(c["met"] for c in checks.values() if c["value"] is not None)
    runtime_readiness = {
        "local": _build_local_runtime_readiness(baselines_dir),
        "managed": _build_managed_runtime_readiness(baselines_dir),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stages_evaluated": ["A", "C"],
        "kpi_checks": checks,
        "overall_floor_met": all_met,
        "sources": {
            "trace_completeness": str(baselines_dir / "reevu_trace_completeness_baseline.json"),
            "top_intent_routing": str(baselines_dir / "reevu_top_intent_routing_baseline.json"),
            "stage_a_kpi": str(baselines_dir / "reevu_stage_a_kpi_report.json"),
            "cross_domain_reasoning": str(baselines_dir / "reevu_cross_domain_reasoning_baseline.json"),
            "real_question_local": str(baselines_dir / "reevu_real_question_local.json"),
            "local_readiness_census": str(baselines_dir / "reevu_local_readiness_census.json"),
            "authority_gap_report": str(baselines_dir / "reevu_authority_gap_report.json"),
            "real_question_managed": str(baselines_dir / "reevu_real_question_managed.json"),
        },
        "runtime_readiness": runtime_readiness,
        "calibration_status": _build_calibration_status(
            checks, calibration_start_date=calibration_start_date
        ),
    }


def generate_markdown(report: dict[str, Any]) -> str:
    """Produce a human-readable markdown summary from the report dict."""
    lines = [
        "# REEVU Ops Report",
        "",
        f"**Generated:** {report['generated_at']}  ",
        f"**Stages evaluated:** {', '.join(report['stages_evaluated'])}  ",
        f"**Overall floor met:** {_bool_status(report['overall_floor_met'])}",
        "",
        "## KPI Summary",
        "",
        "| Metric | Value | Floor | Status |",
        "|--------|-------|-------|--------|",
    ]

    for name, check in report["kpi_checks"].items():
        lines.append(
            f"| {name} | {_pct(check['value'])} | {_pct(check['floor'])} | {_bool_status(check['met'])} |"
        )

    runtime_readiness = report.get("runtime_readiness") or {}
    local_runtime = runtime_readiness.get("local") or {}
    managed_runtime = runtime_readiness.get("managed") or {}
    lines.extend([
        "",
        "## Runtime Readiness",
        "",
        "### Local Runtime",
        "",
    ])

    if local_runtime.get("artifact_present"):
        benchmark_ready_ids = ", ".join(
            str(item) for item in local_runtime.get("benchmark_ready_organization_ids") or []
        ) or "none"
        lines.extend([
            f"**Status:** `{local_runtime.get('runtime_status') or 'N/A'}`  ",
            f"**Selected local org:** {local_runtime.get('selected_local_organization_id') or 'N/A'}  ",
            f"**Pass rate:** {_pct(local_runtime.get('pass_rate'))} ({local_runtime.get('passed_cases', 'N/A')}/{local_runtime.get('total_cases', 'N/A')} passed)  ",
            f"**Authority-gap status:** `{local_runtime.get('authority_gap_status') or 'N/A'}`  ",
            f"**Benchmark-ready org IDs:** {benchmark_ready_ids}",
        ])

        least_blocked_local_organization = _dict_or_none(
            local_runtime.get("least_blocked_local_organization")
        )
        if least_blocked_local_organization is not None:
            least_blocked_label = (
                f"{least_blocked_local_organization.get('organization_id') or 'N/A'} "
                f"({least_blocked_local_organization.get('organization_name') or 'unnamed'})"
            )
            least_blocked_blockers = ", ".join(
                str(item)
                for item in least_blocked_local_organization.get("readiness_blockers") or []
            )
            if least_blocked_blockers:
                least_blocked_label += f" — blockers: {least_blocked_blockers}"
            lines.append(f"**Least-blocked local org:** {least_blocked_label}")

        if local_runtime.get("readiness_blockers"):
            lines.extend(["", "### Local Readiness Blockers", ""])
            lines.extend(
                f"- {blocker}" for blocker in local_runtime.get("readiness_blockers") or []
            )
        if local_runtime.get("readiness_warnings"):
            lines.extend(["", "### Local Readiness Warnings", ""])
            lines.extend(
                f"- {warning}" for warning in local_runtime.get("readiness_warnings") or []
            )
        if local_runtime.get("common_blockers_across_blocked_orgs"):
            lines.extend(["", "### Common Blockers Across Blocked Orgs", ""])
            lines.extend(
                f"- {blocker}"
                for blocker in local_runtime.get("common_blockers_across_blocked_orgs") or []
            )
        if local_runtime.get("policy_guidance"):
            lines.extend(["", "### Local Selection Guidance", ""])
            lines.extend(
                f"- {guidance}" for guidance in local_runtime.get("policy_guidance") or []
            )
        if local_runtime.get("selected_local_organization_remediation"):
            lines.extend(["", "### Local Remediation Guidance", ""])
            lines.extend(
                f"- {guidance}"
                for guidance in local_runtime.get("selected_local_organization_remediation") or []
            )
    else:
        lines.append("Local runtime artifact not present.")

    lines.extend(["", "### Managed Runtime", ""])
    if managed_runtime.get("artifact_present"):
        lines.extend([
            f"**Status:** `{managed_runtime.get('runtime_status') or 'N/A'}`  ",
            f"**Target:** {managed_runtime.get('runtime_target') or 'N/A'}  ",
            f"**Pass rate:** {_pct(managed_runtime.get('pass_rate'))} ({managed_runtime.get('passed_cases', 'N/A')}/{managed_runtime.get('total_cases', 'N/A')} passed)",
        ])
        if managed_runtime.get("readiness_blockers"):
            lines.extend(["", "### Managed Readiness Blockers", ""])
            lines.extend(
                f"- {blocker}" for blocker in managed_runtime.get("readiness_blockers") or []
            )
        if managed_runtime.get("readiness_warnings"):
            lines.extend(["", "### Managed Readiness Warnings", ""])
            lines.extend(
                f"- {warning}" for warning in managed_runtime.get("readiness_warnings") or []
            )
    else:
        lines.append("Managed runtime artifact not present.")

    lines.extend([
        "",
        "## Sources",
        "",
    ])
    for label, path in report["sources"].items():
        lines.append(f"- **{label}**: `{path}`")

    return "\n".join(lines) + "\n"


def _build_calibration_status(
    kpi_checks: dict[str, Any],
    *,
    calibration_start_date: str | None = None,
) -> dict[str, Any]:
    """Build the calibration_status section of the report."""
    floors = {
        name: check["floor"]
        for name, check in kpi_checks.items()
    }

    if calibration_start_date:
        from datetime import date as _date
        try:
            start = _date.fromisoformat(calibration_start_date)
            days_elapsed = (datetime.now(timezone.utc).date() - start).days
        except ValueError:
            days_elapsed = 0
    else:
        days_elapsed = 0

    return {
        "current_floors": floors,
        "calibration_start_date": calibration_start_date,
        "days_since_start": days_elapsed,
        "calibration_ready": days_elapsed >= 30,
        "playbook": "docs/reevu/slo_calibration_playbook.md",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate consolidated REEVU ops report."
    )
    parser.add_argument(
        "--baselines-dir",
        default="test_reports",
        help="Directory containing baseline JSON artifacts",
    )
    parser.add_argument(
        "--json-output",
        default="test_reports/reevu_ops_report.json",
        help="Path to write JSON report",
    )
    parser.add_argument(
        "--md-output",
        default="test_reports/reevu_ops_report.md",
        help="Path to write markdown report",
    )
    parser.add_argument(
        "--calibration-start-date",
        default=None,
        help="ISO date when calibration baseline collection started (e.g. 2026-03-01). Omit if not started.",
    )
    args = parser.parse_args()

    baselines_dir = Path(args.baselines_dir)
    report = build_report(
        baselines_dir,
        calibration_start_date=args.calibration_start_date,
    )

    # Write JSON.
    json_path = Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # Write markdown.
    md_path = Path(args.md_output)
    md_path.write_text(generate_markdown(report), encoding="utf-8")

    print("REEVU Ops Report")
    for name, check in report["kpi_checks"].items():
        print(f"  {name}: {_pct(check['value'])} (floor {_pct(check['floor'])}) — {_bool_status(check['met'])}")
    print(f"  overall floor met: {_bool_status(report['overall_floor_met'])}")
    print(f"  wrote JSON: {json_path}")
    print(f"  wrote markdown: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
