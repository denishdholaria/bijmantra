"""Generate a REEVU authority-gap diagnostic report for the local benchmark lane.

This artifact explains why the local benchmark is blocked or failing without changing
benchmark scoring. It ties failed benchmark classes to the locked first-wave REEVU
surfaces so operators can see which local authorities are still missing.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


FIRST_WAVE_SURFACE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "surface_key": "breeding_germplasm_detail",
        "surface_label": "Breeding germplasm detail",
        "trust_status": "trusted",
        "expected_functions": ("get_germplasm_details",),
    },
    {
        "surface_key": "breeding_phenotype_summary_and_comparison",
        "surface_label": "Breeding phenotype summary and comparison",
        "trust_status": "trusted",
        "expected_functions": ("get_trait_summary", "compare_germplasm"),
    },
    {
        "surface_key": "trial_summary_and_ranking",
        "surface_label": "Trial summary and ranking",
        "trust_status": "trusted",
        "expected_functions": ("get_trial_results",),
    },
    {
        "surface_key": "genomics_marker_and_qtl_lookup",
        "surface_label": "Genomics marker and QTL lookup",
        "trust_status": "trusted",
        "expected_functions": ("get_marker_associations",),
    },
    {
        "surface_key": "deterministic_breeding_value_compute",
        "surface_label": "Deterministic breeding-value compute",
        "trust_status": "trusted",
        "expected_functions": ("calculate_breeding_value",),
    },
    {
        "surface_key": "cross_domain_orchestration",
        "surface_label": "Cross-domain orchestration",
        "trust_status": "trusted",
        "expected_functions": ("cross_domain_query",),
    },
    {
        "surface_key": "weather_enrichment_inside_cross_domain_queries",
        "surface_label": "Weather enrichment inside cross-domain queries",
        "trust_status": "partial",
        "question_families": ("trials::trials_analytics_weather",),
    },
    {
        "surface_key": "speed_breeding_protocol_enrichment",
        "surface_label": "Speed-breeding protocol enrichment inside cross-domain queries",
        "trust_status": "partial",
        "question_families": ("breeding::breeding_analytics_protocol",),
    },
)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _derive_common_blockers(census_payload: dict[str, Any]) -> list[str]:
    blocked_orgs = [
        organization
        for organization in census_payload.get("organizations", [])
        if isinstance(organization, dict) and organization.get("runtime_status") == "blocked"
    ]
    if not blocked_orgs:
        return []

    common_blockers = set(blocked_orgs[0].get("readiness_blockers") or [])
    for organization in blocked_orgs[1:]:
        common_blockers &= set(organization.get("readiness_blockers") or [])

    return sorted(common_blockers)


def _surface_matches_result(surface_definition: dict[str, Any], result: dict[str, Any]) -> bool:
    expected_functions = surface_definition.get("expected_functions") or ()
    question_families = surface_definition.get("question_families") or ()

    if expected_functions and result.get("expected_function") in expected_functions:
        return True
    if question_families and result.get("question_family") in question_families:
        return True
    return False


def _surface_gap_status(
    *,
    failed_cases: int,
    benchmark_ready_organization_ids: list[int],
    selected_local_org_status: str | None,
) -> str:
    if failed_cases == 0:
        return "clear"
    if not benchmark_ready_organization_ids:
        return "blocked_no_benchmark_ready_local_org"
    if selected_local_org_status == "blocked":
        return "blocked_selected_local_org"
    return "failing_with_ready_local_org_available"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _failure_attribution_payload(result: dict[str, Any]) -> dict[str, Any]:
    payload = result.get("failure_attribution")
    return payload if isinstance(payload, dict) else {}


def _summarize_failure_attributions(results: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for result in results:
        status = _failure_attribution_payload(result).get("status")
        if not isinstance(status, str) or not status.strip():
            continue
        summary[status] = summary.get(status, 0) + 1
    return {status: summary[status] for status in sorted(summary)}


def _build_failed_case_details(failed_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for result in sorted(
        failed_results,
        key=lambda item: str(item.get("benchmark_id") or ""),
    ):
        safe_failure_payload = result.get("safe_failure_payload")
        safe_failure_payload = safe_failure_payload if isinstance(safe_failure_payload, dict) else {}
        failure_attribution = _failure_attribution_payload(result)
        details.append(
            {
                "benchmark_id": result.get("benchmark_id"),
                "expected_function": result.get("expected_function"),
                "question_family": result.get("question_family"),
                "safe_failure_source": result.get("safe_failure_source"),
                "safe_failure_error_category": safe_failure_payload.get("error_category"),
                "safe_failure_missing": _string_list(safe_failure_payload.get("missing")),
                "safe_failure_searched": _string_list(safe_failure_payload.get("searched")),
                "failure_attribution_status": failure_attribution.get("status"),
                "failure_attribution_reason": failure_attribution.get("reason"),
                "failure_attribution_relevant_blockers": _string_list(
                    failure_attribution.get("relevant_blockers")
                ),
                "failure_attribution_relevant_warnings": _string_list(
                    failure_attribution.get("relevant_warnings")
                ),
                "failure_attribution_unmapped_expected_domains": _string_list(
                    failure_attribution.get("unmapped_expected_domains")
                ),
            }
        )

    return details


def build_authority_gap_report(
    *,
    local_benchmark_payload: dict[str, Any],
    local_readiness_census_payload: dict[str, Any],
) -> dict[str, Any]:
    results = local_benchmark_payload.get("results") or []
    organizations = local_readiness_census_payload.get("organizations") or []
    selected_local_organization_id = local_readiness_census_payload.get("selected_local_organization_id")
    selected_local_org = next(
        (
            organization
            for organization in organizations
            if isinstance(organization, dict)
            and organization.get("organization_id") == selected_local_organization_id
        ),
        {},
    )
    benchmark_ready_organization_ids = list(
        local_readiness_census_payload.get("benchmark_ready_organization_ids") or []
    )
    common_blockers = _derive_common_blockers(local_readiness_census_payload)

    surface_gaps: list[dict[str, Any]] = []
    for surface_definition in FIRST_WAVE_SURFACE_DEFINITIONS:
        surface_results = [
            result
            for result in results
            if isinstance(result, dict) and _surface_matches_result(surface_definition, result)
        ]
        if not surface_results:
            continue

        failed_results = [result for result in surface_results if not result.get("passed")]
        failed_checks = sorted(
            {
                failed_check
                for result in failed_results
                for failed_check in (result.get("failed_checks") or [])
            }
        )
        benchmark_ids = sorted(result.get("benchmark_id") for result in surface_results)
        failed_benchmark_ids = sorted(result.get("benchmark_id") for result in failed_results)
        passed_benchmark_ids = sorted(
            result.get("benchmark_id") for result in surface_results if result.get("passed")
        )
        total_cases = len(surface_results)
        failed_cases = len(failed_results)
        pass_rate = ((total_cases - failed_cases) / total_cases) if total_cases else 0.0
        failed_case_details = _build_failed_case_details(failed_results)
        failure_attribution_summary = _summarize_failure_attributions(failed_results)
        safe_failure_sources = sorted(
            {
                str(source)
                for result in failed_results
                for source in [result.get("safe_failure_source")]
                if isinstance(source, str) and source.strip()
            }
        )
        safe_failure_error_categories = sorted(
            {
                str(error_category)
                for result in failed_results
                for payload in [result.get("safe_failure_payload")]
                if isinstance(payload, dict)
                for error_category in [payload.get("error_category")]
                if isinstance(error_category, str) and error_category.strip()
            }
        )

        surface_gaps.append(
            {
                "surface_key": surface_definition["surface_key"],
                "surface_label": surface_definition["surface_label"],
                "trust_status": surface_definition["trust_status"],
                "benchmark_ids": benchmark_ids,
                "question_families": sorted(
                    {
                        result.get("question_family")
                        for result in surface_results
                        if isinstance(result.get("question_family"), str)
                    }
                ),
                "expected_functions": sorted(
                    {
                        result.get("expected_function")
                        for result in surface_results
                        if isinstance(result.get("expected_function"), str)
                    }
                ),
                "total_cases": total_cases,
                "failed_cases": failed_cases,
                "pass_rate": round(pass_rate, 4),
                "failed_benchmark_ids": failed_benchmark_ids,
                "passed_benchmark_ids": passed_benchmark_ids,
                "failed_checks": failed_checks,
                "safe_failure_sources": safe_failure_sources,
                "safe_failure_error_categories": safe_failure_error_categories,
                "failure_attribution_statuses": sorted(failure_attribution_summary),
                "failure_attribution_summary": failure_attribution_summary,
                "failed_case_details": failed_case_details,
                "selected_local_org_status": selected_local_org.get("runtime_status"),
                "selected_local_org_blockers": selected_local_org.get("readiness_blockers", []),
                "selected_local_org_warnings": selected_local_org.get("readiness_warnings", []),
                "common_blockers_across_blocked_orgs": common_blockers,
                "benchmark_ready_local_org_count": len(benchmark_ready_organization_ids),
                "benchmark_ready_organization_ids": benchmark_ready_organization_ids,
                "gap_status": _surface_gap_status(
                    failed_cases=failed_cases,
                    benchmark_ready_organization_ids=benchmark_ready_organization_ids,
                    selected_local_org_status=selected_local_org.get("runtime_status"),
                ),
            }
        )

    overall_gap_status = "clear"
    if not benchmark_ready_organization_ids:
        overall_gap_status = "no_benchmark_ready_local_org"
    elif selected_local_org.get("runtime_status") == "blocked":
        overall_gap_status = "selected_local_org_blocked"
    elif local_benchmark_payload.get("failed_cases", 0):
        overall_gap_status = "surface_failures_present"

    return {
        "generated_at": _iso_now(),
        "runtime_path": "local",
        "overall_gap_status": overall_gap_status,
        "selected_local_organization_id": selected_local_organization_id,
        "local_organization_selection": local_readiness_census_payload.get(
            "local_organization_selection",
            {},
        ),
        "organizations_scanned": local_readiness_census_payload.get("organizations_scanned"),
        "benchmark_ready_organization_ids": benchmark_ready_organization_ids,
        "benchmark_ready_demo_organization_ids": local_readiness_census_payload.get(
            "benchmark_ready_demo_organization_ids",
            [],
        ),
        "benchmark_ready_non_demo_organization_ids": local_readiness_census_payload.get(
            "benchmark_ready_non_demo_organization_ids",
            [],
        ),
        "blocked_organization_ids": local_readiness_census_payload.get(
            "blocked_organization_ids",
            [],
        ),
        "least_blocked_local_organization": local_readiness_census_payload.get(
            "least_blocked_local_organization"
        ),
        "common_blockers_across_blocked_orgs": common_blockers,
        "policy_guidance": local_readiness_census_payload.get("policy_guidance", []),
        "selected_local_organization_remediation": local_readiness_census_payload.get(
            "selected_local_organization_remediation",
            [],
        ),
        "selected_local_org_blockers": selected_local_org.get("readiness_blockers", []),
        "selected_local_org_warnings": selected_local_org.get("readiness_warnings", []),
        "surface_gaps": surface_gaps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate REEVU authority-gap report.")
    parser.add_argument(
        "--benchmark-artifact",
        default="test_reports/reevu_real_question_local.json",
        help="Path to the local real-question benchmark artifact",
    )
    parser.add_argument(
        "--readiness-census-artifact",
        default="test_reports/reevu_local_readiness_census.json",
        help="Path to the local readiness census artifact",
    )
    parser.add_argument(
        "--json-output",
        default="test_reports/reevu_authority_gap_report.json",
        help="Path to write the authority-gap JSON artifact",
    )
    args = parser.parse_args()

    benchmark_artifact = Path(args.benchmark_artifact)
    readiness_census_artifact = Path(args.readiness_census_artifact)
    json_output = Path(args.json_output)

    report = build_authority_gap_report(
        local_benchmark_payload=_load_json(benchmark_artifact),
        local_readiness_census_payload=_load_json(readiness_census_artifact),
    )

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("REEVU Authority-Gap Report")
    print(f"  overall gap status: {report['overall_gap_status']}")
    print(f"  selected local org: {report['selected_local_organization_id']}")
    print(f"  organizations scanned: {report['organizations_scanned']}")
    print(
        "  benchmark-ready local orgs: "
        + (", ".join(str(org_id) for org_id in report["benchmark_ready_organization_ids"]) or "none")
    )
    print(
        "  common blockers across blocked orgs: "
        + (", ".join(report["common_blockers_across_blocked_orgs"]) or "none")
    )
    print(f"  wrote JSON: {json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())