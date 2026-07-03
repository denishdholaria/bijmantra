import json

from scripts.generate_reevu_ops_report import build_report, generate_markdown


def _write_json(tmp_path, name, payload):
    (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")


def _write_minimum_baselines(tmp_path):
    _write_json(
        tmp_path,
        "reevu_trace_completeness_baseline.json",
        {"trace_completeness_rate": 1.0},
    )
    _write_json(
        tmp_path,
        "reevu_top_intent_routing_baseline.json",
        {"actionable_function_precision": 1.0},
    )
    _write_json(
        tmp_path,
        "reevu_stage_a_kpi_report.json",
        {"stage": "A", "kpi_targets": {}, "kpi_values": {}, "status": "ok", "sources": {}},
    )
    _write_json(
        tmp_path,
        "reevu_cross_domain_reasoning_baseline.json",
        {
            "domain_detection_accuracy": 1.0,
            "compound_classification_accuracy": 1.0,
            "step_adequacy_rate": 1.0,
        },
    )


def test_build_report_includes_local_runtime_readiness(tmp_path):
    _write_minimum_baselines(tmp_path)
    _write_json(
        tmp_path,
        "reevu_real_question_local.json",
        {
            "runtime_path": "local",
            "runtime_target": "in_process_app",
            "runtime_status": "blocked",
            "local_organization_id": 1,
            "readiness_blockers": ["observations.empty"],
            "readiness_warnings": ["trials.sparse"],
            "pass_rate": 3 / 14,
            "passed_cases": 3,
            "failed_cases": 11,
            "total_cases": 14,
        },
    )
    _write_json(
        tmp_path,
        "reevu_local_readiness_census.json",
        {
            "selected_local_organization_id": 1,
            "benchmark_ready_organization_ids": [2],
            "benchmark_ready_demo_organization_ids": [2],
            "benchmark_ready_non_demo_organization_ids": [],
            "policy_guidance": [
                "The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1."
            ],
            "selected_local_organization_remediation": [
                "observations.empty: Import authoritative observations.",
            ],
            "least_blocked_local_organization": {
                "organization_id": 2,
                "organization_name": "Demo Organization",
                "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"],
            },
        },
    )
    _write_json(
        tmp_path,
        "reevu_authority_gap_report.json",
        {
            "overall_gap_status": "no_benchmark_ready_local_org",
            "selected_local_organization_id": 1,
            "benchmark_ready_organization_ids": [2],
            "common_blockers_across_blocked_orgs": ["observations.empty"],
            "policy_guidance": ["authority-gap policy guidance"],
            "selected_local_organization_remediation": ["authority-gap remediation"],
        },
    )

    report = build_report(tmp_path)

    local_runtime = report["runtime_readiness"]["local"]
    assert local_runtime["artifact_present"] is True
    assert local_runtime["runtime_status"] == "blocked"
    assert local_runtime["selected_local_organization_id"] == 1
    assert local_runtime["benchmark_ready_organization_ids"] == [2]
    assert local_runtime["policy_guidance"] == [
        "The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1."
    ]
    assert local_runtime["selected_local_organization_remediation"] == [
        "observations.empty: Import authoritative observations.",
    ]
    assert local_runtime["least_blocked_local_organization"] == {
        "organization_id": 2,
        "organization_name": "Demo Organization",
        "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"],
    }
    assert local_runtime["authority_gap_status"] == "no_benchmark_ready_local_org"
    assert local_runtime["common_blockers_across_blocked_orgs"] == ["observations.empty"]
    assert report["runtime_readiness"]["managed"]["artifact_present"] is False


def test_generate_markdown_renders_runtime_readiness_guidance():
    markdown = generate_markdown(
        {
            "generated_at": "2026-04-05T00:00:00+00:00",
            "stages_evaluated": ["A", "C"],
            "kpi_checks": {
                "trace_completeness": {"value": 1.0, "floor": 0.99, "met": True},
                "tool_call_precision": {"value": 1.0, "floor": 0.92, "met": True},
                "domain_detection_accuracy": {"value": 1.0, "floor": 0.85, "met": True},
                "compound_classification": {"value": 1.0, "floor": 0.80, "met": True},
                "step_adequacy": {"value": 1.0, "floor": 0.85, "met": True},
            },
            "overall_floor_met": True,
            "runtime_readiness": {
                "local": {
                    "artifact_present": True,
                    "runtime_status": "blocked",
                    "selected_local_organization_id": 1,
                    "pass_rate": 3 / 14,
                    "passed_cases": 3,
                    "failed_cases": 11,
                    "total_cases": 14,
                    "authority_gap_status": "no_benchmark_ready_local_org",
                    "benchmark_ready_organization_ids": [2],
                    "readiness_blockers": ["observations.empty"],
                    "readiness_warnings": ["trials.sparse"],
                    "common_blockers_across_blocked_orgs": ["observations.empty"],
                    "policy_guidance": [
                        "Do not mirror demo-seeded benchmark data into non-demo organization 1."
                    ],
                    "selected_local_organization_remediation": [
                        "observations.empty: Import authoritative observations."
                    ],
                    "least_blocked_local_organization": {
                        "organization_id": 2,
                        "organization_name": "Demo Organization",
                        "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.empty"],
                    },
                },
                "managed": {"artifact_present": False},
            },
            "sources": {},
            "calibration_status": {},
        }
    )

    assert "## Runtime Readiness" in markdown
    assert "### Local Runtime" in markdown
    assert "**Authority-gap status:** `no_benchmark_ready_local_org`" in markdown
    assert "**Least-blocked local org:** 2 (Demo Organization) — blockers: bio_gwas_runs.empty, bio_qtls.empty" in markdown
    assert "### Local Selection Guidance" in markdown
    assert "- Do not mirror demo-seeded benchmark data into non-demo organization 1." in markdown
    assert "### Local Remediation Guidance" in markdown
    assert "- observations.empty: Import authoritative observations." in markdown
    assert "### Managed Runtime" in markdown
    assert "Managed runtime artifact not present." in markdown