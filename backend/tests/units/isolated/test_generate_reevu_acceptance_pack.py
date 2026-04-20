from scripts.generate_reevu_acceptance_pack import (
    _build_authority_gap_summary,
    _build_gate_commands,
    _build_local_readiness_census_summary,
    _build_managed_runtime_preflight,
    _generate_markdown,
    _build_real_question_readiness,
    _collect_acceptance_blockers,
    _resolve_gate_python_command,
)


def test_build_gate_commands_can_use_explicit_python_command():
    commands, runtime_paths = _build_gate_commands(
        managed_base_url=None,
        managed_auth_token=None,
        python_command="/tmp/backend/venv/bin/python",
    )

    assert runtime_paths == ["local"]
    assert commands[0] == "/tmp/backend/venv/bin/python -m pytest tests/units/api/v2 -q"
    assert commands[3] == "/tmp/backend/venv/bin/python scripts/eval_cross_domain_reasoning.py"
    assert commands[-1] == "/tmp/backend/venv/bin/python scripts/validate_reevu_artifacts.py --required-runtime-paths local"


def test_resolve_gate_python_command_prefers_active_virtualenv(monkeypatch, tmp_path):
    fake_python = tmp_path / "venv" / "bin" / "python"
    fake_python.parent.mkdir(parents=True)
    fake_python.write_text("", encoding="utf-8")

    monkeypatch.setattr("scripts.generate_reevu_acceptance_pack.sys.executable", str(fake_python))
    monkeypatch.setattr("scripts.generate_reevu_acceptance_pack.sys.prefix", str(tmp_path / "venv"))
    monkeypatch.setattr("scripts.generate_reevu_acceptance_pack.sys.base_prefix", "/usr/local")

    assert _resolve_gate_python_command() == str(fake_python)


def test_build_real_question_readiness_preserves_local_status_metadata(tmp_path):
    (tmp_path / "reevu_real_question_local.json").write_text(
        """
        {
          "runtime_target": "in_process_app",
          "runtime_status": "blocked",
          "local_organization_id": 7,
          "readiness_blockers": ["observations.empty"],
          "readiness_warnings": ["germplasm.sparse"],
          "pass_rate": 0.0,
          "passed_cases": 0,
          "failed_cases": 0,
          "total_cases": 0
        }
        """,
        encoding="utf-8",
    )

    readiness = _build_real_question_readiness(tmp_path, required_runtime_paths=["local"])

    assert readiness["local"]["runtime_status"] == "blocked"
    assert readiness["local"]["local_organization_id"] == 7
    assert readiness["local"]["readiness_blockers"] == ["observations.empty"]
    assert readiness["local"]["readiness_warnings"] == ["germplasm.sparse"]


def test_build_managed_runtime_preflight_requires_explicit_configuration_even_if_artifact_exists(tmp_path):
    (tmp_path / "reevu_real_question_managed.json").write_text(
        """
        {
          "runtime_target": "https://reevu.example.com",
          "runtime_status": "evaluated"
        }
        """,
        encoding="utf-8",
    )

    preflight = _build_managed_runtime_preflight(
        tmp_path,
        managed_base_url=None,
        managed_auth_token=None,
        gate_outcomes=[],
    )

    assert preflight["status"] == "pending_configuration"
    assert preflight["counts_toward_final_acceptance"] is False
    assert preflight["managed_artifact_present"] is True
    assert any("not counted" in note for note in preflight["notes"])


def test_build_managed_runtime_preflight_accepts_matching_evaluated_artifact(tmp_path):
    (tmp_path / "reevu_real_question_managed.json").write_text(
        """
        {
          "runtime_target": "https://reevu.example.com",
          "runtime_status": "evaluated"
        }
        """,
        encoding="utf-8",
    )

    preflight = _build_managed_runtime_preflight(
        tmp_path,
        managed_base_url="https://reevu.example.com",
        managed_auth_token="token123",
        gate_outcomes=[],
    )

    assert preflight["status"] == "evaluated"
    assert preflight["counts_toward_final_acceptance"] is True
    assert preflight["managed_artifact_target"] == "https://reevu.example.com"


