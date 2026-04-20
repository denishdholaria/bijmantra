"""Extracted get-handler family for the REEVU function executor.

This module intentionally receives shared helpers and imported service references
from tools.py so the first extraction slice can stay narrow without introducing
cycles or breaking existing monkeypatch surfaces in focused tests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.schemas.genomics_marker_lookup_contract import GenomicsMarkerLookupContractMetadata
from app.schemas.germplasm_lookup_contract import GermplasmLookupContractMetadata
from app.schemas.phenotype_comparison_contract import PhenotypeComparisonContractMetadata


@dataclass(slots=True)
class GetHandlerSharedContext:
    build_single_contract_plan_execution_summary: Any
    with_plan_execution_summary: Any
    get_germplasm_identifier: Any
    resolve_trait_query: Any
    derive_germplasm_data_age_seconds: Any
    derive_germplasm_confidence: Any
    build_germplasm_evidence_envelope: Any
    derive_genomics_lookup_confidence: Any
    build_genomics_evidence_envelope: Any
    sample_record_identifiers: Any
    sample_scalar_values: Any
    dedupe_string_values: Any
    get_trial_summary: Any
    get_comparison_statistics: Any
    get_qtl_mapping_service: Any
    observation_search_service: Any
    program_search_service: Any
    seedlot_search_service: Any
    trait_search_service: Any
    cross_domain_gdd_service_cls: Any


async def handle_get(
    executor: Any,
    function_name: str,
    params: dict[str, Any],
    *,
    shared: GetHandlerSharedContext,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Handle get_* functions for FunctionExecutor."""

    _build_single_contract_plan_execution_summary = (
        shared.build_single_contract_plan_execution_summary
    )
    _with_plan_execution_summary = shared.with_plan_execution_summary
    _get_germplasm_identifier = shared.get_germplasm_identifier
    _resolve_trait_query = shared.resolve_trait_query
    _derive_germplasm_data_age_seconds = shared.derive_germplasm_data_age_seconds
    _derive_germplasm_confidence = shared.derive_germplasm_confidence
    _build_germplasm_evidence_envelope = shared.build_germplasm_evidence_envelope
    _derive_genomics_lookup_confidence = shared.derive_genomics_lookup_confidence
    _build_genomics_evidence_envelope = shared.build_genomics_evidence_envelope
    _sample_record_identifiers = shared.sample_record_identifiers
    _sample_scalar_values = shared.sample_scalar_values
    _dedupe_string_values = shared.dedupe_string_values
    get_trial_summary = shared.get_trial_summary
    get_comparison_statistics = shared.get_comparison_statistics
    get_qtl_mapping_service = shared.get_qtl_mapping_service
    observation_search_service = shared.observation_search_service
    program_search_service = shared.program_search_service
    seedlot_search_service = shared.seedlot_search_service
    trait_search_service = shared.trait_search_service
    CrossDomainGDDService = shared.cross_domain_gdd_service_cls

    if function_name == "get_germplasm_details":
        org_id = params.get("organization_id", 1)
        germplasm_id = params.get("germplasm_id") or params.get("id")
        query = params.get("query") or params.get("name") or params.get("accession")
        plan_metadata = {
            "resolution_mode": "query_lookup" if query and not germplasm_id else "identifier_lookup",
        }

        if not germplasm_id and query:
            if not executor.germplasm_search_service:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "germplasm_search_service is required to resolve germplasm queries",
                        "message": "Germplasm lookup is not available in the current REEVU runtime.",
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="breeding",
                        completed=False,
                        missing_reason="germplasm lookup runtime service is unavailable",
                        metadata=plan_metadata,
                    ),
                )

            matches = await executor.germplasm_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=str(query),
                limit=5,
            )
            if not matches:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Germplasm not found",
                        "message": f"No germplasm matched '{query}'",
                        "retrieval_audit": {
                            "services": ["germplasm_search_service.search"],
                            "tables": ["Germplasm"],
                            "entities": {
                                "query": str(query),
                                "match_count": 0,
                            },
                            "scope": {"organization_id": org_id},
                        },
                        "safe_failure": {
                            "error_category": "insufficient_retrieval_scope",
                            "searched": ["germplasm_lookup", "germplasm_search_service"],
                            "missing": ["specific germplasm identifier"],
                            "next_steps": [
                                "Provide the exact accession or germplasm ID.",
                                "Retry with a narrower germplasm name or accession query.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="breeding",
                        completed=False,
                        services=["germplasm_search_service.search"],
                        output_metadata={"query": str(query)},
                        missing_reason=f"no grounded germplasm record matched '{query}'",
                        metadata=plan_metadata,
                    ),
                )

            if len(matches) > 1:
                candidate_ids = [str(match.get("id")) for match in matches if match.get("id")]
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Ambiguous germplasm query",
                        "message": f"Multiple germplasm records matched '{query}'. Please choose one explicit accession.",
                        "candidates": matches,
                        "retrieval_audit": {
                            "services": ["germplasm_search_service.search"],
                            "tables": ["Germplasm"],
                            "entities": {
                                "query": str(query),
                                "match_count": len(matches),
                                "candidate_ids": [
                                    str(match.get("id"))
                                    for match in matches
                                    if match.get("id")
                                ],
                            },
                            "scope": {"organization_id": org_id},
                        },
                        "safe_failure": {
                            "error_category": "ambiguous_retrieval_scope",
                            "searched": ["germplasm_lookup", "germplasm_search_service"],
                            "missing": ["single authoritative germplasm match"],
                            "next_steps": [
                                "Retry with the exact accession or internal germplasm ID.",
                                "Add more identifying context such as species or origin.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="breeding",
                        completed=False,
                        services=["germplasm_search_service.search"],
                        actual_outputs=["candidate_matches"],
                        output_counts={"candidate_matches": len(matches)},
                        output_entity_ids={"candidate_matches": candidate_ids},
                        output_metadata={"query": str(query)},
                        missing_reason="multiple germplasm records matched the query; one authoritative accession is still required",
                        metadata=plan_metadata,
                    ),
                )

            germplasm_id = matches[0].get("id")
            if not germplasm_id:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Unresolvable germplasm match",
                        "message": (
                            f"Matched '{query}' to a germplasm record without an authoritative "
                            "internal germplasm identifier."
                        ),
                        "retrieval_audit": {
                            "services": ["germplasm_search_service.search"],
                            "tables": ["Germplasm"],
                            "entities": {
                                "query": str(query),
                                "match_count": len(matches),
                            },
                            "scope": {"organization_id": org_id},
                        },
                        "safe_failure": {
                            "error_category": "insufficient_retrieval_scope",
                            "searched": ["germplasm_lookup", "germplasm_search_service"],
                            "missing": ["authoritative germplasm identifier"],
                            "next_steps": [
                                "Retry with the exact internal germplasm ID.",
                                "Check the matched germplasm record quality before relying on this answer.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="breeding",
                        completed=False,
                        services=["germplasm_search_service.search"],
                        actual_outputs=["candidate_matches"],
                        output_counts={"candidate_matches": len(matches)},
                        output_metadata={"query": str(query)},
                        missing_reason="the matched germplasm record did not expose one authoritative internal identifier",
                        metadata=plan_metadata,
                    ),
                )

        if not germplasm_id:
            return _with_plan_execution_summary(
                {
                    "success": False,
                    "error": "germplasm_id is required",
                    "message": "Please specify a germplasm ID or query that resolves to one germplasm record.",
                },
                _build_single_contract_plan_execution_summary(
                    function_name=function_name,
                    domain="breeding",
                    completed=False,
                    missing_reason="a germplasm identifier or resolvable query is required before retrieval can run",
                    metadata=plan_metadata,
                ),
            )

        try:
            result = await executor.germplasm_search_service.get_by_id(
                db=executor.db,
                organization_id=org_id,
                germplasm_id=str(germplasm_id),
            )

            if not result:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Germplasm not found",
                        "message": f"No germplasm found with ID {germplasm_id}",
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="breeding",
                        completed=False,
                        services=["germplasm_search_service.get_by_id"],
                        output_metadata={"germplasm_id": str(germplasm_id)},
                        missing_reason=f"no grounded germplasm record matched identifier {germplasm_id}",
                        metadata=plan_metadata,
                    ),
                )

            observations = await observation_search_service.get_by_germplasm(
                db=executor.db,
                organization_id=org_id,
                germplasm_id=int(germplasm_id),
                limit=20,
            )
            accession = _get_germplasm_identifier(result)
            evidence_refs = [f"db:germplasm:{accession}"]
            evidence_refs.extend(
                f"db:observation:{observation.get('observation_db_id') or observation.get('id')}"
                for observation in observations[:10]
                if observation.get("observation_db_id") or observation.get("id")
            )
            data_age_seconds = _derive_germplasm_data_age_seconds(observations)
            confidence_score = _derive_germplasm_confidence(result, observations)
            contract_metadata = GermplasmLookupContractMetadata(
                confidence_score=confidence_score,
                data_age_seconds=data_age_seconds,
            )
            evidence_envelope = _build_germplasm_evidence_envelope(
                germplasm=result,
                observations=observations,
                confidence_score=confidence_score,
                data_age_seconds=data_age_seconds,
            )

            plan_execution_summary = _build_single_contract_plan_execution_summary(
                function_name=function_name,
                domain="breeding",
                completed=True,
                services=[
                    "germplasm_search_service.get_by_id",
                    "observation_search_service.get_by_germplasm",
                ],
                actual_outputs=["germplasm"] + (["observations"] if observations else []),
                output_counts={
                    "germplasm": 1,
                    "observations": len(observations),
                },
                output_entity_ids={
                    "germplasm": [accession or str(germplasm_id)],
                    "observations": _sample_record_identifiers(
                        observations,
                        keys=("observation_db_id", "id"),
                        limit=5,
                    ),
                },
                output_metadata={
                    "query": str(query) if query else None,
                    "confidence_score": contract_metadata.confidence_score,
                },
                metadata=plan_metadata,
            )

            return _with_plan_execution_summary(
                {
                    "success": True,
                    "function": function_name,
                    "result_type": "germplasm_details",
                    "data": {
                        "germplasm": result,
                        "observation_count": len(observations),
                        "observations": observations[:10],
                        "message": f"Germplasm '{result['name']}' with {len(observations)} observations",
                    },
                    "evidence_refs": evidence_refs,
                    "response_contract_version": contract_metadata.response_contract_version,
                    "trust_surface": contract_metadata.trust_surface,
                    "data_source": contract_metadata.data_source,
                    "schema_version": contract_metadata.schema_version,
                    "confidence_score": contract_metadata.confidence_score,
                    "data_age_seconds": contract_metadata.data_age_seconds,
                    "evidence_envelope": evidence_envelope,
                    "retrieval_audit": {
                        "services": [
                            "germplasm_search_service.get_by_id",
                            "observation_search_service.get_by_germplasm",
                        ],
                        "tables": ["Germplasm", "Observation", "ObservationVariable"],
                        "entities": {
                            "germplasm_id": str(germplasm_id),
                            "germplasm_accession": accession,
                        },
                        "scope": {
                            "organization_id": org_id,
                            "query": str(query) if query else None,
                        },
                    },
                    "demo": False,
                },
                plan_execution_summary,
            )
        except Exception as e:
            logger.error(f"Get germplasm details failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get germplasm details",
            }

    elif function_name == "get_trial_results":
        org_id = params.get("organization_id", 1)
        trial_id = params.get("trial_id")
        query = params.get("query") or params.get("name")
        crop = params.get("crop")
        season = params.get("season")
        location = params.get("location")
        plan_metadata = {
            "resolution_mode": "query_lookup" if query and not trial_id else "identifier_lookup",
        }

        if not trial_id and query:
            if not executor.trial_search_service:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "trial_search_service is required to resolve trial queries",
                        "message": "Trial lookup is not available in the current REEVU runtime.",
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="trials",
                        completed=False,
                        missing_reason="trial lookup runtime service is unavailable",
                        metadata=plan_metadata,
                    ),
                )

            matches = await executor.trial_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=str(query),
                crop=str(crop) if crop else None,
                season=str(season) if season else None,
                location=str(location) if location else None,
                limit=5,
            )
            if (
                not matches
                and crop
                and str(query).strip().lower() == f"{str(crop).strip().lower()} trial"
            ):
                matches = await executor.trial_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=None,
                    crop=str(crop),
                    season=str(season) if season else None,
                    location=str(location) if location else None,
                    limit=5,
                )
            if not matches:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Trial not found",
                        "message": f"No trial matched '{query}'",
                        "retrieval_audit": {
                            "services": ["trial_search_service.search"],
                            "tables": ["Trial"],
                            "entities": {
                                "query": str(query),
                                "match_count": 0,
                            },
                            "scope": {
                                "organization_id": org_id,
                                "crop": str(crop) if crop else None,
                                "season": str(season) if season else None,
                                "location": str(location) if location else None,
                            },
                        },
                        "safe_failure": {
                            "error_category": "insufficient_retrieval_scope",
                            "searched": ["trial_summary", "trial_search_service"],
                            "missing": ["specific trial identifier"],
                            "next_steps": [
                                "Provide the trial ID or exact trial name.",
                                "Narrow the question by crop, location, or season.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="trials",
                        completed=False,
                        services=["trial_search_service.search"],
                        output_metadata={
                            "query": str(query),
                            "crop": str(crop) if crop else None,
                            "season": str(season) if season else None,
                            "location": str(location) if location else None,
                        },
                        missing_reason=f"no grounded trial record matched '{query}' within the current scope",
                        metadata=plan_metadata,
                    ),
                )

            if len(matches) > 1:
                candidate_ids = [
                    str(match.get("trial_db_id") or match.get("id"))
                    for match in matches
                    if match.get("trial_db_id") or match.get("id")
                ]
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Ambiguous trial query",
                        "message": f"Multiple trials matched '{query}'. Please choose one explicit trial.",
                        "candidates": matches,
                        "retrieval_audit": {
                            "services": ["trial_search_service.search"],
                            "tables": ["Trial"],
                            "entities": {
                                "query": str(query),
                                "match_count": len(matches),
                                "candidate_ids": [
                                    str(match.get("trial_db_id") or match.get("id"))
                                    for match in matches
                                    if match.get("trial_db_id") or match.get("id")
                                ],
                            },
                            "scope": {
                                "organization_id": org_id,
                                "crop": str(crop) if crop else None,
                                "season": str(season) if season else None,
                                "location": str(location) if location else None,
                            },
                        },
                        "safe_failure": {
                            "error_category": "ambiguous_retrieval_scope",
                            "searched": ["trial_summary", "trial_search_service"],
                            "missing": ["single authoritative trial match"],
                            "next_steps": [
                                "Retry with the exact trial ID.",
                                "Specify the trial name more precisely.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="trials",
                        completed=False,
                        services=["trial_search_service.search"],
                        actual_outputs=["candidate_matches"],
                        output_counts={"candidate_matches": len(matches)},
                        output_entity_ids={"candidate_matches": candidate_ids},
                        output_metadata={
                            "query": str(query),
                            "crop": str(crop) if crop else None,
                            "season": str(season) if season else None,
                            "location": str(location) if location else None,
                        },
                        missing_reason="multiple trial records matched the query; one authoritative trial is still required",
                        metadata=plan_metadata,
                    ),
                )

            trial_id = matches[0].get("trial_db_id") or matches[0].get("id")
            if not trial_id:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Unresolvable trial match",
                        "message": (
                            f"Matched '{query}' to a trial record without an authoritative "
                            "trial identifier."
                        ),
                        "retrieval_audit": {
                            "services": ["trial_search_service.search"],
                            "tables": ["Trial"],
                            "entities": {
                                "query": str(query),
                                "match_count": len(matches),
                            },
                            "scope": {
                                "organization_id": org_id,
                                "crop": str(crop) if crop else None,
                                "season": str(season) if season else None,
                                "location": str(location) if location else None,
                            },
                        },
                        "safe_failure": {
                            "error_category": "insufficient_retrieval_scope",
                            "searched": ["trial_summary", "trial_search_service"],
                            "missing": ["authoritative trial identifier"],
                            "next_steps": [
                                "Retry with the exact trial ID.",
                                "Check the trial record quality before relying on this answer.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="trials",
                        completed=False,
                        services=["trial_search_service.search"],
                        actual_outputs=["candidate_matches"],
                        output_counts={"candidate_matches": len(matches)},
                        output_metadata={
                            "query": str(query),
                            "crop": str(crop) if crop else None,
                            "season": str(season) if season else None,
                            "location": str(location) if location else None,
                        },
                        missing_reason="the matched trial record did not expose one authoritative trial identifier",
                        metadata=plan_metadata,
                    ),
                )

        if not trial_id:
            return _with_plan_execution_summary(
                {
                    "success": False,
                    "error": "trial_id is required",
                    "message": "Please specify a trial ID or query that resolves to one trial.",
                },
                _build_single_contract_plan_execution_summary(
                    function_name=function_name,
                    domain="trials",
                    completed=False,
                    missing_reason="a trial identifier or resolvable query is required before retrieval can run",
                    metadata=plan_metadata,
                ),
            )

        try:
            summary = await get_trial_summary(
                str(trial_id),
                db=executor.db,
                organization_id=org_id,
            )
            summary_payload = summary.model_dump(mode="json")
            trial_payload = summary_payload.get("trial", {})

            plan_execution_summary = _build_single_contract_plan_execution_summary(
                function_name=function_name,
                domain="trials",
                domains_involved=[
                    "trials",
                    *(["analytics"] if summary_payload.get("topPerformers") else []),
                ],
                completed=True,
                services=["app.api.v2.trial_summary.get_trial_summary"],
                actual_outputs=_dedupe_string_values(
                    [
                        "trial",
                        "top_performers" if summary_payload.get("topPerformers") else None,
                        "trait_summary" if summary_payload.get("traitSummary") else None,
                        "location_performance" if summary_payload.get("locationPerformance") else None,
                    ]
                ),
                output_counts={
                    "trial": 1,
                    "top_performers": len(summary_payload.get("topPerformers") or []),
                    "trait_summary": len(summary_payload.get("traitSummary") or []),
                    "location_performance": len(summary_payload.get("locationPerformance") or []),
                },
                output_entity_ids={
                    "trial": [str(trial_payload.get("trialDbId") or trial_id)],
                    "top_performers": _sample_record_identifiers(
                        summary_payload.get("topPerformers"),
                        keys=("germplasmName", "candidate"),
                        limit=5,
                    ),
                    "trait_summary": _sample_record_identifiers(
                        summary_payload.get("traitSummary"),
                        keys=("trait",),
                        limit=5,
                    ),
                },
                output_metadata={
                    "query": str(query) if query else None,
                    "crop": str(crop) if crop else None,
                    "season": str(season) if season else None,
                    "location": str(location) if location else None,
                    "primary_trait": (summary_payload.get("statistics") or {}).get("primary_trait"),
                },
                compute_methods=list(summary_payload.get("calculation_method_refs") or []),
                metadata=plan_metadata,
            )

            return _with_plan_execution_summary(
                {
                    "success": True,
                    "function": function_name,
                    "result_type": "trial_results",
                    "data": {
                        "trial": trial_payload,
                        "top_performers": summary_payload.get("topPerformers", []),
                        "trait_summary": summary_payload.get("traitSummary", []),
                        "location_performance": summary_payload.get("locationPerformance", []),
                        "statistics": summary_payload.get("statistics", {}),
                        "interpretation": summary_payload.get("interpretation", {}),
                        "message": (
                            f"Trial '{trial_payload.get('trialName') or trial_id}' summary "
                            "retrieved from database-backed trial surfaces."
                        ),
                    },
                    "evidence_refs": summary_payload.get("evidence_refs", []),
                    "calculation_ids": summary_payload.get("calculation_ids", []),
                    "response_contract_version": summary_payload.get("response_contract_version"),
                    "trust_surface": summary_payload.get("trust_surface"),
                    "data_source": summary_payload.get("data_source"),
                    "schema_version": summary_payload.get("schema_version"),
                    "confidence_score": summary_payload.get("confidence_score"),
                    "data_age_seconds": summary_payload.get("data_age_seconds"),
                    "calculation_method_refs": summary_payload.get("calculation_method_refs", []),
                    "evidence_envelope": summary_payload.get("evidence_envelope"),
                    "retrieval_audit": {
                        "services": ["app.api.v2.trial_summary.get_trial_summary"],
                        "tables": [
                            "Trial",
                            "Study",
                            "Observation",
                            "ObservationUnit",
                            "ObservationVariable",
                            "Germplasm",
                            "Location",
                        ],
                        "entities": {
                            "trial_id": str(trial_id),
                            "trial_db_id": trial_payload.get("trialDbId"),
                        },
                        "scope": {
                            "organization_id": org_id,
                            "query": str(query) if query else None,
                            "crop": str(crop) if crop else None,
                            "season": str(season) if season else None,
                            "location": str(location) if location else None,
                        },
                    },
                    "demo": False,
                },
                plan_execution_summary,
            )
        except Exception as e:
            logger.error(f"Get trial results failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get trial results",
            }

    elif function_name == "get_trait_summary":
        org_id = params.get("organization_id", 1)
        requested_germplasm_ids = params.get("germplasm_ids") or []
        if isinstance(requested_germplasm_ids, str):
            requested_germplasm_ids = [
                item.strip() for item in requested_germplasm_ids.split(",") if item.strip()
            ]
        plan_metadata = {
            "resolution_mode": (
                "explicit_germplasm_scope" if requested_germplasm_ids else "comparison_scope"
            ),
        }

        resolved_germplasm = []
        if requested_germplasm_ids:
            resolved_germplasm = await executor._resolve_germplasm_requests(
                organization_id=org_id,
                germplasm_ids=[str(gid) for gid in requested_germplasm_ids],
            )
            if not resolved_germplasm:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Trait summary requires at least one resolvable germplasm",
                        "message": (
                            "No requested germplasm could be resolved for phenotype trait summary."
                        ),
                        "retrieval_audit": {
                            "services": [
                                "germplasm_search_service.get_by_id",
                                "germplasm_search_service.search",
                            ],
                            "tables": ["Germplasm"],
                            "entities": {
                                "requested_germplasm_ids": [
                                    str(gid) for gid in requested_germplasm_ids
                                ],
                                "resolved_germplasm_ids": [],
                            },
                            "scope": {"organization_id": org_id},
                        },
                        "safe_failure": {
                            "error_category": "insufficient_retrieval_scope",
                            "searched": [
                                "phenotype_comparison.statistics",
                                "germplasm_search_service",
                            ],
                            "missing": ["resolvable germplasm identifiers"],
                            "next_steps": [
                                "Retry with exact accession or germplasm IDs.",
                                "Use fewer or more specific germplasm names.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="breeding",
                        completed=False,
                        services=[
                            "germplasm_search_service.get_by_id",
                            "germplasm_search_service.search",
                        ],
                        output_metadata={
                            "requested_germplasm_count": len(requested_germplasm_ids),
                        },
                        missing_reason="no requested germplasm identifiers resolved to an authoritative phenotype comparison scope",
                        metadata=plan_metadata,
                    ),
                )

        authoritative_germplasm_ids = [
            identifier
            for germplasm in resolved_germplasm
            for identifier in [_get_germplasm_identifier(germplasm)]
            if identifier
        ]

        try:
            summary_payload = await get_comparison_statistics(
                germplasm_ids=",".join(authoritative_germplasm_ids)
                if authoritative_germplasm_ids
                else None,
                db=executor.db,
                organization_id=org_id,
            )
            contract_metadata = PhenotypeComparisonContractMetadata(
                scope=str(summary_payload.get("scope") or "statistics"),
                confidence_score=summary_payload.get("confidence_score")
                if summary_payload.get("confidence_score") is not None
                else (summary_payload.get("evidence_envelope") or {})
                .get("uncertainty", {})
                .get("confidence"),
                data_age_seconds=summary_payload.get("data_age_seconds"),
            )
            trait_summary = summary_payload.get("trait_summary") or {}
            actual_outputs = ["trait_summary", "interpretation"]
            if authoritative_germplasm_ids or summary_payload.get("total_germplasm"):
                actual_outputs.append("germplasm")
            plan_execution_summary = _build_single_contract_plan_execution_summary(
                function_name=function_name,
                domain="breeding",
                domains_involved=["breeding", "analytics"],
                completed=True,
                services=[
                    "app.api.v2.phenotype_comparison.get_comparison_statistics"
                ],
                actual_outputs=actual_outputs,
                output_counts={
                    "trait_summary": len(trait_summary),
                    "interpretation": 1 if summary_payload.get("interpretation") else 0,
                    "germplasm": len(authoritative_germplasm_ids)
                    or int(summary_payload.get("total_germplasm") or 0),
                },
                output_entity_ids={
                    "trait_summary": _sample_scalar_values(list(trait_summary.keys()), limit=5),
                    "germplasm": authoritative_germplasm_ids,
                },
                output_metadata={
                    "scope": summary_payload.get("scope") or contract_metadata.scope,
                    "requested_germplasm_count": len(requested_germplasm_ids),
                    "total_traits": summary_payload.get("total_traits"),
                },
                metadata=plan_metadata,
            )

            return _with_plan_execution_summary(
                {
                    "success": True,
                    "function": function_name,
                    "result_type": "trait_summary",
                    "data": {
                        "total_germplasm": summary_payload.get("total_germplasm", 0),
                        "total_traits": summary_payload.get("total_traits", 0),
                        "trait_summary": summary_payload.get("trait_summary", {}),
                        "interpretation": summary_payload.get("interpretation", {}),
                        "message": (
                            "Trait summary statistics retrieved from database-backed phenotype "
                            "comparison surfaces."
                        ),
                    },
                    "evidence_refs": summary_payload.get("evidence_refs", []),
                    "calculation_ids": summary_payload.get("calculation_ids", []),
                    "response_contract_version": summary_payload.get(
                        "response_contract_version"
                    )
                    or summary_payload.get("contract_version")
                    or contract_metadata.response_contract_version,
                    "trust_surface": summary_payload.get("trust_surface")
                    or contract_metadata.trust_surface,
                    "data_source": summary_payload.get("data_source")
                    or summary_payload.get("source")
                    or contract_metadata.data_source,
                    "schema_version": summary_payload.get("schema_version")
                    or contract_metadata.schema_version,
                    "scope": summary_payload.get("scope") or contract_metadata.scope,
                    "confidence_score": contract_metadata.confidence_score,
                    "data_age_seconds": contract_metadata.data_age_seconds,
                    "evidence_envelope": summary_payload.get("evidence_envelope"),
                    "retrieval_audit": {
                        "services": [
                            "app.api.v2.phenotype_comparison.get_comparison_statistics"
                        ],
                        "tables": ["Germplasm", "Observation", "ObservationVariable"],
                        "entities": {
                            "requested_germplasm_ids": [
                                str(gid) for gid in requested_germplasm_ids
                            ],
                            "resolved_germplasm_ids": authoritative_germplasm_ids,
                        },
                        "scope": {
                            "organization_id": org_id,
                            "statistics_scope": contract_metadata.scope,
                        },
                    },
                    "demo": False,
                },
                plan_execution_summary,
            )
        except Exception as e:
            logger.error(f"Get trait summary failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get trait summary",
            }

    elif function_name == "get_marker_associations":
        org_id = params.get("organization_id", 1)
        qtl_service = get_qtl_mapping_service()
        requested_trait = params.get("trait") or params.get("query")
        chromosome = params.get("chromosome")
        plan_metadata = {
            "resolution_mode": "trait_lookup",
            "chromosome": chromosome,
        }

        try:
            available_traits = await qtl_service.get_traits(executor.db, org_id)
            resolved_trait, matches = _resolve_trait_query(
                available_traits=available_traits,
                requested_trait=requested_trait,
            )

            if not requested_trait:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Marker association lookup requires a trait query",
                        "message": "Please specify the trait or marker-association question to resolve.",
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="genomics",
                        completed=False,
                        services=["QTLMappingService.get_traits"],
                        missing_reason="a trait query is required before genomics marker retrieval can run",
                        metadata=plan_metadata,
                    ),
                )

            if len(matches) > 1:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Ambiguous marker association query",
                        "message": (
                            f"Multiple genomics traits matched '{requested_trait}'. Please choose one exact trait."
                        ),
                        "candidates": matches,
                        "retrieval_audit": {
                            "services": ["QTLMappingService.get_traits"],
                            "tables": ["BioQTL", "GWASResult", "GWASRun"],
                            "entities": {
                                "requested_trait": requested_trait,
                                "candidate_traits": matches,
                            },
                            "scope": {"organization_id": org_id},
                        },
                        "safe_failure": {
                            "error_category": "ambiguous_retrieval_scope",
                            "searched": [
                                "QTLMappingService.get_traits",
                                "QTLMappingService.get_gwas_results",
                            ],
                            "missing": ["single authoritative genomics trait"],
                            "next_steps": [
                                "Retry with one exact trait name.",
                                "Narrow the request by chromosome if applicable.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="genomics",
                        completed=False,
                        services=["QTLMappingService.get_traits"],
                        actual_outputs=["candidate_traits"],
                        output_counts={"candidate_traits": len(matches)},
                        output_entity_ids={
                            "candidate_traits": _sample_scalar_values(matches, limit=5)
                        },
                        output_metadata={
                            "requested_trait": requested_trait,
                            "chromosome": chromosome,
                        },
                        missing_reason="multiple genomics traits matched the query; one authoritative trait is still required",
                        metadata=plan_metadata,
                    ),
                )

            if not resolved_trait:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Unresolvable marker association query",
                        "message": (
                            f"Could not resolve '{requested_trait}' to one authoritative genomics trait."
                        ),
                        "candidates": matches,
                        "retrieval_audit": {
                            "services": ["QTLMappingService.get_traits"],
                            "tables": ["BioQTL", "GWASResult", "GWASRun"],
                            "entities": {
                                "requested_trait": requested_trait,
                                "candidate_traits": matches,
                            },
                            "scope": {"organization_id": org_id},
                        },
                        "safe_failure": {
                            "error_category": "insufficient_retrieval_scope",
                            "searched": [
                                "QTLMappingService.get_traits",
                                "QTLMappingService.get_gwas_results",
                            ],
                            "missing": ["single authoritative genomics trait"],
                            "next_steps": [
                                "Retry with the exact trait name used in QTL or GWAS records.",
                                "Ask for available genomics traits before requesting markers.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="genomics",
                        completed=False,
                        services=["QTLMappingService.get_traits"],
                        actual_outputs=["candidate_traits"] if matches else [],
                        output_counts={"candidate_traits": len(matches)},
                        output_entity_ids={
                            "candidate_traits": _sample_scalar_values(matches, limit=5)
                        },
                        output_metadata={
                            "requested_trait": requested_trait,
                            "chromosome": chromosome,
                        },
                        missing_reason="the requested trait did not resolve to one authoritative genomics trait",
                        metadata=plan_metadata,
                    ),
                )

            qtls = await qtl_service.list_qtls(
                executor.db,
                org_id,
                trait=resolved_trait,
                chromosome=chromosome,
            )
            associations = await qtl_service.get_gwas_results(
                executor.db,
                org_id,
                trait=resolved_trait,
                chromosome=chromosome,
            )

            if not qtls and not associations:
                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "No marker associations found",
                        "message": (
                            f"No QTL or GWAS marker associations were found for trait '{resolved_trait}'."
                        ),
                        "retrieval_audit": {
                            "services": [
                                "QTLMappingService.get_traits",
                                "QTLMappingService.list_qtls",
                                "QTLMappingService.get_gwas_results",
                            ],
                            "tables": ["BioQTL", "GWASResult", "GWASRun"],
                            "entities": {
                                "requested_trait": requested_trait,
                                "resolved_trait": resolved_trait,
                                "chromosome": chromosome,
                            },
                            "scope": {"organization_id": org_id},
                        },
                        "safe_failure": {
                            "error_category": "insufficient_retrieval_scope",
                            "searched": [
                                "QTLMappingService.list_qtls",
                                "QTLMappingService.get_gwas_results",
                            ],
                            "missing": ["QTL or GWAS records for the resolved trait"],
                            "next_steps": [
                                "Try another trait with genomics evidence.",
                                "Load QTL/GWAS results for this organization before retrying.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="genomics",
                        completed=False,
                        services=[
                            "QTLMappingService.get_traits",
                            "QTLMappingService.list_qtls",
                            "QTLMappingService.get_gwas_results",
                        ],
                        output_metadata={
                            "requested_trait": requested_trait,
                            "resolved_trait": resolved_trait,
                            "chromosome": chromosome,
                        },
                        missing_reason="the resolved trait did not expose grounded QTL or GWAS marker associations",
                        metadata=plan_metadata,
                    ),
                )

            confidence_score = _derive_genomics_lookup_confidence(
                qtl_count=len(qtls),
                association_count=len(associations),
            )
            contract_metadata = GenomicsMarkerLookupContractMetadata(
                confidence_score=confidence_score,
            )
            evidence_envelope = _build_genomics_evidence_envelope(
                trait=resolved_trait,
                qtls=qtls,
                associations=associations,
                confidence_score=confidence_score,
            )

            plan_execution_summary = _build_single_contract_plan_execution_summary(
                function_name=function_name,
                domain="genomics",
                completed=True,
                services=[
                    "QTLMappingService.get_traits",
                    "QTLMappingService.list_qtls",
                    "QTLMappingService.get_gwas_results",
                ],
                actual_outputs=_dedupe_string_values(
                    [
                        "qtls" if qtls else None,
                        "marker_associations" if associations else None,
                    ]
                ),
                output_counts={
                    "qtls": len(qtls),
                    "marker_associations": len(associations),
                },
                output_entity_ids={
                    "qtls": _sample_record_identifiers(qtls, keys=("qtl_id", "id"), limit=5),
                    "marker_associations": _sample_record_identifiers(
                        associations,
                        keys=("marker_name", "id"),
                        limit=5,
                    ),
                },
                output_metadata={
                    "requested_trait": requested_trait,
                    "resolved_trait": resolved_trait,
                    "chromosome": chromosome,
                    "top_marker": associations[0].get("marker_name") if associations else None,
                },
                metadata=plan_metadata,
            )

            return _with_plan_execution_summary(
                {
                    "success": True,
                    "function": function_name,
                    "result_type": "marker_associations",
                    "data": {
                        "trait": resolved_trait,
                        "qtls": qtls,
                        "associations": associations,
                        "summary": {
                            "qtl_count": len(qtls),
                            "association_count": len(associations),
                            "top_marker": (
                                associations[0].get("marker_name") if associations else None
                            ),
                        },
                        "message": (
                            f"Retrieved genomics marker associations for trait '{resolved_trait}' from "
                            "database-backed QTL and GWAS records."
                        ),
                    },
                    "evidence_refs": [
                        ref["entity_id"]
                        for ref in evidence_envelope.get("evidence_refs", [])
                    ],
                    "calculation_ids": [
                        step["step_id"]
                        for step in evidence_envelope.get("calculation_steps", [])
                    ],
                    "response_contract_version": contract_metadata.response_contract_version,
                    "trust_surface": contract_metadata.trust_surface,
                    "data_source": contract_metadata.data_source,
                    "schema_version": contract_metadata.schema_version,
                    "confidence_score": contract_metadata.confidence_score,
                    "evidence_envelope": evidence_envelope,
                    "retrieval_audit": {
                        "services": [
                            "QTLMappingService.get_traits",
                            "QTLMappingService.list_qtls",
                            "QTLMappingService.get_gwas_results",
                        ],
                        "tables": ["BioQTL", "GWASResult", "GWASRun"],
                        "entities": {
                            "requested_trait": requested_trait,
                            "resolved_trait": resolved_trait,
                            "chromosome": chromosome,
                        },
                        "scope": {
                            "organization_id": org_id,
                            "candidate_traits": matches,
                        },
                    },
                    "demo": False,
                },
                plan_execution_summary,
            )
        except Exception as e:
            logger.error(f"Get marker associations failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get marker associations",
            }

    elif function_name == "get_observations":
        org_id = params.get("organization_id", 1)
        trait = params.get("trait")
        study_id = params.get("study_id")
        germplasm_id = params.get("germplasm_id")
        query = params.get("query") or params.get("q")

        try:
            results = await observation_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                trait=trait,
                study_id=int(study_id) if study_id else None,
                germplasm_id=int(germplasm_id) if germplasm_id else None,
                limit=50,
            )

            return {
                "success": True,
                "function": function_name,
                "result_type": "observation_list",
                "data": {
                    "total": len(results),
                    "items": results,
                    "message": f"Found {len(results)} observations"
                    + (f" for trait '{trait}'" if trait else ""),
                },
                "demo": False,
            }
        except Exception as e:
            logger.error(f"Get observations failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get observations",
            }

    elif function_name == "get_trait_details":
        org_id = params.get("organization_id", 1)
        trait_id = params.get("trait_id") or params.get("id")

        if not trait_id:
            return {
                "success": False,
                "error": "trait_id is required",
                "message": "Please specify a trait ID",
            }

        try:
            result = await trait_search_service.get_by_id(
                db=executor.db,
                organization_id=org_id,
                trait_id=str(trait_id),
            )

            if not result:
                return {
                    "success": False,
                    "error": "Trait not found",
                    "message": f"No trait found with ID {trait_id}",
                }

            return {
                "success": True,
                "function": function_name,
                "result_type": "trait_details",
                "data": {
                    "trait": result,
                    "observation_count": result.get("observation_count", 0),
                    "message": f"Trait '{result['name']}' ({result.get('trait_class', 'unknown class')})",
                },
                "demo": False,
            }
        except Exception as e:
            logger.error(f"Get trait details failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get trait details",
            }

    elif function_name == "get_program_details":
        org_id = params.get("organization_id", 1)
        program_id = params.get("program_id") or params.get("id")

        if not program_id:
            return {
                "success": False,
                "error": "program_id is required",
                "message": "Please specify a program ID",
            }

        try:
            result = await program_search_service.get_by_id(
                db=executor.db,
                organization_id=org_id,
                program_id=str(program_id),
            )

            if not result:
                return {
                    "success": False,
                    "error": "Program not found",
                    "message": f"No program found with ID {program_id}",
                }

            return {
                "success": True,
                "function": function_name,
                "result_type": "program_details",
                "data": {
                    "program": result,
                    "trial_count": result.get("trial_count", 0),
                    "message": f"Program '{result['name']}' with {result.get('trial_count', 0)} trials",
                },
                "demo": False,
            }
        except Exception as e:
            logger.error(f"Get program details failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get program details",
            }

    elif function_name == "get_location_details":
        org_id = params.get("organization_id", 1)
        location_id = params.get("location_id") or params.get("id")

        if not location_id:
            return {
                "success": False,
                "error": "location_id is required",
                "message": "Please specify a location ID",
            }

        try:
            result = await executor.location_search_service.get_by_id(
                db=executor.db,
                organization_id=org_id,
                location_id=str(location_id),
            )

            if not result:
                return {
                    "success": False,
                    "error": "Location not found",
                    "message": f"No location found with ID {location_id}",
                }

            return {
                "success": True,
                "function": function_name,
                "result_type": "location_details",
                "data": {
                    "location": result,
                    "message": f"Location '{result['name']}' in {result.get('country', 'unknown country')}",
                },
                "demo": False,
            }
        except Exception as e:
            logger.error(f"Get location details failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get location details",
            }

    elif function_name == "get_seedlot_details":
        org_id = params.get("organization_id", 1)
        seedlot_id = params.get("seedlot_id") or params.get("id")

        if not seedlot_id:
            return {
                "success": False,
                "error": "seedlot_id is required",
                "message": "Please specify a seedlot ID",
            }

        try:
            result = await seedlot_search_service.get_by_id(
                db=executor.db,
                organization_id=org_id,
                seedlot_id=str(seedlot_id),
            )

            if not result:
                return {
                    "success": False,
                    "error": "Seedlot not found",
                    "message": f"No seedlot found with ID {seedlot_id}",
                }

            viability = await seedlot_search_service.check_viability(
                db=executor.db,
                organization_id=org_id,
                seedlot_id=str(seedlot_id),
            )

            return {
                "success": True,
                "function": function_name,
                "result_type": "seedlot_details",
                "data": {
                    "seedlot": result,
                    "viability": viability,
                    "message": f"Seedlot '{result.get('name', seedlot_id)}' - {result.get('amount', 0)} {result.get('units', 'seeds')}",
                },
                "demo": False,
            }
        except Exception as e:
            logger.error(f"Get seedlot details failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get seedlot details",
            }

    elif function_name == "get_cross_details":
        org_id = params.get("organization_id", 1)
        cross_id = params.get("cross_id") or params.get("id")

        if not cross_id:
            return {
                "success": False,
                "error": "cross_id is required",
                "message": "Please specify a cross ID",
            }

        try:
            result = await executor.cross_search_service.get_by_id(
                db=executor.db,
                organization_id=org_id,
                cross_id=str(cross_id),
            )

            if not result:
                return {
                    "success": False,
                    "error": "Cross not found",
                    "message": f"No cross found with ID {cross_id}",
                }

            return {
                "success": True,
                "function": function_name,
                "result_type": "cross_details",
                "data": {
                    "cross": result,
                    "message": f"Cross '{result.get('name', cross_id)}' - {result.get('status', 'unknown status')}",
                },
                "demo": False,
            }
        except Exception as e:
            logger.error(f"Get cross details failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get cross details",
            }

    elif function_name == "get_weather_forecast":
        location = params.get("location") or params.get("location_id") or "default"
        location_name = params.get("location_name") or location
        days = params.get("days", 7)
        crop = params.get("crop", "wheat")

        try:
            forecast = await executor.weather_service.get_forecast(
                location_id=str(location),
                location_name=location_name,
                days=days,
                crop=crop,
            )

            summary = executor.weather_service.get_veena_summary(forecast)

            return {
                "success": True,
                "function": function_name,
                "result_type": "weather_forecast",
                "data": {
                    "location": location_name,
                    "days": days,
                    "summary": summary,
                    "alerts": forecast.alerts,
                    "impacts_count": len(forecast.impacts),
                    "optimal_windows": [
                        {
                            "activity": window.activity.value,
                            "start": window.start.isoformat(),
                            "end": window.end.isoformat(),
                            "confidence": window.confidence,
                        }
                        for window in forecast.optimal_windows[:5]
                    ],
                    "message": f"Weather forecast for {location_name} ({days} days)",
                },
                "demo": False,
            }
        except Exception as e:
            logger.error(f"Get weather forecast failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get weather forecast",
            }

    elif function_name == "get_gdd_insights":
        field_id = params.get("field_id")
        insight_type = params.get("insight_type")
        try:
            gdd_service = CrossDomainGDDService(executor.db)
            insights: dict[str, Any] = {}
            if insight_type == "risk":
                insights = gdd_service.create_climate_risk_alerts(field_id)
            elif insight_type == "planting":
                insights = gdd_service.analyze_planting_windows(field_id, "maize")
            elif insight_type == "harvest":
                from datetime import date

                insights = gdd_service.predict_harvest_timing(field_id, date.today(), "maize")
            message = insights.get("message") if isinstance(insights, dict) else None
            if not isinstance(message, str) or not message.strip():
                risk_alerts = insights.get("risk_alerts") if isinstance(insights, dict) else None
                if isinstance(risk_alerts, list) and risk_alerts:
                    first_risk_alert = risk_alerts[0]
                    candidate = first_risk_alert.get("message") if isinstance(first_risk_alert, dict) else None
                    if isinstance(candidate, str) and candidate.strip():
                        message = candidate
            if not isinstance(message, str) or not message.strip():
                if insight_type == "planting":
                    message = f"Generated planting GDD insights for field {field_id}."
                elif insight_type == "harvest":
                    message = f"Generated harvest GDD insights for field {field_id}."
                elif insight_type == "risk":
                    message = f"Generated climate risk GDD insights for field {field_id}."
                else:
                    message = f"Generated GDD insights for field {field_id}."
            return {
                "success": True,
                "function": function_name,
                "result_type": "gdd_insights",
                "data": {
                    **insights,
                    "message": message,
                },
            }
        except Exception as exc:
            logger.error("Get GDD insights failed: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "message": "Failed to get GDD insights",
            }

    return {"success": False, "error": f"Unhandled get function: {function_name}"}