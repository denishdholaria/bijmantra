from scripts.generate_reevu_authority_gap_report import build_authority_gap_report


def test_build_authority_gap_report_marks_no_ready_local_org_and_common_blockers():
    report = build_authority_gap_report(
        local_benchmark_payload={
            "failed_cases": 2,
            "results": [
                {
                    "benchmark_id": "rq-01",
                    "expected_function": "get_germplasm_details",
                    "question_family": "breeding::single_domain",
                    "passed": False,
                    "failure_attribution": {
                        "status": "selected_local_org_readiness_warning",
                        "reason": "The selected local organization is sparse on benchmark-relevant data surfaces.",
                        "relevant_blockers": [],
                        "relevant_warnings": ["germplasm.sparse"],
                        "unmapped_expected_domains": [],
                    },
                    "safe_failure_source": "function_result",
                    "safe_failure_payload": {
                        "error_category": "insufficient_retrieval_scope",
                        "missing": ["specific germplasm identifier"],
                        "searched": ["germplasm_lookup"],
                    },
                    "failed_checks": ["safe_failure.unexpected_safe_failure"],
                },
                {
                    "benchmark_id": "rq-04",
                    "expected_function": "get_trial_results",
                    "question_family": "trials::single_domain",
                    "passed": False,
                    "safe_failure_source": "function_result",
                    "safe_failure_payload": {
                        "error_category": "insufficient_retrieval_scope",
                        "missing": ["specific trial identifier"],
                        "searched": ["trial_summary"],
                    },
                    "failed_checks": ["safe_failure.unexpected_safe_failure"],
                },
            ],
        },
        local_readiness_census_payload={
            "selected_local_organization_id": 1,
            "local_organization_selection": {
                "mode": "default",
                "requested_organization_id": 1,
                "effective_organization_id": 1,
            },
            "organizations_scanned": 2,
            "benchmark_ready_organization_ids": [],
            "blocked_organization_ids": [1, 2],
            "organizations": [
                {
                    "organization_id": 1,
                    "runtime_status": "blocked",
                    "readiness_blockers": [
                        "observations.empty",
                        "bio_gwas_runs.empty",
                        "bio_qtls.missing_or_inaccessible",
                    ],
                    "readiness_warnings": ["germplasm.sparse"],
                },
                {
                    "organization_id": 2,
                    "runtime_status": "blocked",
                    "readiness_blockers": [
                        "trials.empty",
                        "observations.empty",
                        "bio_gwas_runs.empty",
                        "bio_qtls.missing_or_inaccessible",
                    ],
                    "readiness_warnings": [],
                },
            ],
        },
    )

    assert report["overall_gap_status"] == "no_benchmark_ready_local_org"
    assert report["common_blockers_across_blocked_orgs"] == [
        "bio_gwas_runs.empty",
        "bio_qtls.missing_or_inaccessible",
        "observations.empty",
    ]
    breeding_surface = next(
        surface_gap
        for surface_gap in report["surface_gaps"]
        if surface_gap["surface_key"] == "breeding_germplasm_detail"
    )
    assert breeding_surface["failed_cases"] == 1
    assert breeding_surface["gap_status"] == "blocked_no_benchmark_ready_local_org"
    assert breeding_surface["safe_failure_sources"] == ["function_result"]
    assert breeding_surface["safe_failure_error_categories"] == ["insufficient_retrieval_scope"]
    assert breeding_surface["failure_attribution_statuses"] == [
        "selected_local_org_readiness_warning"
    ]
    assert breeding_surface["failure_attribution_summary"] == {
        "selected_local_org_readiness_warning": 1
    }
    breeding_detail = breeding_surface["failed_case_details"][0]
    assert breeding_detail["benchmark_id"] == "rq-01"
    assert breeding_detail["expected_function"] == "get_germplasm_details"
    assert breeding_detail["question_family"] == "breeding::single_domain"
    assert breeding_detail["safe_failure_source"] == "function_result"
    assert breeding_detail["safe_failure_error_category"] == "insufficient_retrieval_scope"
    assert breeding_detail["safe_failure_missing"] == ["specific germplasm identifier"]
    assert breeding_detail["safe_failure_searched"] == ["germplasm_lookup"]
    assert breeding_detail["failure_attribution_status"] == "selected_local_org_readiness_warning"
    assert breeding_detail["failure_attribution_relevant_blockers"] == []
    assert breeding_detail["failure_attribution_relevant_warnings"] == ["germplasm.sparse"]
    assert breeding_detail["failure_attribution_unmapped_expected_domains"] == []