def test_collect_acceptance_blockers_prefers_blocked_runtime_over_generic_failures():
    blockers = _collect_acceptance_blockers(
        gate_outcomes=[
            {
                "command": "venv/bin/python scripts/eval_real_question_benchmark.py --runtime-path local --json-output test_reports/reevu_real_question_local.json --local-readiness-census-output test_reports/reevu_local_readiness_census.json --fail-on-failed-cases",
                "status": "failed",
            }
        ],
        artifact_status={"all_valid": True},
        real_question_readiness={
            "local": {
                "present": True,
                "runtime_status": "blocked",
                "local_organization_id": 7,
                "readiness_blockers": ["observations.empty", "bio_qtls.missing_or_inaccessible"],
                "failed_cases": 11,
            }
        },
        local_readiness_census={"present": False},
    )

    assert blockers == [
        "Local runtime path is not benchmark-ready for organization 7: observations.empty, bio_qtls.missing_or_inaccessible."
    ]


def test_collect_acceptance_blockers_keeps_generic_gate_failure_for_unexplained_command():
    blockers = _collect_acceptance_blockers(
        gate_outcomes=[
            {
                "command": "venv/bin/python scripts/eval_cross_domain_reasoning.py",
                "status": "failed",
            }
        ],
        artifact_status={"all_valid": True},
        real_question_readiness={
            "local": {
                "present": True,
                "runtime_status": "ready",
                "local_organization_id": 2,
                "readiness_blockers": [],
                "failed_cases": 0,
            }
        },
        local_readiness_census={"present": True},
    )

    assert blockers == [
        "One or more gate commands failed."
    ]


def test_collect_acceptance_blockers_requires_managed_runtime_evidence_for_final_acceptance():
    blockers = _collect_acceptance_blockers(
        gate_outcomes=[],
        artifact_status={"all_valid": True},
        real_question_readiness={},
        local_readiness_census={"present": False},
        managed_runtime_preflight={
            "status": "pending_configuration",
            "managed_base_url": None,
            "managed_artifact_target": None,
        },
    )

    assert blockers == [
        "Managed runtime evaluation is pending configuration: supply a managed base URL and rerun the managed real-question benchmark before final acceptance."
    ]


