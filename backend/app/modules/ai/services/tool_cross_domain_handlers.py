"""Extracted cross-domain handler family for the REEVU function executor.

This module keeps the cross-domain query path out of tools.py while still
receiving shared helpers and runtime surfaces from that module. The slice stays
behavior-preserving, avoids new cycles, and keeps the executor dispatch stable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.modules.ai.services.reevu.planner import ReevuPlanner
from app.modules.ai.services.reevu.step_executor import ExecutionOutcome, StepExecutor
from app.schemas.cross_domain_query_contract import CrossDomainQueryContractMetadata


@dataclass(slots=True)
class CrossDomainHandlerSharedContext:
    trial_phenotype_environment_tokens: tuple[str, ...]
    min_recommendation_domains: int
    get_qtl_mapping_service: Any
    resolve_trait_query: Any
    build_cross_domain_retrieval_tables: Any
    build_cross_domain_retrieval_entities: Any
    build_cross_domain_plan_execution_summary: Any
    build_cross_domain_evidence_envelope: Any
    is_recommendation_query: Any


def _assemble_results_from_outcome(outcome: ExecutionOutcome) -> dict[str, Any]:
    """Map StepResults back into the flat results dict shape expected by the handler."""
    results: dict[str, Any] = {
        "germplasm": [],
        "trials": [],
        "observations": [],
        "protocols": [],
        "locations": [],
        "weather": None,
        "genomics": None,
        "traits": [],
        "seedlots": [],
        "cross_domain_insights": [],
    }

    for step_result in outcome.step_results:
        if step_result.status != "success":
            continue
        records = step_result.records

        if step_result.domain == "trials":
            results["trials"].extend(records.get("trials", []))
            results["locations"].extend(records.get("locations", []))
            results["observations"].extend(records.get("observations", []))
        elif step_result.domain == "breeding":
            results["germplasm"].extend(records.get("germplasm", []))
            results["observations"].extend(records.get("observations", []))
            results["traits"].extend(records.get("traits", []))
            results["seedlots"].extend(records.get("seedlots", []))
        elif step_result.domain == "weather":
            results["weather"] = records.get("weather")
        elif step_result.domain == "genomics":
            results["genomics"] = records.get("genomics")
        elif step_result.domain == "protocols":
            results["protocols"].extend(records.get("protocols", []))
        elif step_result.domain == "analytics":
            results["cross_domain_insights"].extend(records.get("insights", []))

    return results


async def handle_cross_domain(
    executor: Any,
    params: dict[str, Any],
    *,
    shared: CrossDomainHandlerSharedContext,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Execute the REEVU cross-domain query flow for FunctionExecutor."""

    org_id = params.get("organization_id", 1)
    original_query = params.get("query") or ""
    plan = ReevuPlanner().build_plan(
        original_query or "cross-domain query",
        function_call_name="cross_domain_query",
    )

    germplasm_query = params.get("germplasm")
    trait_query = params.get("trait")
    location_query = params.get("location")
    crop_query = params.get("crop")
    program_query = params.get("program")
    seedlot_query = params.get("seedlot")

    requested_domain_list = list(plan.domains_involved)

    try:
        requested_domains = set(requested_domain_list)

        # Pass requested domains to params so step handlers can access them
        params["_requested_domains"] = list(plan.domains_involved)

        step_executor = StepExecutor(
            executor=executor,
            organization_id=org_id,
            original_query=original_query,
            params=params,
        )
        outcome = await step_executor.execute_plan(plan)
        results = _assemble_results_from_outcome(outcome)

        # Extract inferred location and study IDs from step results
        inferred_location_query: str | None = None
        resolved_study_ids: list[str] = []
        weather_resolution_error: str | None = None
        weather_audit_service: str | None = None
        resolved_weather_location: dict[str, Any] | None = None

        for step_result in outcome.step_results:
            if step_result.domain == "trials" and step_result.status == "success":
                inferred_location_query = step_result.metadata.get("inferred_location_query")
                resolved_study_ids = step_result.metadata.get("resolved_study_ids", [])
            if step_result.domain == "weather" and step_result.status == "failed":
                weather_resolution_error = step_result.error_message
            if step_result.domain == "weather" and step_result.status == "success":
                weather_audit_service = "weather_service.get_forecast"
            if step_result.domain == "weather" and step_result.status == "failed":
                if step_result.error_category == "missing_service":
                    weather_audit_service = "weather_service_unavailable"
                else:
                    weather_audit_service = "weather_location_coordinate_resolution"

        # Resolve location query for downstream use
        resolved_location_query = location_query or inferred_location_query

        # Determine trial_phenotype_environment_mode for result_presence logic
        trial_phenotype_environment_mode = (
            {"breeding", "trials", "weather"}.issubset(requested_domains)
            and germplasm_query is None
            and any(
                token in original_query.lower()
                for token in shared.trial_phenotype_environment_tokens
            )
        )

        # Resolve weather location from results for retrieval audit
        if results["locations"]:
            resolved_weather_location = next(
                (
                    location
                    for location in results["locations"]
                    if location.get("latitude") is not None and location.get("longitude") is not None
                ),
                None,
            )

        insights = []

        if results["traits"]:
            traits_with_obs = set()
            for observation in results["observations"]:
                if observation.get("trait"):
                    traits_with_obs.add(observation["trait"].get("id"))

            traits_without_obs = [
                trait for trait in results["traits"] if trait["id"] not in traits_with_obs
            ]
            if traits_without_obs:
                insights.append(
                    {
                        "type": "trait_gap",
                        "message": f"{len(traits_without_obs)} traits have no observations in the queried germplasm",
                        "affected_items": [trait["name"] for trait in traits_without_obs[:5]],
                        "recommendation": "Consider phenotyping for these traits to enable selection",
                    }
                )

        germplasm_with_obs = set()
        for observation in results["observations"]:
            if observation.get("germplasm"):
                germplasm_with_obs.add(observation["germplasm"]["id"])

        germplasm_without_obs = [
            germplasm for germplasm in results["germplasm"] if germplasm["id"] not in germplasm_with_obs
        ]
        if germplasm_without_obs:
            insights.append(
                {
                    "type": "data_gap",
                    "message": f"{len(germplasm_without_obs)} germplasm entries have no phenotypic observations recorded",
                    "affected_items": [germplasm["name"] for germplasm in germplasm_without_obs[:5]],
                    "recommendation": "Consider phenotyping these accessions to enable trait-based selection",
                }
            )

        if results["trials"]:
            trials_needing_data = [trial for trial in results["trials"] if trial.get("study_count", 0) == 0]
            if trials_needing_data:
                insights.append(
                    {
                        "type": "incomplete_trial",
                        "message": f"{len(trials_needing_data)} trials have no studies/observations",
                        "affected_items": [trial["name"] for trial in trials_needing_data[:5]],
                        "recommendation": "Add studies and record observations for these trials",
                    }
                )

        if results["locations"] and results["germplasm"]:
            insights.append(
                {
                    "type": "coverage_summary",
                    "message": f"Query spans {len(results['locations'])} locations and {len(results['germplasm'])} germplasm entries",
                    "recommendation": "Consider multi-environment trials to assess G×E interactions",
                }
            )

        if results["weather"] and results["trials"] and results["germplasm"]:
            insights.append(
                {
                    "type": "joined_breeding_trial_environment",
                    "message": (
                        f"Joined breeding, trial, and weather evidence for {len(results['trials'])} "
                        f"trials and {len(results['germplasm'])} germplasm entries."
                    ),
                    "recommendation": "Review trial performance together with current weather risk before selection decisions.",
                }
            )

        if results["trials"] and results["germplasm"] and results["observations"] and not results["weather"]:
            insights.append(
                {
                    "type": "joined_breeding_trial",
                    "message": (
                        f"Joined breeding and trial evidence for {len(results['germplasm'])} "
                        f"germplasm entries across {len(results['trials'])} trial(s)."
                    ),
                    "recommendation": "Review observed field performance together with the matched trial set before selecting breeding lines.",
                }
            )

        if results["weather"] and results["trials"] and results["observations"]:
            insights.append(
                {
                    "type": "joined_trial_phenotype_environment",
                    "message": (
                        f"Joined trial, phenotype, and weather evidence for {len(results['trials'])} "
                        f"trials using {len(results['observations'])} linked observations."
                    ),
                    "recommendation": "Review observed field performance together with current weather conditions before interpreting trial outcomes.",
                }
            )

        if results["genomics"] and results["germplasm"]:
            insights.append(
                {
                    "type": "joined_breeding_genomics",
                    "message": (
                        f"Joined breeding and genomics evidence for {len(results['germplasm'])} "
                        f"germplasm entries using trait '{results['genomics']['trait']}'."
                    ),
                    "recommendation": "Review trait-linked QTL and marker evidence together with candidate germplasm before selection decisions.",
                }
            )

        if results["protocols"] and results["germplasm"] and results["traits"]:
            insights.append(
                {
                    "type": "joined_germplasm_trait_protocol",
                    "message": (
                        f"Joined germplasm, trait, and protocol evidence for {len(results['germplasm'])} "
                        f"germplasm entries using {len(results['protocols'])} protocols."
                    ),
                    "recommendation": "Review protocol conditions alongside germplasm and target traits before selecting an accelerated breeding workflow.",
                }
            )

        if results["seedlots"]:
            low_quantity = [seedlot for seedlot in results["seedlots"] if seedlot.get("amount", 0) < 100]
            if low_quantity:
                insights.append(
                    {
                        "type": "seed_availability",
                        "message": f"{len(low_quantity)} seedlots have low seed quantity (<100)",
                        "affected_items": [seedlot.get("name", seedlot["id"]) for seedlot in low_quantity[:5]],
                        "recommendation": "Consider seed multiplication before large-scale trials",
                    }
                )

        results["cross_domain_insights"] = insights
        recommendation_candidates: list[dict[str, Any]] = []
        is_recommendation_query = shared.is_recommendation_query(original_query)
        if (
            is_recommendation_query
            and len(requested_domains) >= shared.min_recommendation_domains
            and results["germplasm"]
        ):
            for germplasm in results["germplasm"]:
                accession = germplasm.get("accession") or germplasm.get("id")
                evidence_refs = [f"db:germplasm:{accession}"] if accession else []
                rationale_parts = []
                score = 0.5

                linked_observations = [
                    observation
                    for observation in results["observations"]
                    if (observation.get("germplasm") or {}).get("id") == germplasm.get("id")
                ]
                if linked_observations:
                    score += 0.15
                    rationale_parts.append(
                        f"{len(linked_observations)} linked observations support this candidate"
                    )
                    for observation in linked_observations[:2]:
                        observation_ref = observation.get("observation_db_id") or observation.get("id")
                        if observation_ref:
                            evidence_refs.append(f"db:observation:{observation_ref}")

                if results["trials"]:
                    score += 0.1
                    rationale_parts.append(
                        f"trial evidence available from {len(results['trials'])} trial(s)"
                    )
                    trial_ref = results["trials"][0].get("trial_db_id") or results["trials"][0].get("id")
                    if trial_ref:
                        evidence_refs.append(f"db:trial:{trial_ref}")

                if results["weather"]:
                    score += 0.05
                    rationale_parts.append("weather context is available for the recommendation")
                    evidence_refs.append("fn:weather.forecast")

                if results["genomics"]:
                    score += 0.1
                    rationale_parts.append(
                        f"genomics evidence is available for trait '{results['genomics']['trait']}'"
                    )
                    if results["genomics"].get("qtls"):
                        qtl_id = results["genomics"]["qtls"][0].get("qtl_id")
                        if qtl_id:
                            evidence_refs.append(f"db:qtl:{qtl_id}")

                if results["protocols"]:
                    score += 0.1
                    rationale_parts.append(
                        f"{len(results['protocols'])} protocol(s) match the requested crop or workflow"
                    )
                    protocol_ref = results["protocols"][0].get("id")
                    if protocol_ref:
                        evidence_refs.append(f"db:protocol:{protocol_ref}")

                recommendation_candidates.append(
                    {
                        "candidate": germplasm.get("name") or accession or "unknown-germplasm",
                        "score": round(min(score, 0.95), 2),
                        "rationale": "; ".join(rationale_parts)
                        or "Multi-domain evidence was retrieved for this candidate.",
                        "evidence_refs": list(dict.fromkeys(ref for ref in evidence_refs if ref)),
                        "calculation_method_refs": ["fn:cross_domain_recommendation_ranker"],
                    }
                )

            if recommendation_candidates:
                results["recommendations"] = recommendation_candidates
                insights.append(
                    {
                        "type": "multi_domain_recommendation",
                        "message": (
                            f"Generated {len(recommendation_candidates)} recommendation candidate(s) "
                            "using evidence from more than one domain."
                        ),
                        "recommendation": recommendation_candidates[0]["rationale"],
                    }
                )

        result_presence = {
            "breeding": bool(
                results["germplasm"]
                or results["observations"]
                or results["seedlots"]
                or (results["traits"] and not trial_phenotype_environment_mode)
            ),
            "trials": bool(results["trials"]),
            "weather": bool(results["weather"]),
            "genomics": bool(results["genomics"]),
            "protocols": bool(results["protocols"]),
            "analytics": bool(insights),
        }
        missing_domains = [
            domain
            for domain in plan.domains_involved
            if domain in result_presence and not result_presence[domain]
        ]
        plan_execution_summary = shared.build_cross_domain_plan_execution_summary(
            plan=plan,
            requested_domains=requested_domains,
            result_presence=result_presence,
            results=results,
            trait_query=trait_query,
            germplasm_query=germplasm_query,
            crop_query=crop_query,
            seedlot_query=seedlot_query,
            resolved_location_query=resolved_location_query,
            resolved_study_ids=resolved_study_ids,
            weather_resolution_error=weather_resolution_error,
            weather_service_available=bool(executor.weather_service),
            recommendation_candidates=recommendation_candidates,
            insights=insights,
            missing_domains=missing_domains,
        )
        if missing_domains:
            searched_services = [
                service
                for service in [
                    "germplasm_search_service.search" if executor.germplasm_search_service else None,
                    "trait_search_service.search" if trait_query else None,
                    "trial_search_service.search" if "trials" in requested_domains else None,
                    "location_search_service.search"
                    if location_query and ("trials" in requested_domains or "weather" in requested_domains)
                    else None,
                    weather_audit_service,
                    "QTLMappingService.get_traits" if "genomics" in requested_domains else None,
                    "QTLMappingService.list_qtls" if "genomics" in requested_domains else None,
                    "QTLMappingService.get_gwas_results" if "genomics" in requested_domains else None,
                    "speed_breeding_service.get_protocols" if "protocols" in requested_domains else None,
                    "observation_search_service.search" if trial_phenotype_environment_mode else None,
                ]
                if service is not None
            ]
            next_steps = [
                "Add or verify records in the missing domains and retry.",
                "Narrow the compound query to a location, crop, or trait with known data.",
            ]
            missing_context: list[dict[str, Any]] = []
            if "weather" in missing_domains and weather_resolution_error:
                missing_context.append(
                    {
                        "domain": "weather",
                        "location_query": resolved_location_query,
                        "reason": weather_resolution_error,
                    }
                )
                weather_next_step = {
                    "no location query was provided": "Specify a location so REEVU can resolve coordinates and call the real weather provider.",
                    "resolved location has no stored coordinates": "Use a location with stored coordinates so REEVU can call the real weather provider.",
                    "no matching location was found": "Retry with a location that exists in BijMantra so REEVU can resolve coordinates for the real weather provider.",
                    "weather provider request failed": "Retry once the live weather provider is available for the resolved location.",
                }.get(weather_resolution_error)
                if weather_next_step:
                    next_steps.insert(0, weather_next_step)
            return {
                "success": False,
                "error": f"Cross-domain query could not retrieve requested domains: {', '.join(missing_domains)}",
                "message": (
                    "The compound query was recognized, but not enough domain evidence was retrieved "
                    "to produce a grounded joined response."
                ),
                "plan_execution_summary": plan_execution_summary,
                "retrieval_audit": {
                    "services": searched_services,
                    "tables": shared.build_cross_domain_retrieval_tables(results),
                    "entities": shared.build_cross_domain_retrieval_entities(
                        original_query=original_query,
                        requested_domains=requested_domain_list,
                        result_presence=result_presence,
                        results=results,
                        germplasm_query=germplasm_query,
                        trait_query=trait_query,
                        location_query=location_query,
                        inferred_location_query=inferred_location_query,
                        crop_query=crop_query,
                        program_query=program_query,
                        seedlot_query=seedlot_query,
                        resolved_study_ids=resolved_study_ids,
                        missing_domains=missing_domains,
                        resolved_weather_location=resolved_weather_location,
                        weather_resolution_error=weather_resolution_error,
                    ),
                    "scope": {
                        "organization_id": org_id,
                        "plan_id": plan.plan_id,
                    },
                    "plan": plan_execution_summary,
                    "step_execution_trace": outcome.step_execution_trace,
                },
                "safe_failure": {
                    "error_category": "insufficient_retrieval_scope",
                    "searched": searched_services,
                    "missing": missing_domains,
                    "missing_context": missing_context,
                    "next_steps": next_steps,
                },
            }

        confidence_score = round(
            min(
                0.55
                + (0.1 if result_presence["breeding"] else 0.0)
                + (0.1 if result_presence["trials"] else 0.0)
                + (0.1 if result_presence["weather"] else 0.0)
                + (0.1 if result_presence["genomics"] else 0.0)
                + (0.05 if result_presence["analytics"] else 0.0),
                0.9,
            ),
            2,
        )
        evidence_envelope = shared.build_cross_domain_evidence_envelope(
            query=original_query or "cross-domain query",
            germplasm=results["germplasm"],
            trials=results["trials"],
            observations=results["observations"],
            protocols=results["protocols"],
            locations=results["locations"],
            weather_present=bool(results["weather"]),
            genomics=results["genomics"],
            domains_involved=plan.domains_involved,
            confidence_score=confidence_score,
        )

        contract_metadata = CrossDomainQueryContractMetadata(
            confidence_score=confidence_score,
            calculation_method_refs=(
                ["fn:cross_domain_recommendation_ranker"] if recommendation_candidates else []
            ),
        )

        return {
            "success": True,
            "function": "cross_domain_query",
            "result_type": "cross_domain_results",
            "data": {
                "results": results,
                "recommendations": recommendation_candidates,
                "summary": {
                    "germplasm_count": len(results["germplasm"]),
                    "trial_count": len(results["trials"]),
                    "observation_count": len(results["observations"]),
                    "protocol_count": len(results["protocols"]),
                    "location_count": len(results["locations"]),
                    "weather_count": 1 if results["weather"] else 0,
                    "genomics_qtl_count": len((results["genomics"] or {}).get("qtls", [])),
                    "genomics_association_count": len((results["genomics"] or {}).get("associations", [])),
                    "trait_count": len(results["traits"]),
                    "seedlot_count": len(results["seedlots"]),
                    "recommendation_count": len(recommendation_candidates),
                    "insight_count": len(insights),
                },
                "message": (
                    f"Cross-domain query returned {len(results['germplasm'])} germplasm, "
                    f"{len(results['trials'])} trials, {len(results['traits'])} traits, "
                    f"{len(results['protocols'])} protocols, "
                    f"{len((results['genomics'] or {}).get('qtls', []))} QTLs, "
                    f"{len((results['genomics'] or {}).get('associations', []))} marker associations, "
                    f"{len(recommendation_candidates)} recommendations, and {len(insights)} insights"
                ),
            },
            "evidence_refs": [
                ref["entity_id"] for ref in evidence_envelope.get("evidence_refs", [])
            ],
            "calculation_ids": [
                step["step_id"] for step in evidence_envelope.get("calculation_steps", [])
            ],
            "calculation_method_refs": contract_metadata.calculation_method_refs,
            "response_contract_version": contract_metadata.response_contract_version,
            "trust_surface": contract_metadata.trust_surface,
            "data_source": contract_metadata.data_source,
            "schema_version": contract_metadata.schema_version,
            "confidence_score": contract_metadata.confidence_score,
            "evidence_envelope": evidence_envelope,
            "retrieval_audit": {
                "services": [
                    service
                    for service in [
                        "germplasm_search_service.search",
                        "trial_search_service.search" if results["trials"] else None,
                        "location_search_service.search" if results["locations"] else None,
                        "trait_search_service.search" if trait_query else None,
                        "weather_service.get_forecast" if results["weather"] else None,
                        "QTLMappingService.get_traits" if "genomics" in requested_domains else None,
                        "QTLMappingService.list_qtls" if results["genomics"] else None,
                        "QTLMappingService.get_gwas_results" if results["genomics"] else None,
                        "speed_breeding_service.get_protocols" if results["protocols"] else None,
                        "observation_search_service.search" if results["observations"] else None,
                    ]
                    if service is not None
                ],
                "tables": shared.build_cross_domain_retrieval_tables(results),
                "entities": shared.build_cross_domain_retrieval_entities(
                    original_query=original_query,
                    requested_domains=requested_domain_list,
                    result_presence=result_presence,
                    results=results,
                    germplasm_query=germplasm_query,
                    trait_query=trait_query,
                    location_query=location_query,
                    inferred_location_query=inferred_location_query,
                    crop_query=crop_query,
                    program_query=program_query,
                    seedlot_query=seedlot_query,
                    resolved_study_ids=resolved_study_ids,
                    resolved_weather_location=resolved_weather_location,
                ),
                "scope": {
                    "organization_id": org_id,
                    "plan_id": plan.plan_id,
                },
                "plan": plan_execution_summary,
                "step_execution_trace": outcome.step_execution_trace,
            },
            "plan_execution_summary": plan_execution_summary,
            "demo": False,
        }
    except Exception as exc:
        logger.error(f"Cross-domain query failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "message": "Failed to execute cross-domain query",
        }