def test_build_authority_gap_report_propagates_demo_dataset_policy_guidance():
    report = build_authority_gap_report(
        local_benchmark_payload={
            "failed_cases": 1,
            "results": [
                {
                    "benchmark_id": "rq-01",
                    "expected_function": "get_germplasm_details",
                    "question_family": "breeding::single_domain",
                    "passed": False,
                    "failed_checks": ["safe_failure.unexpected_safe_failure"],
                }
            ],
        },
        local_readiness_census_payload={
            "selected_local_organization_id": 1,
            "local_organization_selection": {
                "mode": "default",
                "requested_organization_id": 1,
                "effective_organization_id": 1,
            },
            "organizations_scanned": 2,
            "benchmark_ready_organization_ids": [2],
            "benchmark_ready_demo_organization_ids": [2],
            "benchmark_ready_non_demo_organization_ids": [],
            "blocked_organization_ids": [1],
            "policy_guidance": [
                "Demo benchmark coverage is isolated from production and staging."
            ],
            "selected_local_organization_remediation": [
                "observations.empty: Import authoritative observations for the selected organization."
            ],
            "organizations": [
                {
                    "organization_id": 1,
                    "runtime_status": "blocked",
                    "readiness_blockers": ["observations.empty"],
                    "readiness_warnings": [],
                },
                {
                    "organization_id": 2,
                    "runtime_status": "ready",
                    "readiness_blockers": [],
                    "readiness_warnings": [],
                },
            ],
        },
    )

    assert report["benchmark_ready_demo_organization_ids"] == [2]
    assert report["benchmark_ready_non_demo_organization_ids"] == []
    assert report["policy_guidance"] == [
        "Demo benchmark coverage is isolated from production and staging."
    ]
    assert report["selected_local_organization_remediation"] == [
        "observations.empty: Import authoritative observations for the selected organization."
    ]
    assert report["least_blocked_local_organization"] is None


def test_build_authority_gap_report_propagates_least_blocked_org_when_none_are_ready():
    report = build_authority_gap_report(
        local_benchmark_payload={
            "failed_cases": 1,
            "results": [
                {
                    "benchmark_id": "rq-04",
                    "expected_function": "get_trial_results",
                    "question_family": "trials::single_domain",
                    "passed": False,
                    "failed_checks": ["safe_failure.unexpected_safe_failure"],
                }
            ],
        },
        local_readiness_census_payload={
            "selected_local_organization_id": 1,
            "local_organization_selection": {
                "mode": "default",
                "requested_organization_id": 1,
                "effective_organization_id": 1,
            },
            "organizations_scanned": 2,
            "benchmark_ready_organization_ids": [],
            "benchmark_ready_demo_organization_ids": [],
            "benchmark_ready_non_demo_organization_ids": [],
            "blocked_organization_ids": [1, 2],
            "policy_guidance": [],
            "selected_local_organization_remediation": [
                "observations.empty: Import authoritative observations for the selected organization."
            ],
            "least_blocked_local_organization": {
                "organization_id": 2,
                "organization_name": "Demo Organization",
                "organization_scope": "demo_dataset",
                "selected": False,
                "runtime_status": "blocked",
                "readiness_blockers": ["bio_gwas_runs.empty"],
                "readiness_warnings": ["trials.sparse"],
                "benchmark_relevant_surface_count": 9,
            },
            "organizations": [
                {
                    "organization_id": 1,
                    "runtime_status": "blocked",
                    "readiness_blockers": ["observations.empty"],
                    "readiness_warnings": [],
                },
                {
                    "organization_id": 2,
                    "runtime_status": "blocked",
                    "readiness_blockers": ["bio_gwas_runs.empty"],
                    "readiness_warnings": ["trials.sparse"],
                },
            ],
        },
    )

    assert report["benchmark_ready_organization_ids"] == []
    assert report["selected_local_organization_remediation"] == [
        "observations.empty: Import authoritative observations for the selected organization."
    ]
    assert report["least_blocked_local_organization"] == {
        "organization_id": 2,
        "organization_name": "Demo Organization",
        "organization_scope": "demo_dataset",
        "selected": False,
        "runtime_status": "blocked",
        "readiness_blockers": ["bio_gwas_runs.empty"],
        "readiness_warnings": ["trials.sparse"],
        "benchmark_relevant_surface_count": 9,
    }


def test_build_authority_gap_report_keeps_partial_surface_entries():
    report = build_authority_gap_report(
        local_benchmark_payload={
            "failed_cases": 1,
            "results": [
                {
                    "benchmark_id": "rq-11",
                    "expected_function": "cross_domain_query",
                    "question_family": "breeding::breeding_analytics_protocol",
                    "passed": False,
                    "safe_failure_source": "function_result",
                    "safe_failure_payload": {
                        "error_category": "insufficient_retrieval_scope",
                        "missing": ["protocol evidence"],
                        "searched": ["cross_domain_query"],
                    },
                    "failed_checks": ["safe_failure.unexpected_safe_failure"],
                }
            ],
        },
        local_readiness_census_payload={
            "selected_local_organization_id": 1,
            "local_organization_selection": {
                "mode": "default",
                "requested_organization_id": 1,
                "effective_organization_id": 1,
            },
            "organizations_scanned": 1,
            "benchmark_ready_organization_ids": [],
            "blocked_organization_ids": [1],
            "organizations": [
                {
                    "organization_id": 1,
                    "runtime_status": "blocked",
                    "readiness_blockers": ["bio_qtls.missing_or_inaccessible"],
                    "readiness_warnings": [],
                }
            ],
        },
    )

    protocol_surface = next(
        surface_gap
        for surface_gap in report["surface_gaps"]
        if surface_gap["surface_key"] == "speed_breeding_protocol_enrichment"
    )
    assert protocol_surface["trust_status"] == "partial"
    assert protocol_surface["benchmark_ids"] == ["rq-11"]
    assert protocol_surface["failed_cases"] == 1
    assert protocol_surface["safe_failure_sources"] == ["function_result"]
    assert protocol_surface["failed_case_details"][0]["safe_failure_error_category"] == (
        "insufficient_retrieval_scope"
    )