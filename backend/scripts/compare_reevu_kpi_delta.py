"""Compare REEVU KPI baseline vs latest artifacts and report metric deltas.

Inputs:
  - baseline cross-domain JSON
  - latest cross-domain JSON
  - latest ops report JSON

Outputs:
  - human-readable table (stdout)
  - machine-readable JSON report artifact

Exit code semantics:
  - 0: successful comparison, even if KPI floors are not met
  - non-zero: malformed input files/schema
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CORE_METRICS = {
    "domain_detection_accuracy": "domain_detection_accuracy",
    "compound_classification": "compound_classification_accuracy",
    "step_adequacy": "step_adequacy_rate",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exercised by CLI failure path
        raise ValueError(f"failed to parse JSON {path}: {exc}") from exc


def _require_mapping(data: Any, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{context} must be a JSON object")
    return data


def _get_float(mapping: dict[str, Any], key: str, *, required: bool, context: str) -> float | None:
    if key not in mapping:
        if required:
            raise ValueError(f"missing required key '{key}' in {context}")
        return None

    value = mapping[key]
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    raise ValueError(f"key '{key}' in {context} must be numeric")


def _bool_floor_status(value: float | None, floor: float | None) -> bool | None:
    if value is None or floor is None:
        return None
    return value >= floor


def _status_str(status: bool | None) -> str:
    if status is None:
        return "N/A"
    return "PASS" if status else "FAIL"


def build_delta_report(
    baseline_cross_domain: dict[str, Any],
    latest_cross_domain: dict[str, Any],
    latest_ops_report: dict[str, Any],
) -> dict[str, Any]:
    baseline_cross_domain = _require_mapping(baseline_cross_domain, "baseline cross-domain report")
    latest_cross_domain = _require_mapping(latest_cross_domain, "latest cross-domain report")
    latest_ops_report = _require_mapping(latest_ops_report, "latest ops report")

    kpi_checks = _require_mapping(latest_ops_report.get("kpi_checks"), "latest ops report.kpi_checks")

    metrics: dict[str, dict[str, Any]] = {}

    for metric_name, cross_key in CORE_METRICS.items():
        op_check = _require_mapping(kpi_checks.get(metric_name), f"kpi_checks.{metric_name}")
        floor = _get_float(op_check, "floor", required=True, context=f"kpi_checks.{metric_name}")
        before = _get_float(
            baseline_cross_domain,
            cross_key,
            required=True,
            context="baseline cross-domain report",
        )
        after = _get_float(
            latest_cross_domain,
            cross_key,
            required=True,
            context="latest cross-domain report",
        )

        metrics[metric_name] = {
            "before": before,
            "after": after,
            "delta": round(after - before, 6),
            "floor": floor,
            "before_floor_met": _bool_floor_status(before, floor),
            "after_floor_met": _bool_floor_status(after, floor),
            "source": "cross_domain",
        }

    for metric_name, raw_check in kpi_checks.items():
        if metric_name in metrics:
            continue

        op_check = _require_mapping(raw_check, f"kpi_checks.{metric_name}")
        floor = _get_float(op_check, "floor", required=True, context=f"kpi_checks.{metric_name}")
        after = _get_float(op_check, "value", required=False, context=f"kpi_checks.{metric_name}")

        metrics[metric_name] = {
            "before": None,
            "after": after,
            "delta": None,
            "floor": floor,
            "before_floor_met": None,
            "after_floor_met": _bool_floor_status(after, floor),
            "source": "ops_report",
        }

    overall_after_met = all(
        metric["after_floor_met"] for metric in metrics.values() if metric["after_floor_met"] is not None
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "baseline_cross_domain": "provided",
            "latest_cross_domain": "provided",
            "latest_ops_report": "provided",
        },
        "metrics": metrics,
        "overall_after_floor_met": overall_after_met,
    }


def render_table(report: dict[str, Any]) -> str:
    header = "| Metric | Before | After | Delta | Floor | Before Floor | After Floor |"
    sep = "|---|---:|---:|---:|---:|---|---|"

    lines = [header, sep]

    for metric_name, item in report["metrics"].items():
        before = item["before"]
        after = item["after"]
        delta = item["delta"]
        floor = item["floor"]

        before_s = f"{before:.4f}" if before is not None else "N/A"
        after_s = f"{after:.4f}" if after is not None else "N/A"
        delta_s = f"{delta:+.4f}" if delta is not None else "N/A"
        floor_s = f"{floor:.4f}" if floor is not None else "N/A"

        lines.append(
            "| "
            f"{metric_name} | {before_s} | {after_s} | {delta_s} | {floor_s} | "
            f"{_status_str(item['before_floor_met'])} | {_status_str(item['after_floor_met'])} |"
        )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare REEVU KPI baseline vs latest artifacts.")
    parser.add_argument(
        "--baseline-cross-domain",
        required=True,
        help="Path to baseline cross-domain reasoning JSON",
    )
    parser.add_argument(
        "--latest-cross-domain",
        required=True,
        help="Path to latest cross-domain reasoning JSON",
    )
    parser.add_argument(
        "--latest-ops-report",
        required=True,
        help="Path to latest consolidated ops report JSON",
    )
    parser.add_argument(
        "--json-output",
        default="test_reports/reevu_kpi_delta_report.json",
        help="Path to write machine-readable delta report",
    )
    args = parser.parse_args()

    try:
        baseline = _load_json(Path(args.baseline_cross_domain))
        latest = _load_json(Path(args.latest_cross_domain))
        ops = _load_json(Path(args.latest_ops_report))
        report = build_delta_report(baseline, latest, ops)
    except ValueError as exc:
        print(f"ERROR: malformed input - {exc}")
        return 1

    output_path = Path(args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("REEVU KPI Delta Comparator")
    print(render_table(report))
    print(f"overall latest floor met: {'PASS' if report['overall_after_floor_met'] else 'FAIL'}")
    print(f"wrote JSON: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