def test_collect_acceptance_blockers_reports_when_no_ready_local_org_exists():
    blockers = _collect_acceptance_blockers(
        gate_outcomes=[],
        artifact_status={"all_valid": True},
        real_question_readiness={
            "local": {
                "present": True,
                "runtime_status": "blocked",
                "local_organization_id": 7,
                "readiness_blockers": ["observations.empty"],
                "failed_cases": 11,
            }
        },
        local_readiness_census={
            "present": True,
            "ready_candidates": [],
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

    assert blockers == [
        "No benchmark-ready local organizations were discovered. Selected organization 7 is blocked: observations.empty. Least-blocked local organization is 2 (Demo Organization): bio_gwas_runs.empty, bio_qtls.missing_or_inaccessible. Recommended remediation: observations.empty: Import authoritative observations."
    ]


def test_collect_acceptance_blockers_adds_demo_dataset_policy_guidance_for_demo_ready_candidate():
    blockers = _collect_acceptance_blockers(
        gate_outcomes=[],
        artifact_status={"all_valid": True},
        real_question_readiness={
            "local": {
                "present": True,
                "runtime_status": "blocked",
                "local_organization_id": 1,
                "readiness_blockers": ["observations.empty", "bio_gwas_runs.empty", "bio_qtls.empty"],
                "failed_cases": 11,
            }
        },
        local_readiness_census={
            "present": True,
            "ready_candidates": [
                {
                    "organization_id": 2,
                    "organization_name": "Demo Organization",
                    "organization_scope": "demo_dataset",
                }
            ],
            "policy_guidance": [
                "The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1 (Default Organization)."
            ],
            "selected_local_organization_remediation": [
                "observations.empty: Provision authoritative observations via /api/v2/import/upload with import_type=observation.",
                "bio_qtls.empty: Provision authoritative BioQTL rows via /api/v2/import/upload with import_type=qtl.",
            ],
            "least_blocked_local_organization": None,
        },
    )

    assert blockers == [
        "Selected local runtime organization 1 is not benchmark-ready: observations.empty, bio_gwas_runs.empty, bio_qtls.empty. Benchmark-ready local organizations discovered: 2 (Demo Organization), demo dataset. The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1 (Default Organization). Recommended remediation: observations.empty: Provision authoritative observations via /api/v2/import/upload with import_type=observation. bio_qtls.empty: Provision authoritative BioQTL rows via /api/v2/import/upload with import_type=qtl."
    ]


def test_build_local_readiness_census_summary_extracts_ready_candidates(tmp_path):
    (tmp_path / "reevu_local_readiness_census.json").write_text(
        """
        {
          "local_organization_selection": {"mode": "default", "requested_organization_id": 1, "effective_organization_id": 1},
          "selected_local_organization_id": 1,
          "organizations_scanned": 2,
          "benchmark_ready_organization_ids": [2],
                    "benchmark_ready_demo_organization_ids": [2],
                    "benchmark_ready_non_demo_organization_ids": [],
          "blocked_organization_ids": [1],
                    "policy_guidance": ["Demo guidance"],
                    "selected_local_organization_remediation": ["observations.empty: Import observations"],
          "organizations": [
                        {"organization_id": 1, "organization_name": "Blocked Org", "organization_scope": "non_demo", "selected": true, "runtime_status": "blocked", "readiness_blockers": ["observations.empty"], "readiness_warnings": []},
                        {"organization_id": 2, "organization_name": "Ready Org", "organization_scope": "demo_dataset", "selected": false, "runtime_status": "ready", "readiness_blockers": [], "readiness_warnings": []}
          ]
        }
        """,
        encoding="utf-8",
    )

    summary = _build_local_readiness_census_summary(tmp_path)

    assert summary["present"] is True
    assert summary["selection_mode"] == "default"
    assert summary["selected_local_organization_scope"] == "non_demo"
    assert summary["selected_local_organization_runtime_status"] == "blocked"
    assert summary["benchmark_ready_demo_organization_ids"] == [2]
    assert summary["benchmark_ready_non_demo_organization_ids"] == []
    assert summary["policy_guidance"] == ["Demo guidance"]
    assert summary["selected_local_organization_remediation"] == [
        "observations.empty: Import observations"
    ]
    assert summary["ready_candidates"] == [
        {
            "organization_id": 2,
            "organization_name": "Ready Org",
            "organization_scope": "demo_dataset",
        }
    ]
    assert summary["least_blocked_local_organization"] is None


def test_build_local_readiness_census_summary_extracts_least_blocked_local_org(tmp_path):
    (tmp_path / "reevu_local_readiness_census.json").write_text(
        """
        {
          "local_organization_selection": {"mode": "default", "requested_organization_id": 1, "effective_organization_id": 1},
          "selected_local_organization_id": 1,
          "organizations_scanned": 2,
          "benchmark_ready_organization_ids": [],
                    "benchmark_ready_demo_organization_ids": [],
                    "benchmark_ready_non_demo_organization_ids": [],
          "blocked_organization_ids": [1, 2],
                    "policy_guidance": [],
          "least_blocked_local_organization": {
            "organization_id": 2,
            "organization_name": "Demo Organization",
                        "organization_scope": "demo_dataset",
            "selected": false,
            "runtime_status": "blocked",
            "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"],
            "readiness_warnings": ["trials.sparse"],
            "benchmark_relevant_surface_count": 30
          },
          "organizations": [
                        {"organization_id": 1, "organization_name": "Blocked Org", "organization_scope": "non_demo", "selected": true, "runtime_status": "blocked", "readiness_blockers": ["observations.empty"], "readiness_warnings": []},
                        {"organization_id": 2, "organization_name": "Demo Organization", "organization_scope": "demo_dataset", "selected": false, "runtime_status": "blocked", "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"], "readiness_warnings": ["trials.sparse"]}
          ]
        }
        """,
        encoding="utf-8",
    )

    summary = _build_local_readiness_census_summary(tmp_path)

    assert summary["least_blocked_local_organization"] == {
        "organization_id": 2,
        "organization_name": "Demo Organization",
        "organization_scope": "demo_dataset",
        "selected": False,
        "runtime_status": "blocked",
        "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"],
        "readiness_warnings": ["trials.sparse"],
        "benchmark_relevant_surface_count": 30,
    }


def test_build_authority_gap_summary_extracts_surface_rows(tmp_path):
    (tmp_path / "reevu_authority_gap_report.json").write_text(
        """
        {
            "overall_gap_status": "no_benchmark_ready_local_org",
            "selected_local_organization_id": 1,
            "organizations_scanned": 2,
            "benchmark_ready_organization_ids": [],
            "benchmark_ready_demo_organization_ids": [],
            "benchmark_ready_non_demo_organization_ids": [],
            "common_blockers_across_blocked_orgs": ["observations.empty"],
            "policy_guidance": ["Demo guidance"],
            "selected_local_organization_remediation": ["observations.empty: Import observations"],
            "least_blocked_local_organization": {
                "organization_id": 2,
                "organization_name": "Demo Organization",
                "readiness_blockers": ["bio_gwas_runs.empty"]
            },
            "surface_gaps": [
                {
                    "surface_label": "Breeding germplasm detail",
                    "trust_status": "trusted",
                    "failed_cases": 1,
                    "total_cases": 1,
                    "gap_status": "blocked_no_benchmark_ready_local_org",
                    "common_blockers_across_blocked_orgs": ["observations.empty"],
                    "safe_failure_sources": ["function_result"],
                    "failed_case_details": [
                        {
                            "benchmark_id": "rq-01",
                            "safe_failure_source": "function_result",
                            "safe_failure_error_category": "insufficient_retrieval_scope",
                            "safe_failure_missing": ["specific germplasm identifier"],
                            "safe_failure_searched": ["germplasm_lookup"]
                        }
                    ]
                }
            ]
        }
        """,
        encoding="utf-8",
    )

    summary = _build_authority_gap_summary(tmp_path)

    assert summary["present"] is True
    assert summary["overall_gap_status"] == "no_benchmark_ready_local_org"
    assert summary["policy_guidance"] == ["Demo guidance"]
    assert summary["selected_local_organization_remediation"] == [
        "observations.empty: Import observations"
    ]
    assert summary["least_blocked_local_organization"] == {
        "organization_id": 2,
        "organization_name": "Demo Organization",
        "readiness_blockers": ["bio_gwas_runs.empty"],
    }
    assert summary["surface_gaps"][0]["surface_label"] == "Breeding germplasm detail"
    assert summary["surface_gaps"][0]["failed_case_details"][0]["benchmark_id"] == "rq-01"


def test_generate_markdown_renders_skipped_gate_outcomes_truthfully():
    markdown = _generate_markdown(
        {
            "generated_at_utc": "2026-03-31T00:00:00+00:00",
            "commit_hash": "abc123",
            "overall_status": "blocked",
            "gate_outcomes": [
                {
                    "command": "uv run pytest tests/units/api/v2 -q",
                    "status": "skipped",
                    "duration_seconds": 0,
                    "return_code": None,
                }
            ],
            "kpi_deltas": {"metrics": {}},
            "real_question_readiness": {},
            "artifact_integrity": {"all_valid": True, "artifacts": {}},
            "blockers": [],
        }
    )

    assert "| `uv run pytest tests/units/api/v2 -q` | ⏭ skipped | 0 | N/A |" in markdown


def test_generate_markdown_renders_managed_runtime_preflight_section():
    markdown = _generate_markdown(
        {
            "generated_at_utc": "2026-03-31T00:00:00+00:00",
            "commit_hash": "abc123",
            "overall_status": "blocked",
            "gate_outcomes": [],
            "kpi_deltas": {"metrics": {}},
            "real_question_readiness": {},
            "managed_runtime_preflight": {
                "status": "pending_configuration",
                "counts_toward_final_acceptance": False,
                "managed_base_url": None,
                "managed_auth_token_supplied": False,
                "managed_gate_status": "not_requested",
                "managed_artifact_present": False,
                "managed_artifact_target": None,
                "managed_artifact_runtime_status": None,
                "summary": "Managed runtime evaluation is pending configuration because no managed base URL was supplied for this acceptance run.",
                "notes": [],
            },
            "artifact_integrity": {"all_valid": True, "artifacts": {}},
            "blockers": [],
        }
    )

    assert "## Managed Runtime Preflight" in markdown
    assert "**Status:** `pending_configuration`" in markdown
    assert "Managed runtime evaluation is pending configuration because no managed base URL was supplied for this acceptance run." in markdown


def test_generate_markdown_renders_least_blocked_local_org():
    markdown = _generate_markdown(
        {
            "generated_at_utc": "2026-04-02T00:00:00+00:00",
            "commit_hash": "abc123",
            "overall_status": "blocked",
            "gate_outcomes": [],
            "kpi_deltas": {"metrics": {}},
            "real_question_readiness": {},
            "local_readiness_census": {
                "present": True,
                "selection_mode": "default",
                "selected_local_organization_id": 1,
                "organizations_scanned": 2,
                "ready_candidates": [],
                "least_blocked_local_organization": {
                    "organization_id": 2,
                    "organization_name": "Demo Organization",
                    "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"],
                },
                "organizations": [],
            },
            "artifact_integrity": {"all_valid": True, "artifacts": {}},
            "blockers": [],
        }
    )

    assert "**Least-blocked local org:** 2 (Demo Organization) — blockers: bio_gwas_runs.empty, bio_qtls.missing_or_inaccessible" in markdown


