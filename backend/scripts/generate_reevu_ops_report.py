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
        },
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
