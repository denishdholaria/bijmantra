import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import eval_real_question_benchmark as benchmark_eval


BACKEND_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = BACKEND_ROOT / "tests" / "fixtures" / "reevu" / "real_question_benchmark.json"


def _load_case(benchmark_id: str) -> dict:
    cases = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    for case in cases:
        if case["benchmark_id"] == benchmark_id:
            return case
    raise AssertionError(f"benchmark case not found: {benchmark_id}")


class TestEvalRealQuestionBenchmark(unittest.TestCase):
    def test_score_case_passes_deterministic_compute_case(self) -> None:
        case = _load_case("rq-07")

        payload = {
            "function_call": {"name": "calculate_breeding_value"},
            "function_result": {
                "calculation_method_refs": ["fn:compute.gblup"],
                "retrieval_audit": {"entities": {"germplasm_ids": ["IR64", "Swarna"]}},
            },
            "evidence_envelope": {
                "calculation_steps": [{"step_id": "fn:compute.gblup"}],
                "claims": ["GBLUP score"],
            },
            "plan_execution_summary": {"domains_involved": ["genomics", "analytics"]},
            "policy_validation": {"valid": True},
        }

        result = benchmark_eval.score_case(
            case,
            http_status=200,
            payload=payload,
            runtime_path="local",
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["actual_function"], "calculate_breeding_value")
        self.assertEqual(result["domain_group"], "genomics")
        self.assertEqual(result["cross_domain_class"], "genomics_analytics")
        self.assertEqual(result["question_family"], "genomics::genomics_analytics")
        self.assertEqual(result["failed_checks"], [])

    def test_score_case_passes_safe_failure_case(self) -> None:
        case = _load_case("rq-12")

        safe_failure = {
            "error_category": "ambiguous_retrieval_scope",
            "searched": ["germplasm_lookup"],
            "missing": ["exact germplasm accession"],
        }
        payload = {
            "function_call": {"name": "get_germplasm_details"},
            "function_result": {
                "safe_failure": safe_failure,
                "retrieval_audit": {"entities": {"candidate_ids": ["IR64", "IR72"]}},
            },
            "policy_validation": {"valid": False, "safe_failure": safe_failure},
            "evidence_envelope": {"claims": []},
        }

        result = benchmark_eval.score_case(
            case,
            http_status=200,
            payload=payload,
            runtime_path="managed",
        )

        self.assertTrue(result["passed"])
        self.assertTrue(result["safe_failure_observed"])
        self.assertEqual(result["safe_failure_source"], "policy_validation")
        self.assertEqual(result["safe_failure_payload"], safe_failure)
        self.assertEqual(result["failed_checks"], [])

    def test_score_case_accepts_top_level_retrieval_audit_from_chat_contract(self) -> None:
        case = _load_case("rq-01")

        payload = {
            "function_call": {"name": "get_germplasm_details"},
            "function_result": {
                "success": True,
                "result_type": "germplasm_details",
            },
            "retrieval_audit": {
                "services": ["germplasm_search_service.get_by_id"],
                "entities": {"germplasm_id": "101"},
            },
            "evidence_envelope": {
                "claims": ["IR64 was retrieved from the database."],
            },
            "policy_validation": {"valid": True},
        }

        result = benchmark_eval.score_case(
            case,
            http_status=200,
            payload=payload,
            runtime_path="local",
        )

        self.assertTrue(result["passed"])
        self.assertIsNone(result["safe_failure_source"])
        self.assertIsNone(result["safe_failure_payload"])
        self.assertEqual(result["failed_checks"], [])

    def test_score_case_fails_when_success_case_emits_unexpected_safe_failure(self) -> None:
        case = _load_case("rq-01")

        safe_failure = {
            "error_category": "insufficient_evidence",
            "searched": ["function_result"],
            "missing": ["grounded evidence for one or more claims"],
        }
        payload = {
            "function_call": {"name": "get_germplasm_details"},
            "function_result": {
                "success": True,
                "result_type": "germplasm_details",
                "safe_failure": safe_failure,
            },
            "retrieval_audit": {
                "services": ["germplasm_search_service.get_by_id"],
                "entities": {"germplasm_id": "101"},
            },
            "evidence_envelope": {
                "claims": ["IR64 was retrieved from the database."],
            },
            "policy_validation": {"valid": False, "safe_failure": safe_failure},
        }

        result = benchmark_eval.score_case(
            case,
            http_status=200,
            payload=payload,
            runtime_path="local",
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["safe_failure_source"], "policy_validation")
        self.assertEqual(result["safe_failure_payload"], safe_failure)
        self.assertIn("safe_failure.unexpected_safe_failure", result["failed_checks"])

    def test_score_case_records_function_safe_failure_metadata_when_policy_validation_is_clean(self) -> None:
        case = _load_case("rq-01")

        safe_failure = {
            "error_category": "insufficient_retrieval_scope",
            "searched": ["germplasm_lookup"],
            "missing": ["specific germplasm identifier"],
        }
        payload = {
            "function_call": {"name": "get_germplasm_details"},
            "function_result": {
                "success": False,
                "safe_failure": safe_failure,
            },
            "retrieval_audit": {
                "services": ["germplasm_search_service.search"],
                "entities": {"query": "IR64", "match_count": 0},
            },
            "evidence_envelope": {"claims": []},
            "policy_validation": {"valid": True},
        }

        result = benchmark_eval.score_case(
            case,
            http_status=200,
            payload=payload,
            runtime_path="local",
        )

        self.assertFalse(result["passed"])
        self.assertTrue(result["safe_failure_observed"])
        self.assertEqual(result["safe_failure_source"], "function_result")
        self.assertEqual(result["safe_failure_payload"], safe_failure)
        self.assertIn("safe_failure.unexpected_safe_failure", result["failed_checks"])

    def test_build_summary_tracks_runtime_path_and_pass_rate(self) -> None:
        results = [
            {
                "benchmark_id": "rq-01",
                "passed": True,
                "failed_checks": [],
                "domain_group": "breeding",
                "cross_domain_class": "single_domain",
                "question_family": "breeding::single_domain",
            },
            {
                "benchmark_id": "rq-02",
                "passed": False,
                "failed_checks": ["x"],
                "domain_group": "breeding",
                "cross_domain_class": "breeding_trials",
                "question_family": "breeding::breeding_trials",
            },
        ]

        summary = benchmark_eval.build_summary(
            fixture_path=FIXTURE_PATH,
            runtime_path="managed",
            results=results,
            managed_base_url="https://reevu.example.com",
        )

        self.assertEqual(summary["runtime_path"], "managed")
        self.assertEqual(summary["runtime_target"], "https://reevu.example.com")
        self.assertEqual(summary["runtime_status"], "evaluated")
        self.assertEqual(summary["total_cases"], 2)
        self.assertEqual(summary["passed_cases"], 1)
        self.assertEqual(summary["failed_cases"], 1)
        self.assertEqual(summary["pass_rate"], 0.5)
        self.assertEqual(
            summary["question_family_summary"]["by_domain_group"]["breeding"]["failed_benchmark_ids"],
            ["rq-02"],
        )
        self.assertEqual(
            summary["question_family_summary"]["by_cross_domain_class"]["single_domain"]["pass_rate"],
            1.0,
        )
        self.assertEqual(
            summary["question_family_summary"]["by_question_family"]["breeding::breeding_trials"]["failed_cases"],
            1,
        )

    def test_build_summary_includes_local_runtime_readiness_snapshot(self) -> None:
        results = [
            {
                "benchmark_id": "rq-01",
                "passed": False,
                "failed_checks": ["safe_failure.unexpected_safe_failure"],
                "domain_group": "breeding",
                "cross_domain_class": "single_domain",
                "question_family": "breeding::single_domain",
            }
        ]

        readiness = {
            "organization_id": 1,
            "surface_counts": {"germplasm": 2, "observations": 0},
            "surface_examples": {"germplasm": ["TEST-VAR-8841-A"]},
            "surface_errors": {"bio_qtls": "ProgrammingError: relation \"bio_qtls\" does not exist"},
            "readiness_flags": ["germplasm.sparse", "observations.empty", "bio_qtls.missing_or_inaccessible"],
        }

        with patch.object(benchmark_eval, "_inspect_local_runtime_readiness", return_value=readiness):
            summary = benchmark_eval.build_summary(
                fixture_path=FIXTURE_PATH,
                runtime_path="local",
                results=results,
                local_organization_id=7,
                local_organization_selection={
                    "mode": "cli",
                    "requested_organization_id": 7,
                    "effective_organization_id": 7,
                },
            )

        self.assertEqual(summary["runtime_target"], "in_process_app")
        self.assertEqual(summary["runtime_status"], "blocked")
        self.assertEqual(summary["local_organization_id"], 7)
        self.assertEqual(
            summary["local_organization_selection"],
            {"mode": "cli", "requested_organization_id": 7, "effective_organization_id": 7},
        )
        self.assertEqual(summary["readiness_blockers"], ["observations.empty", "bio_qtls.missing_or_inaccessible"])
        self.assertEqual(summary["readiness_warnings"], ["germplasm.sparse"])
        self.assertEqual(summary["runtime_readiness"], readiness)
        self.assertEqual(
            summary["failure_attribution_summary"],
            {"executor_regression_or_contract_gap": 1},
        )
        self.assertEqual(
            summary["results"][0]["failure_attribution"]["status"],
            "executor_regression_or_contract_gap",
        )

    def test_build_summary_attributes_local_safe_failure_to_selected_org_readiness(self) -> None:
        case = _load_case("rq-01")
        readiness = {
            "organization_id": 1,
            "surface_counts": {"germplasm": 2, "observations": 0},
            "surface_examples": {"germplasm": ["IR64"]},
            "surface_errors": {},
            "readiness_flags": ["germplasm.sparse", "observations.empty"],
        }

        with patch.object(benchmark_eval, "_inspect_local_runtime_readiness", return_value=readiness):
            summary = benchmark_eval.build_summary(
                fixture_path=FIXTURE_PATH,
                runtime_path="local",
                results=[
                    {
                        "benchmark_id": case["benchmark_id"],
                        "passed": False,
                        "failed_checks": ["safe_failure.unexpected_safe_failure"],
                        "domain_group": case["domain_group"],
                        "cross_domain_class": case["cross_domain_class"],
                        "question_family": benchmark_eval._question_family(case),
                        "expected_function": case["expected_function"],
                        "expected_domains": case["expected_domains"],
                        "safe_failure_expected": case["safe_failure_expected"],
                        "safe_failure_observed": True,
                        "safe_failure_source": "function_result",
                        "safe_failure_payload": {
                            "error_category": "insufficient_retrieval_scope",
                            "missing": ["specific germplasm identifier"],
                            "searched": ["germplasm_lookup"],
                        },
                    }
                ],
                local_organization_id=1,
            )

        attribution = summary["results"][0]["failure_attribution"]

        self.assertEqual(
            summary["failure_attribution_summary"],
            {"selected_local_org_readiness_warning": 1},
        )
        self.assertEqual(attribution["status"], "selected_local_org_readiness_warning")
        self.assertEqual(attribution["relevant_blockers"], [])
        self.assertEqual(attribution["relevant_warnings"], ["germplasm.sparse"])
        self.assertEqual(attribution["unmapped_expected_domains"], [])

    def test_resolve_local_organization_selection_prefers_cli_then_env_then_default(self) -> None:
        self.assertEqual(
            benchmark_eval._resolve_local_organization_selection(cli_value="7", env_value="9"),
            {"mode": "cli", "requested_organization_id": 7, "effective_organization_id": 7},
        )
        self.assertEqual(
            benchmark_eval._resolve_local_organization_selection(cli_value=None, env_value="9"),
            {"mode": "env", "requested_organization_id": 9, "effective_organization_id": 9},
        )
        self.assertEqual(
            benchmark_eval._resolve_local_organization_selection(cli_value=None, env_value=None),
            {"mode": "default", "requested_organization_id": 1, "effective_organization_id": 1},
        )

    def test_build_local_readiness_census_payload_keeps_selected_org_explicit(self) -> None:
        payload = benchmark_eval._build_local_readiness_census_payload(
            organizations=[
                {
                    "organization_id": 2,
                    "organization_name": "Ready Org",
                    "is_active": True,
                    "listed_in_active_organizations": True,
                }
            ],
            readiness_by_organization_id={
                1: {
                    "organization_id": 1,
                    "surface_counts": {"observations": 0},
                    "surface_examples": {},
                    "surface_errors": {"bio_qtls": "UndefinedTableError"},
                    "readiness_flags": ["observations.empty", "bio_qtls.missing_or_inaccessible"],
                },
                2: {
                    "organization_id": 2,
                    "surface_counts": {"germplasm": 8, "trials": 8, "observations": 20, "bio_gwas_runs": 3, "bio_qtls": 2},
                    "surface_examples": {"germplasm": ["IR64"]},
                    "surface_errors": {},
                    "readiness_flags": [],
                },
            },
            local_organization_selection={
                "mode": "default",
                "requested_organization_id": 1,
                "effective_organization_id": 1,
            },
        )

        self.assertEqual(payload["selected_local_organization_id"], 1)
        self.assertEqual(payload["benchmark_ready_organization_ids"], [2])
        self.assertEqual(payload["benchmark_ready_demo_organization_ids"], [])
        self.assertEqual(payload["benchmark_ready_non_demo_organization_ids"], [2])
        self.assertEqual(payload["blocked_organization_ids"], [1])
        self.assertEqual(payload["organizations_scanned"], 2)
        self.assertEqual(payload["policy_guidance"], [])
        self.assertEqual(
            payload["selected_local_organization_remediation"],
            [
                "observations.empty: Provision authoritative observations for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=observation.",
                "bio_qtls.missing_or_inaccessible: Provision authoritative BioQTL rows for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=qtl.",
            ],
        )
        self.assertEqual(payload["organizations"][0]["organization_id"], 1)
        self.assertEqual(payload["organizations"][0]["organization_scope"], "unknown")
        self.assertTrue(payload["organizations"][0]["selected"])
        self.assertFalse(payload["organizations"][0]["listed_in_active_organizations"])
        self.assertEqual(payload["organizations"][1]["organization_name"], "Ready Org")
        self.assertEqual(payload["organizations"][1]["organization_scope"], "non_demo")
        self.assertEqual(payload["organizations"][1]["runtime_status"], "ready")
        self.assertIsNone(payload["least_blocked_local_organization"])

    def test_build_local_readiness_census_payload_adds_demo_only_policy_guidance(self) -> None:
        payload = benchmark_eval._build_local_readiness_census_payload(
            organizations=[
                {
                    "organization_id": 1,
                    "organization_name": "Default Organization",
                    "is_active": True,
                    "listed_in_active_organizations": True,
                },
                {
                    "organization_id": 2,
                    "organization_name": "Demo Organization",
                    "is_active": True,
                    "listed_in_active_organizations": True,
                },
            ],
            readiness_by_organization_id={
                1: {
                    "organization_id": 1,
                    "surface_counts": {"observations": 0, "bio_gwas_runs": 0, "bio_qtls": 0},
                    "surface_examples": {},
                    "surface_errors": {},
                    "readiness_flags": ["observations.empty", "bio_gwas_runs.empty", "bio_qtls.empty"],
                },
                2: {
                    "organization_id": 2,
                    "surface_counts": {"germplasm": 8, "trials": 8, "observations": 20, "bio_gwas_runs": 3, "bio_qtls": 2},
                    "surface_examples": {"germplasm": ["IR64"]},
                    "surface_errors": {},
                    "readiness_flags": [],
                },
            },
            local_organization_selection={
                "mode": "default",
                "requested_organization_id": 1,
                "effective_organization_id": 1,
            },
        )

        self.assertEqual(payload["benchmark_ready_organization_ids"], [2])
        self.assertEqual(payload["benchmark_ready_demo_organization_ids"], [2])
        self.assertEqual(payload["benchmark_ready_non_demo_organization_ids"], [])
        self.assertEqual(len(payload["policy_guidance"]), 1)
        self.assertIn("do not mirror demo-seeded benchmark data", payload["policy_guidance"][0])
        self.assertIn("1 (Default Organization)", payload["policy_guidance"][0])
        self.assertEqual(
            payload["selected_local_organization_remediation"],
            [
                "observations.empty: Provision authoritative observations for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=observation.",
                "bio_gwas_runs.empty: Persist authoritative GWAS runs for the selected organization through the authenticated GWAS execution surface at /api/v2/bio-analytics/gwas/run using authoritative genotype and phenotype inputs.",
                "bio_qtls.empty: Provision authoritative BioQTL rows for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=qtl.",
            ],
        )

    def test_build_local_readiness_census_payload_selects_least_blocked_local_org(self) -> None:
        payload = benchmark_eval._build_local_readiness_census_payload(
            organizations=[
                {
                    "organization_id": 1,
                    "organization_name": "Default Organization",
                    "is_active": True,
                    "listed_in_active_organizations": True,
                },
                {
                    "organization_id": 2,
                    "organization_name": "Demo Organization",
                    "is_active": True,
                    "listed_in_active_organizations": True,
                },
            ],
            readiness_by_organization_id={
                1: {
                    "organization_id": 1,
                    "surface_counts": {"germplasm": 2, "trials": 2, "observations": 0, "bio_gwas_runs": 0},
                    "surface_examples": {},
                    "surface_errors": {"bio_qtls": "UndefinedTableError"},
                    "readiness_flags": ["germplasm.sparse", "trials.sparse", "observations.empty", "bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"],
                },
                2: {
                    "organization_id": 2,
                    "surface_counts": {"germplasm": 18, "trials": 3, "observations": 9, "bio_gwas_runs": 0},
                    "surface_examples": {"germplasm": ["IR64"]},
                    "surface_errors": {"bio_qtls": "UndefinedTableError"},
                    "readiness_flags": ["trials.sparse", "bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"],
                },
            },
            local_organization_selection={
                "mode": "default",
                "requested_organization_id": 1,
                "effective_organization_id": 1,
            },
        )

        self.assertEqual(payload["benchmark_ready_organization_ids"], [])
        self.assertEqual(
            payload["least_blocked_local_organization"],
            {
                "organization_id": 2,
                "organization_name": "Demo Organization",
                "organization_scope": "demo_dataset",
                "selected": False,
                "runtime_status": "blocked",
                "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.missing_or_inaccessible"],
                "readiness_warnings": ["trials.sparse"],
                "benchmark_relevant_surface_count": 30,
            },
        )
        self.assertEqual(
            payload["selected_local_organization_remediation"],
            [
                "observations.empty: Provision authoritative observations for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=observation.",
                "bio_gwas_runs.empty: Persist authoritative GWAS runs for the selected organization through the authenticated GWAS execution surface at /api/v2/bio-analytics/gwas/run using authoritative genotype and phenotype inputs.",
                "bio_qtls.missing_or_inaccessible: Provision authoritative BioQTL rows for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=qtl.",
                "germplasm.sparse: Expand authoritative germplasm coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=germplasm.",
                "trials.sparse: Expand authoritative trial coverage for the selected organization via the authenticated import upload surface at /api/v2/import/upload with import_type=trial.",
            ],
        )

    def test_build_local_readiness_console_lines_surfaces_guidance(self) -> None:
        lines = benchmark_eval._build_local_readiness_console_lines(
            {
                "organizations": [
                    {
                        "organization_id": 2,
                        "organization_name": "Demo Organization",
                        "organization_scope": "demo_dataset",
                        "runtime_status": "ready",
                    }
                ],
                "policy_guidance": [
                    "Do not mirror demo-seeded benchmark data into non-demo organization 1."
                ],
                "selected_local_organization_remediation": [
                    "observations.empty: Import authoritative observations."
                ],
            }
        )

        self.assertEqual(
            lines,
            [
                "- benchmark-ready local organizations: 2 (Demo Organization), demo dataset",
                "- local selection guidance: Do not mirror demo-seeded benchmark data into non-demo organization 1.",
                "- recommended remediation: observations.empty: Import authoritative observations.",
            ],
        )

    def test_build_blocked_local_runtime_message_includes_least_blocked_and_remediation(self) -> None:
        message = benchmark_eval._build_blocked_local_runtime_message(
            {
                "local_organization_id": 1,
                "readiness_blockers": ["observations.empty", "bio_qtls.empty"],
            },
            local_readiness_census={
                "organizations": [],
                "policy_guidance": [
                    "The canonical demo dataset is isolated from production and staging."
                ],
                "selected_local_organization_remediation": [
                    "observations.empty: Import authoritative observations.",
                    "bio_qtls.empty: Import authoritative QTL rows.",
                ],
                "least_blocked_local_organization": {
                    "organization_id": 2,
                    "organization_name": "Demo Organization",
                    "readiness_blockers": ["bio_gwas_runs.empty", "bio_qtls.empty"],
                },
            },
        )

        self.assertEqual(
            message,
            "Benchmark blocked: local runtime organization 1 is not benchmark-ready (observations.empty, bio_qtls.empty). Least-blocked local organization is 2 (Demo Organization): bio_gwas_runs.empty, bio_qtls.empty. The canonical demo dataset is isolated from production and staging. Recommended remediation: observations.empty: Import authoritative observations. bio_qtls.empty: Import authoritative QTL rows.",
        )

    def test_main_requires_managed_base_url(self) -> None:
        exit_code = benchmark_eval.main(
            [
                "--runtime-path",
                "managed",
                "--fixture",
                str(FIXTURE_PATH),
            ]
        )

        self.assertEqual(exit_code, 2)

    def test_main_can_fail_when_failed_cases_are_present(self) -> None:
        with patch.object(benchmark_eval, "_load_fixture", return_value=[]), patch.object(
            benchmark_eval,
            "evaluate_cases",
            return_value=[],
        ), patch.object(
            benchmark_eval,
            "build_summary",
            return_value={
                "generated_at": "2099-01-01T00:00:00+00:00",
                "runtime_path": "local",
                "runtime_target": "in_process_app",
                "runtime_status": "ready",
                "total_cases": 1,
                "passed_cases": 0,
                "failed_cases": 1,
                "pass_rate": 0.0,
                "question_family_summary": {
                    "by_domain_group": {},
                    "by_cross_domain_class": {},
                    "by_question_family": {},
                },
                "results": [],
            },
        ), patch.object(benchmark_eval, "_print_summary", return_value=None):
            exit_code = benchmark_eval.main(
                [
                    "--runtime-path",
                    "local",
                    "--fixture",
                    str(FIXTURE_PATH),
                    "--fail-on-failed-cases",
                ]
            )

        self.assertEqual(exit_code, 1)

    def test_main_can_fail_when_local_runtime_is_blocked(self) -> None:
        with patch.object(benchmark_eval, "_load_fixture", return_value=[]), patch.object(
            benchmark_eval,
            "evaluate_cases",
            return_value=[],
        ), patch.object(
            benchmark_eval,
            "build_summary",
            return_value={
                "generated_at": "2099-01-01T00:00:00+00:00",
                "runtime_path": "local",
                "runtime_target": "in_process_app",
                "runtime_status": "blocked",
                "local_organization_id": 7,
                "readiness_blockers": ["observations.empty"],
                "total_cases": 0,
                "passed_cases": 0,
                "failed_cases": 0,
                "pass_rate": 0.0,
                "question_family_summary": {
                    "by_domain_group": {},
                    "by_cross_domain_class": {},
                    "by_question_family": {},
                },
                "results": [],
            },
        ), patch.object(
            benchmark_eval,
            "build_local_readiness_census",
            return_value={
                "organizations": [
                    {
                        "organization_id": 2,
                        "organization_name": "Demo Organization",
                        "organization_scope": "demo_dataset",
                        "runtime_status": "ready",
                    }
                ],
                "policy_guidance": [
                    "Do not mirror demo-seeded benchmark data into non-demo organization 7."
                ],
                "selected_local_organization_remediation": [
                    "observations.empty: Import authoritative observations."
                ],
            },
        ), patch.object(benchmark_eval, "_print_summary", return_value=None), patch("builtins.print") as print_mock:
            exit_code = benchmark_eval.main(
                [
                    "--runtime-path",
                    "local",
                    "--fixture",
                    str(FIXTURE_PATH),
                    "--fail-on-failed-cases",
                ]
            )

        self.assertEqual(exit_code, 1)
        printed = "\n".join(
            " ".join(str(arg) for arg in call.args)
            for call in print_mock.call_args_list
        )
        self.assertIn("Benchmark-ready local organizations discovered: 2 (Demo Organization), demo dataset.", printed)
        self.assertIn("Recommended remediation: observations.empty: Import authoritative observations.", printed)

    def test_validate_auth_token_rejects_whitespace(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not contain whitespace"):
            benchmark_eval._validate_auth_token("bad token")

    def test_parse_local_organization_id_rejects_non_numeric_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be an integer"):
            benchmark_eval._parse_local_organization_id("demo")

    def test_evaluate_cases_local_reuses_single_test_client_context(self) -> None:
        cases = [{"query": "first"}, {"query": "second"}]
        enter_count = 0
        exit_count = 0
        queries: list[str] = []

        class FakePoster:
            def __enter__(self):
                nonlocal enter_count
                enter_count += 1

                def post_local_query(query: str) -> tuple[int, dict]:
                    queries.append(query)
                    return 200, {"function_call": {"name": "get_germplasm_details"}}

                return post_local_query

            def __exit__(self, exc_type, exc, tb) -> bool:
                nonlocal exit_count
                exit_count += 1
                return False

        with patch.object(benchmark_eval, "_local_query_poster", return_value=FakePoster()) as poster_mock:
            with patch.object(
                benchmark_eval,
                "score_case",
                side_effect=[
                    {"benchmark_id": "first", "passed": True},
                    {"benchmark_id": "second", "passed": True},
                ],
            ):
                results = benchmark_eval.evaluate_cases(
                    cases,
                    runtime_path="local",
                    local_organization_id=9,
                )

        self.assertEqual(enter_count, 1)
        self.assertEqual(exit_count, 1)
        self.assertEqual(queries, ["first", "second"])
        poster_mock.assert_called_once_with(local_organization_id=9)
        self.assertEqual(results, [{"benchmark_id": "first", "passed": True}, {"benchmark_id": "second", "passed": True}])


if __name__ == "__main__":
    unittest.main()
