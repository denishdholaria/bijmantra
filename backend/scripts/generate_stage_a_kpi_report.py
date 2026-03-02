"""Generate a compact Stage A KPI rollup from REEVU baseline artifacts.

This script consolidates Stage A readiness signals into one JSON report for
quick review and handoff:
- top-intent routing precision baseline
- trace completeness baseline
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bool(v: Any) -> bool:
    return bool(v)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate REEVU Stage A KPI rollup report.")
    parser.add_argument(
        "--top-intent",
        default="test_reports/reevu_top_intent_routing_baseline.json",
        help="Path to top-intent baseline JSON",
    )
    parser.add_argument(
        "--trace",
        default="test_reports/reevu_trace_completeness_baseline.json",
        help="Path to trace completeness baseline JSON",
    )
    parser.add_argument(
        "--json-output",
        default="test_reports/reevu_stage_a_kpi_report.json",
        help="Path to write Stage A KPI rollup JSON",
    )
    parser.add_argument(
        "--intent-floor",
        type=float,
        default=0.92,
        help="Tool-call precision floor from roadmap",
    )
    parser.add_argument(
        "--trace-floor",
        type=float,
        default=0.99,
        help="Trace completeness floor from roadmap",
    )
    args = parser.parse_args()

    top_intent = _load_json(Path(args.top_intent))
    trace = _load_json(Path(args.trace))

    intent_precision = float(top_intent.get("actionable_function_precision", 0.0))
    trace_completeness = float(trace.get("trace_completeness_rate", 0.0))

    intent_meets_floor = intent_precision >= args.intent_floor
    trace_meets_floor = trace_completeness >= args.trace_floor

    report = {
        "stage": "A",
        "kpi_targets": {
            "tool_call_precision_floor": args.intent_floor,
            "trace_completeness_floor": args.trace_floor,
        },
        "kpi_values": {
            "tool_call_precision": intent_precision,
            "trace_completeness": trace_completeness,
        },
        "status": {
            "tool_call_precision_meets_floor": intent_meets_floor,
            "trace_completeness_meets_floor": trace_meets_floor,
            "stage_a_kpi_floor_met": _bool(intent_meets_floor and trace_meets_floor),
        },
        "sources": {
            "top_intent": str(Path(args.top_intent)),
            "trace": str(Path(args.trace)),
        },
    }

    output_path = Path(args.json_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("REEVU Stage A KPI Report")
    print(f"- tool-call precision: {intent_precision:.2%} (floor {args.intent_floor:.2%})")
    print(f"- trace completeness: {trace_completeness:.2%} (floor {args.trace_floor:.2%})")
    print(f"- stage floor met: {report['status']['stage_a_kpi_floor_met']}")
    print(f"- wrote json summary: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
