"""Shared plan-summary helpers for REEVU tool handlers."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.modules.ai.services.tool_query_helpers import (
    _dedupe_string_values,
    _sample_record_identifiers,
    _sample_scalar_values,
)


TRUSTED_CONTRACT_PLAN_DESCRIPTIONS: dict[str, str] = {
    "compare_germplasm": "Resolve grounded phenotype evidence and compare germplasm side by side",
    "get_germplasm_details": "Resolve a grounded germplasm record and linked observations",
    "get_trait_summary": "Summarize phenotype traits for a grounded germplasm scope",
    "get_trial_results": "Resolve one authoritative trial summary and linked rankings",
    "get_marker_associations": "Resolve one authoritative genomics trait and linked marker evidence",
    "calculate_breeding_value": "Run deterministic breeding-value retrieval and compute steps",
}


TRUSTED_CONTRACT_EXPECTED_OUTPUTS: dict[str, list[str]] = {
    "compare_germplasm": ["comparison", "germplasm", "interpretation"],
    "get_germplasm_details": ["germplasm", "observations"],
    "get_trait_summary": ["trait_summary", "interpretation"],
    "get_trial_results": ["trial", "top_performers", "trait_summary"],
    "get_marker_associations": ["qtls", "marker_associations"],
    "calculate_breeding_value": ["breeding_values"],
}


def _build_cross_domain_plan_execution_summary(
    *,
    plan: Any,
    requested_domains: set[str],
    result_presence: dict[str, bool],
    results: dict[str, Any],
    trait_query: str | None,
    germplasm_query: str | None,
    crop_query: str | None,
    seedlot_query: str | None,
    resolved_location_query: str | None,
    resolved_study_ids: list[str],
    weather_resolution_error: str | None,
    weather_service_available: bool,
    recommendation_candidates: list[dict[str, Any]] | None = None,
    insights: list[dict[str, Any]] | None = None,
    missing_domains: list[str] | None = None,
) -> dict[str, Any]:
    recommendation_candidates = recommendation_candidates or []
    insights = insights or []
    genomics = results.get("genomics") or {}

    def add_output(
        *,
        actual_outputs: list[str],
        output_counts: dict[str, int],
        output_entity_ids: dict[str, Any],
        name: str,
        count: int,
        identifiers: list[str] | None = None,
    ) -> None:
        if count <= 0:
            return

        actual_outputs.append(name)
        output_counts[name] = count
        if identifiers:
            output_entity_ids[name] = identifiers

    steps: list[dict[str, Any]] = []
    for step in plan.steps:
        actual_outputs: list[str] = []
        output_counts: dict[str, int] = {}
        output_entity_ids: dict[str, Any] = {}
        output_metadata: dict[str, Any] = {}
        compute_methods: list[str] = []
        services: list[str] = []

        if step.domain == "breeding":
            services = _dedupe_string_values(
                [
                    "trait_search_service.search" if trait_query else None,
                    (
                        "germplasm_search_service.search"
                        if germplasm_query or trait_query or crop_query
                        else None
                    ),
                    (
                        "observation_search_service.get_by_germplasm"
                        if results.get("germplasm") and results.get("observations")
                        else None
                    ),
                    "seedlot_search_service.search" if seedlot_query or germplasm_query else None,
                ]
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="traits",
                count=len(results.get("traits") or []),
                identifiers=_sample_record_identifiers(results.get("traits"), keys=("id",)),
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="germplasm",
                count=len(results.get("germplasm") or []),
                identifiers=_sample_record_identifiers(
                    results.get("germplasm"),
                    keys=("accession", "id"),
                ),
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="observations",
                count=len(results.get("observations") or []),
                identifiers=_sample_record_identifiers(
                    results.get("observations"),
                    keys=("observation_db_id", "id"),
                ),
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="seedlots",
                count=len(results.get("seedlots") or []),
                identifiers=_sample_record_identifiers(
                    results.get("seedlots"),
                    keys=("seedlot_db_id", "id"),
                ),
            )
        elif step.domain == "trials":
            services = _dedupe_string_values(
                [
                    "trial_search_service.search" if "trials" in requested_domains else None,
                    "trial_search_service.get_by_id" if resolved_study_ids else None,
                    "observation_search_service.search" if resolved_study_ids else None,
                ]
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="trials",
                count=len(results.get("trials") or []),
                identifiers=_sample_record_identifiers(
                    results.get("trials"),
                    keys=("trial_db_id", "id"),
                ),
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="study_ids",
                count=len(resolved_study_ids),
                identifiers=_sample_scalar_values(resolved_study_ids),
            )
            if resolved_study_ids:
                add_output(
                    actual_outputs=actual_outputs,
                    output_counts=output_counts,
                    output_entity_ids=output_entity_ids,
                    name="observations",
                    count=len(results.get("observations") or []),
                    identifiers=_sample_record_identifiers(
                        results.get("observations"),
                        keys=("observation_db_id", "id"),
                    ),
                )
        elif step.domain == "weather":
            services = _dedupe_string_values(
                [
                    "location_search_service.search" if resolved_location_query else None,
                    "weather_service.get_forecast" if "weather" in requested_domains else None,
                ]
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="locations",
                count=len(results.get("locations") or []),
                identifiers=_sample_record_identifiers(
                    results.get("locations"),
                    keys=("location_db_id", "id"),
                ),
            )
            if results.get("weather"):
                add_output(
                    actual_outputs=actual_outputs,
                    output_counts=output_counts,
                    output_entity_ids=output_entity_ids,
                    name="weather",
                    count=1,
                )
                output_metadata["weather_source"] = (results.get("weather") or {}).get("source")
        elif step.domain == "genomics":
            services = _dedupe_string_values(
                [
                    "QTLMappingService.get_traits" if "genomics" in requested_domains else None,
                    "QTLMappingService.list_qtls" if "genomics" in requested_domains else None,
                    "QTLMappingService.get_gwas_results" if "genomics" in requested_domains else None,
                ]
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="qtls",
                count=len(genomics.get("qtls") or []),
                identifiers=_sample_record_identifiers(genomics.get("qtls"), keys=("qtl_id", "id")),
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="marker_associations",
                count=len(genomics.get("associations") or []),
                identifiers=_sample_record_identifiers(
                    genomics.get("associations"),
                    keys=("marker_name", "id"),
                ),
            )
            if genomics.get("trait"):
                output_metadata["trait"] = genomics.get("trait")
            matched_trait_candidates = _sample_scalar_values(
                (genomics.get("summary") or {}).get("matched_trait_candidates") or []
            )
            if matched_trait_candidates:
                output_metadata["matched_trait_candidates"] = matched_trait_candidates
        elif step.domain == "protocols":
            services = _dedupe_string_values(
                ["speed_breeding_service.get_protocols" if "protocols" in requested_domains else None]
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="protocols",
                count=len(results.get("protocols") or []),
                identifiers=_sample_record_identifiers(results.get("protocols"), keys=("id",)),
            )
        elif step.domain == "analytics":
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="insights",
                count=len(insights),
                identifiers=_sample_record_identifiers(insights, keys=("type",), limit=5),
            )
            add_output(
                actual_outputs=actual_outputs,
                output_counts=output_counts,
                output_entity_ids=output_entity_ids,
                name="recommendations",
                count=len(recommendation_candidates),
                identifiers=_sample_record_identifiers(
                    recommendation_candidates,
                    keys=("candidate",),
                    limit=5,
                ),
            )
            if recommendation_candidates:
                compute_methods.append("fn:cross_domain_recommendation_ranker")

        completed = bool(result_presence.get(step.domain, False))
        step_summary: dict[str, Any] = {
            "step_id": step.step_id,
            "domain": step.domain,
            "description": step.description,
            "prerequisites": list(step.prerequisites),
            "expected_outputs": list(step.expected_outputs),
            "deterministic": step.deterministic,
            "completed": completed,
            "status": "completed" if completed else "missing",
            "actual_outputs": actual_outputs,
            "services": services,
            "output_counts": output_counts,
        }
        if output_entity_ids:
            step_summary["output_entity_ids"] = output_entity_ids
        if output_metadata:
            step_summary["output_metadata"] = output_metadata
        if compute_methods:
            step_summary["compute_methods"] = compute_methods

        if not completed:
            missing_reason = {
                "breeding": "no grounded breeding evidence matched the query scope",
                "trials": "no trial evidence matched the query scope",
                "weather": (
                    weather_resolution_error
                    or (
                        "weather service is unavailable"
                        if not weather_service_available
                        else "no grounded weather evidence matched the query scope"
                    )
                ),
                "genomics": "no trait-linked genomics evidence matched the query",
                "protocols": "no protocol evidence matched the query scope",
                "analytics": "no grounded cross-domain insights were produced",
            }.get(step.domain)
            if missing_reason:
                step_summary["missing_reason"] = missing_reason

        steps.append(step_summary)

    plan_execution_summary = {
        "plan_id": plan.plan_id,
        "is_compound": plan.is_compound,
        "domains_involved": list(plan.domains_involved),
        "total_steps": plan.total_steps,
        "steps": steps,
    }
    if plan.metadata:
        plan_execution_summary["metadata"] = dict(plan.metadata)
    if missing_domains:
        plan_execution_summary["missing_domains"] = list(missing_domains)

    return plan_execution_summary


def _build_single_contract_plan_execution_summary(
    *,
    function_name: str,
    domain: str,
    domains_involved: list[str] | None = None,
    completed: bool,
    services: list[str] | None = None,
    actual_outputs: list[str] | None = None,
    output_counts: dict[str, int] | None = None,
    output_entity_ids: dict[str, Any] | None = None,
    output_metadata: dict[str, Any] | None = None,
    compute_methods: list[str] | None = None,
    missing_reason: str | None = None,
    expected_outputs: list[str] | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cleaned_output_counts = {
        str(key): int(value)
        for key, value in (output_counts or {}).items()
        if isinstance(value, (int, float)) and int(value) > 0
    }
    cleaned_output_entity_ids = {
        str(key): value
        for key, value in (output_entity_ids or {}).items()
        if value not in (None, [], {})
    }
    cleaned_output_metadata = {
        str(key): value
        for key, value in (output_metadata or {}).items()
        if value not in (None, [], {})
    }
    plan_metadata = {
        "contract_function": function_name,
        "execution_scope": "trusted_contract",
    }
    if metadata:
        plan_metadata.update(
            {
                str(key): value
                for key, value in metadata.items()
                if value not in (None, [], {})
            }
        )
    involved_domains = _dedupe_string_values(domains_involved or [domain])
    if not involved_domains:
        involved_domains = [domain]

    step_summary: dict[str, Any] = {
        "step_id": "step-1",
        "domain": domain,
        "description": description or TRUSTED_CONTRACT_PLAN_DESCRIPTIONS.get(function_name, f"Execute {function_name}"),
        "prerequisites": [],
        "expected_outputs": list(expected_outputs or TRUSTED_CONTRACT_EXPECTED_OUTPUTS.get(function_name, [])),
        "deterministic": function_name.startswith(("calculate_", "analyze_", "predict_", "compute_", "estimate_")),
        "completed": completed,
        "status": "completed" if completed else "missing",
        "actual_outputs": _dedupe_string_values(list(actual_outputs or [])),
        "services": _dedupe_string_values(list(services or [])),
        "output_counts": cleaned_output_counts,
    }
    if cleaned_output_entity_ids:
        step_summary["output_entity_ids"] = cleaned_output_entity_ids
    if cleaned_output_metadata:
        step_summary["output_metadata"] = cleaned_output_metadata
    if compute_methods:
        step_summary["compute_methods"] = _dedupe_string_values(list(compute_methods))
    if missing_reason:
        step_summary["missing_reason"] = missing_reason

    plan_execution_summary = {
        "plan_id": f"plan-{uuid4().hex[:8]}",
        "is_compound": False,
        "domains_involved": involved_domains,
        "total_steps": 1,
        "metadata": plan_metadata,
        "steps": [step_summary],
    }
    if not completed:
        plan_execution_summary["missing_domains"] = involved_domains

    return plan_execution_summary


def _with_plan_execution_summary(
    payload: dict[str, Any],
    plan_execution_summary: dict[str, Any],
) -> dict[str, Any]:
    response = dict(payload)
    retrieval_audit = response.get("retrieval_audit")
    if isinstance(retrieval_audit, dict):
        response["retrieval_audit"] = {
            **retrieval_audit,
            "plan": plan_execution_summary,
        }
    response["plan_execution_summary"] = plan_execution_summary
    return response