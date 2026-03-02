import json
import os

from scripts.validate_reevu_artifacts import validate_artifacts


MIN_VALID_ARTIFACTS = {
    "reevu_trace_completeness_baseline.json": {
        "total_cases": 1,
        "complete_cases": 1,
        "trace_completeness_rate": 1.0,
        "kpi_floor": 0.99,
        "meets_floor": True,
    },
    "reevu_top_intent_routing_baseline.json": {
        "total_cases": 1,
        "function_exact_match_rate": 1.0,
        "actionable_function_precision": 1.0,
        "param_subset_match_rate_when_function_matches": 1.0,
    },
    "reevu_stage_a_kpi_report.json": {
        "stage": "A",
        "kpi_targets": {
            "tool_call_precision_floor": 0.92,
            "trace_completeness_floor": 0.99,
        },
        "kpi_values": {"tool_call_precision": 1.0, "trace_completeness": 1.0},
        "status": {"stage_a_kpi_floor_met": True},
        "sources": {"top_intent": "x", "trace": "y"},
    },
    "reevu_cross_domain_reasoning_baseline.json": {
        "total_prompts": 1,
        "domain_detection_accuracy": 1.0,
        "compound_classification_accuracy": 1.0,
        "step_adequacy_rate": 1.0,
    },
    "reevu_ops_report.json": {
        "generated_at": "2099-01-01T00:00:00+00:00",
        "stages_evaluated": ["A", "C"],
        "kpi_checks": {
            "trace_completeness": {"value": 1.0, "floor": 0.99},
            "tool_call_precision": {"value": 1.0, "floor": 0.92},
            "domain_detection_accuracy": {"value": 1.0, "floor": 0.85},
            "compound_classification": {"value": 1.0, "floor": 0.8},
            "step_adequacy": {"value": 1.0, "floor": 0.85},
        },
        "overall_floor_met": True,
        "sources": {},
    },
}


def _write_all(base):
    for filename, payload in MIN_VALID_ARTIFACTS.items():
        (base / filename).write_text(json.dumps(payload), encoding="utf-8")
    ops_path = base / "reevu_ops_report.json"
    stat = ops_path.stat()
    os.utime(ops_path, (stat.st_atime, stat.st_mtime + 5))


def test_validate_artifacts_success(tmp_path):
    _write_all(tmp_path)

    ok, violations, _ = validate_artifacts(tmp_path)

    assert ok is True
    assert violations == []


def test_validate_artifacts_detects_malformed_kpi(tmp_path):
    _write_all(tmp_path)
    malformed = MIN_VALID_ARTIFACTS["reevu_cross_domain_reasoning_baseline.json"].copy()
    malformed["domain_detection_accuracy"] = 1.2
    (tmp_path / "reevu_cross_domain_reasoning_baseline.json").write_text(
        json.dumps(malformed), encoding="utf-8"
    )

    ok, violations, _ = validate_artifacts(tmp_path)

    assert ok is False
    assert any("domain_detection_accuracy" in violation for violation in violations)