def test_generate_markdown_renders_local_selection_guidance():
    markdown = _generate_markdown(
        {
            "generated_at_utc": "2026-04-03T00:00:00+00:00",
            "commit_hash": "abc123",
            "overall_status": "blocked",
            "gate_outcomes": [],
            "kpi_deltas": {"metrics": {}},
            "real_question_readiness": {},
            "local_readiness_census": {
                "present": True,
                "selection_mode": "default",
                "selected_local_organization_id": 1,
                "organizations_scanned": 2,
                "ready_candidates": [
                    {
                        "organization_id": 2,
                        "organization_name": "Demo Organization",
                        "organization_scope": "demo_dataset",
                    }
                ],
                "policy_guidance": [
                    "The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1 (Default Organization)."
                ],
                "selected_local_organization_remediation": [
                    "observations.empty: Provision authoritative observations via /api/v2/import/upload with import_type=observation.",
                    "bio_qtls.empty: Provision authoritative BioQTL rows via /api/v2/import/upload with import_type=qtl.",
                ],
                "least_blocked_local_organization": None,
                "organizations": [],
            },
            "artifact_integrity": {"all_valid": True, "artifacts": {}},
            "blockers": [],
        }
    )

    assert "### Local Selection Guidance" in markdown
    assert (
        "- The canonical demo dataset is isolated from production and staging; do not mirror demo-seeded benchmark data into selected non-demo organization 1 (Default Organization)."
        in markdown
    )
    assert "### Local Remediation Guidance" in markdown
    assert (
        "- observations.empty: Provision authoritative observations via /api/v2/import/upload with import_type=observation."
        in markdown
    )


