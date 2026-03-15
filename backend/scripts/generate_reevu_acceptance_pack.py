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
import subprocess
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
        status = "✅ passed" if outcome["status"] == "passed" else "❌ failed"
        lines.append(
            f"| `{outcome['command']}` | {status} | {outcome['duration_seconds']} | {outcome['return_code']} |"
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
    args = parser.parse_args()

    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent

    gate_commands = [
        "uv run pytest tests/units/api/v2 -q",
        "uv run pytest tests/units/test_reevu_stage_c.py -q",
        "uv run pytest tests/units/test_reevu_metrics.py -q",
        "uv run python scripts/eval_cross_domain_reasoning.py",
        "uv run python scripts/generate_reevu_ops_report.py",
    ]

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

    artifact_status = _artifact_integrity(
        {
            "trace_completeness_baseline": reports_dir / "reevu_trace_completeness_baseline.json",
            "top_intent_routing_baseline": reports_dir / "reevu_top_intent_routing_baseline.json",
            "stage_a_kpi_report": reports_dir / "reevu_stage_a_kpi_report.json",
            "cross_domain_reasoning_baseline": reports_dir / "reevu_cross_domain_reasoning_baseline.json",
            "ops_report_json": reports_dir / "reevu_ops_report.json",
            "ops_report_markdown": reports_dir / "reevu_ops_report.md",
        }
    )

    kpi_deltas = _compute_kpi_deltas(current_report=current_report, comparator_report=comparator_report)

    blockers: list[str] = []
    failed_gate = [item for item in gate_outcomes if item["status"] == "failed"]
    if failed_gate:
        blockers.append("One or more gate commands failed.")
    if not artifact_status["all_valid"]:
        blockers.append("Artifact integrity checks reported missing/invalid files.")

    pack = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit_hash": _resolve_git_commit(repo_root=repo_root),
        "overall_status": "passed" if not blockers else "blocked",
        "gate_outcomes": gate_outcomes,
        "kpi_deltas": kpi_deltas,
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
