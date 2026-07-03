import copy
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
    "reevu_real_question_local.json": {
        "generated_at": "2099-01-01T00:00:00+00:00",
        "fixture_path": "tests/fixtures/reevu/real_question_benchmark.json",
        "runtime_path": "local",
        "runtime_target": "in_process_app",
        "runtime_status": "ready",
        "local_organization_id": 1,
        "local_organization_selection": {
            "mode": "default",
            "requested_organization_id": 1,
            "effective_organization_id": 1,
        },
        "readiness_blockers": [],
        "readiness_warnings": [],
        "runtime_readiness": {
            "organization_id": 1,
            "surface_counts": {"germplasm": 5, "trials": 5, "observations": 5, "bio_gwas_runs": 2, "bio_qtls": 2},
            "surface_examples": {"germplasm": ["IR64"], "trials": ["Ludhiana Trial"]},
            "surface_errors": {},
            "readiness_flags": [],
        },
        "total_cases": 1,
        "passed_cases": 1,
        "pass_rate": 1.0,
        "failed_cases": 0,
        "question_family_summary": {
            "by_domain_group": {"breeding": {"pass_rate": 1.0}},
            "by_cross_domain_class": {"single_domain": {"pass_rate": 1.0}},
            "by_question_family": {"breeding::single_domain": {"pass_rate": 1.0}},
        },
        "results": [],
    },
    "reevu_local_readiness_census.json": {
        "generated_at": "2099-01-01T00:00:00+00:00",
        "runtime_path": "local",
        "local_organization_selection": {
            "mode": "default",
            "requested_organization_id": 1,
            "effective_organization_id": 1,
        },
        "selected_local_organization_id": 1,
        "organizations_scanned": 1,
        "benchmark_ready_organization_ids": [1],
        "benchmark_ready_demo_organization_ids": [],
        "benchmark_ready_non_demo_organization_ids": [1],
        "blocked_organization_ids": [],
        "least_blocked_local_organization": None,
        "policy_guidance": [],
        "selected_local_organization_remediation": [],
        "organizations": [
            {
                "organization_id": 1,
                "organization_name": "IRRI Demo",
                "organization_scope": "non_demo",
                "selected": True,
                "runtime_status": "ready",
                "readiness_blockers": [],
                "readiness_warnings": [],
                "surface_counts": {"germplasm": 5, "trials": 5, "observations": 5, "bio_gwas_runs": 2, "bio_qtls": 2},
                "surface_errors": {},
                "surface_examples": {"germplasm": ["IR64"], "trials": ["Ludhiana Trial"]},
            }
        ],
    },
    "reevu_authority_gap_report.json": {
        "generated_at": "2099-01-01T00:00:00+00:00",
        "runtime_path": "local",
        "overall_gap_status": "clear",
        "selected_local_organization_id": 1,
        "local_organization_selection": {
            "mode": "default",
            "requested_organization_id": 1,
            "effective_organization_id": 1,
        },
        "organizations_scanned": 1,
        "benchmark_ready_organization_ids": [1],
        "benchmark_ready_demo_organization_ids": [],
        "benchmark_ready_non_demo_organization_ids": [1],
        "blocked_organization_ids": [],
        "common_blockers_across_blocked_orgs": [],
        "policy_guidance": [],
        "surface_gaps": [
            {
                "surface_key": "breeding_germplasm_detail",
                "surface_label": "Breeding germplasm detail",
                "trust_status": "trusted",
                "benchmark_ids": ["rq-01"],
                "failed_benchmark_ids": [],
                "failed_checks": [],
                "question_families": ["breeding::single_domain"],
                "expected_functions": ["get_germplasm_details"],
                "total_cases": 1,
                "failed_cases": 0,
                "pass_rate": 1.0,
                "passed_benchmark_ids": ["rq-01"],
                "selected_local_org_status": "ready",
                "selected_local_org_blockers": [],
                "selected_local_org_warnings": [],
                "safe_failure_sources": [],
                "safe_failure_error_categories": [],
                "failed_case_details": [],
                "common_blockers_across_blocked_orgs": [],
                "benchmark_ready_local_org_count": 1,
                "benchmark_ready_organization_ids": [1],
                "gap_status": "clear",
            }
        ],
    },
    "reevu_real_question_managed.json": {
        "generated_at": "2099-01-01T00:00:00+00:00",
        "fixture_path": "tests/fixtures/reevu/real_question_benchmark.json",
        "runtime_path": "managed",
        "runtime_target": "https://reevu.example.com",
        "runtime_status": "evaluated",
        "total_cases": 1,
        "passed_cases": 1,
        "pass_rate": 1.0,
        "failed_cases": 0,
        "question_family_summary": {
            "by_domain_group": {"breeding": {"pass_rate": 1.0}},
            "by_cross_domain_class": {"single_domain": {"pass_rate": 1.0}},
            "by_question_family": {"breeding::single_domain": {"pass_rate": 1.0}},
        },
        "results": [],
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
        "runtime_readiness": {
            "local": {
                "artifact_present": True,
                "pass_rate": 1.0,
                "readiness_blockers": [],
                "readiness_warnings": [],
                "benchmark_ready_organization_ids": [1],
                "benchmark_ready_demo_organization_ids": [],
                "benchmark_ready_non_demo_organization_ids": [1],
                "policy_guidance": [],
                "selected_local_organization_remediation": [],
                "common_blockers_across_blocked_orgs": [],
                "least_blocked_local_organization": None,
            },
            "managed": {
                "artifact_present": True,
                "pass_rate": 1.0,
                "readiness_blockers": [],
                "readiness_warnings": [],
            },
        },
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


def test_validate_artifacts_detects_missing_runtime_path_artifact(tmp_path):
    _write_all(tmp_path)
    (tmp_path / "reevu_real_question_managed.json").unlink()

    ok, violations, _ = validate_artifacts(tmp_path)

    assert ok is False
    assert "missing required artifact: reevu_real_question_managed.json" in violations


def test_validate_artifacts_detects_malformed_ops_runtime_readiness(tmp_path):
    _write_all(tmp_path)
    malformed = copy.deepcopy(MIN_VALID_ARTIFACTS["reevu_ops_report.json"])
    malformed["runtime_readiness"]["local"]["artifact_present"] = "yes"
    (tmp_path / "reevu_ops_report.json").write_text(
        json.dumps(malformed), encoding="utf-8"
    )

    ok, violations, _ = validate_artifacts(tmp_path)

    assert ok is False
    assert any(
        "runtime_readiness.local.artifact_present" in violation
        for violation in violations
    )


def test_validate_artifacts_allows_local_only_runtime_mode(tmp_path):
    _write_all(tmp_path)
    (tmp_path / "reevu_real_question_managed.json").unlink()

    ok, violations, _ = validate_artifacts(tmp_path, required_runtime_paths=("local",))

    assert ok is True
    assert violations == []


def test_validate_artifacts_requires_local_readiness_census_for_local_mode(tmp_path):
    _write_all(tmp_path)
    (tmp_path / "reevu_real_question_managed.json").unlink()
    (tmp_path / "reevu_local_readiness_census.json").unlink()

    ok, violations, _ = validate_artifacts(tmp_path, required_runtime_paths=("local",))

    assert ok is False
    assert "missing required artifact: reevu_local_readiness_census.json" in violations


def test_validate_artifacts_requires_authority_gap_report_for_local_mode(tmp_path):
    _write_all(tmp_path)
    (tmp_path / "reevu_real_question_managed.json").unlink()
    (tmp_path / "reevu_authority_gap_report.json").unlink()

    ok, violations, _ = validate_artifacts(tmp_path, required_runtime_paths=("local",))

    assert ok is False
    assert "missing required artifact: reevu_authority_gap_report.json" in violations


def test_validate_artifacts_detects_invalid_local_runtime_status(tmp_path):
    _write_all(tmp_path)
    malformed = MIN_VALID_ARTIFACTS["reevu_real_question_local.json"].copy()
    malformed["runtime_status"] = "evaluated"
    (tmp_path / "reevu_real_question_local.json").write_text(
        json.dumps(malformed), encoding="utf-8"
    )

    ok, violations, _ = validate_artifacts(tmp_path, required_runtime_paths=("local",))

    assert ok is False
    assert any("runtime_status" in violation for violation in violations)


def test_validate_artifacts_detects_inconsistent_local_ready_ids(tmp_path):
    _write_all(tmp_path)
    malformed = copy.deepcopy(MIN_VALID_ARTIFACTS["reevu_local_readiness_census.json"])
    malformed["benchmark_ready_organization_ids"] = []
    (tmp_path / "reevu_real_question_managed.json").unlink()
    (tmp_path / "reevu_local_readiness_census.json").write_text(
        json.dumps(malformed), encoding="utf-8"
    )

    ok, violations, _ = validate_artifacts(tmp_path, required_runtime_paths=("local",))

    assert ok is False
    assert any("benchmark_ready_organization_ids" in violation for violation in violations)


def test_validate_artifacts_detects_stale_gap_status_when_ready_org_exists(tmp_path):
    _write_all(tmp_path)
    malformed = copy.deepcopy(MIN_VALID_ARTIFACTS["reevu_authority_gap_report.json"])
    malformed["overall_gap_status"] = "no_benchmark_ready_local_org"
    malformed["benchmark_ready_organization_ids"] = [1]
    (tmp_path / "reevu_real_question_managed.json").unlink()
    (tmp_path / "reevu_authority_gap_report.json").write_text(
        json.dumps(malformed), encoding="utf-8"
    )

    ok, violations, _ = validate_artifacts(tmp_path, required_runtime_paths=("local",))

    assert ok is False
    assert any("overall_gap_status" in violation for violation in violations)


def test_validate_artifacts_detects_stale_default_census_against_supplementary_ready_lane(tmp_path):
    _write_all(tmp_path)
    default_census = {
        "generated_at": "2099-01-01T00:00:00+00:00",
        "runtime_path": "local",
        "local_organization_selection": {
            "mode": "default",
            "requested_organization_id": 1,
            "effective_organization_id": 1,
        },
        "selected_local_organization_id": 1,
        "organizations_scanned": 2,
        "benchmark_ready_organization_ids": [],
        "benchmark_ready_demo_organization_ids": [],
        "benchmark_ready_non_demo_organization_ids": [],
        "blocked_organization_ids": [1, 2],
        "policy_guidance": [],
        "selected_local_organization_remediation": [
            "observations.empty: Provision authoritative observations"
        ],
        "least_blocked_local_organization": {
            "organization_id": 2,
            "organization_name": "Demo Organization",
            "organization_scope": "demo_dataset",
            "selected": False,
            "runtime_status": "blocked",
            "readiness_blockers": ["bio_gwas_runs.empty"],
            "readiness_warnings": [],
        },
        "organizations": [
            {
                "organization_id": 1,
                "organization_name": "Default Organization",
                "organization_scope": "non_demo",
                "selected": True,
                "runtime_status": "blocked",
                "readiness_blockers": ["observations.empty"],
                "readiness_warnings": [],
            },
            {
                "organization_id": 2,
                "organization_name": "Demo Organization",
                "organization_scope": "demo_dataset",
                "selected": False,
                "runtime_status": "blocked",
                "readiness_blockers": ["bio_gwas_runs.empty"],
                "readiness_warnings": [],
            },
        ],
    }
    supplementary_census = {
        "generated_at": "2099-01-01T00:00:00+00:00",
        "runtime_path": "local",
        "local_organization_selection": {
            "mode": "cli",
            "requested_organization_id": 2,
            "effective_organization_id": 2,
        },
        "selected_local_organization_id": 2,
        "organizations_scanned": 2,
        "benchmark_ready_organization_ids": [2],
        "benchmark_ready_demo_organization_ids": [2],
        "benchmark_ready_non_demo_organization_ids": [],
        "blocked_organization_ids": [1],
        "policy_guidance": [],
        "selected_local_organization_remediation": [],
        "least_blocked_local_organization": None,
        "organizations": [
            {
                "organization_id": 1,
                "organization_name": "Default Organization",
                "organization_scope": "non_demo",
                "selected": False,
                "runtime_status": "blocked",
                "readiness_blockers": ["observations.empty"],
                "readiness_warnings": [],
            },
            {
                "organization_id": 2,
                "organization_name": "Demo Organization",
                "organization_scope": "demo_dataset",
                "selected": True,
                "runtime_status": "ready",
                "readiness_blockers": [],
                "readiness_warnings": [],
            },
        ],
    }

    (tmp_path / "reevu_real_question_managed.json").unlink()
    (tmp_path / "reevu_local_readiness_census.json").write_text(
        json.dumps(default_census), encoding="utf-8"
    )
    (tmp_path / "reevu_local_readiness_census_org2.json").write_text(
        json.dumps(supplementary_census), encoding="utf-8"
    )

    ok, violations, _ = validate_artifacts(tmp_path, required_runtime_paths=("local",))

    assert ok is False
    assert any("supplementary readiness artifacts" in violation for violation in violations)