def test_generate_markdown_renders_authority_gap_failure_attribution():
    markdown = _generate_markdown(
        {
            "generated_at_utc": "2026-04-02T00:00:00+00:00",
            "commit_hash": "abc123",
            "overall_status": "blocked",
            "gate_outcomes": [],
            "kpi_deltas": {"metrics": {}},
            "real_question_readiness": {},
            "authority_gap_summary": {
                "present": True,
                "overall_gap_status": "no_benchmark_ready_local_org",
                "selected_local_organization_id": 1,
                "organizations_scanned": 2,
                "common_blockers_across_blocked_orgs": ["observations.empty"],
                "surface_gaps": [
                    {
                        "surface_label": "Breeding germplasm detail",
                        "trust_status": "trusted",
                        "failed_cases": 1,
                        "total_cases": 1,
                        "gap_status": "blocked_no_benchmark_ready_local_org",
                        "common_blockers_across_blocked_orgs": ["observations.empty"],
                        "failed_case_details": [
                            {
                                "benchmark_id": "rq-01",
                                "safe_failure_source": "function_result",
                                "safe_failure_error_category": "insufficient_retrieval_scope",
                                "safe_failure_missing": ["specific germplasm identifier"],
                                "safe_failure_searched": ["germplasm_lookup"],
                            }
                        ],
                    }
                ],
            },
            "artifact_integrity": {"all_valid": True, "artifacts": {}},
            "blockers": [],
        }
    )

    assert "### Failed Case Attribution" in markdown
    assert (
        "- Breeding germplasm detail: rq-01: function_result / insufficient_retrieval_scope ; missing specific germplasm identifier ; searched germplasm_lookup"
        in markdown
    )


def test_generate_markdown_renders_authority_gap_guidance():
    markdown = _generate_markdown(
        {
            "generated_at_utc": "2026-04-04T00:00:00+00:00",
            "commit_hash": "abc123",
            "overall_status": "blocked",
            "gate_outcomes": [],
            "kpi_deltas": {"metrics": {}},
            "real_question_readiness": {},
            "authority_gap_summary": {
                "present": True,
                "overall_gap_status": "no_benchmark_ready_local_org",
                "selected_local_organization_id": 1,
                "organizations_scanned": 2,
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
                "surface_gaps": [],
            },
            "artifact_integrity": {"all_valid": True, "artifacts": {}},
            "blockers": [],
        }
    )

    assert "**Least-blocked local org:** 2 (Demo Organization) — blockers: bio_gwas_runs.empty, bio_qtls.empty" in markdown
    assert "### Authority-Gap Selection Guidance" in markdown
    assert "- Do not mirror demo-seeded benchmark data into non-demo organization 1." in markdown
    assert "### Authority-Gap Remediation Guidance" in markdown
    assert "- observations.empty: Import authoritative observations." in markdown