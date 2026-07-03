"""Extracted compare-handler family for the REEVU function executor.

This module keeps compare-specific control flow out of tools.py while still
receiving helper seams from that module so the extraction stays narrow and
behavior-preserving.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

from app.modules.ai.services.reevu.phenotype_comparison_engine import PhenotypeComparisonEngine
from app.modules.phenotyping.services.phenotype_evidence_service import (
    build_phenotype_evidence_envelope as _build_phenotype_evidence_envelope,
)
from app.schemas.phenotype_comparison_contract import PhenotypeComparisonContractMetadata


@dataclass(slots=True)
class CompareHandlerSharedContext:
    build_single_contract_plan_execution_summary: Any
    with_plan_execution_summary: Any
    get_germplasm_identifier: Any
    observation_search_service: Any
    phenotype_interpretation_service: Any
    envelope_observation_record_cls: Any


async def handle_compare(
    executor: Any,
    function_name: str,
    params: dict[str, Any],
    *,
    shared: CompareHandlerSharedContext,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Handle compare_* functions for FunctionExecutor."""

    _build_single_contract_plan_execution_summary = (
        shared.build_single_contract_plan_execution_summary
    )
    _with_plan_execution_summary = shared.with_plan_execution_summary
    _get_germplasm_identifier = shared.get_germplasm_identifier
    observation_search_service = shared.observation_search_service
    EnvelopeObservationRecord = shared.envelope_observation_record_cls

    if function_name == "compare_germplasm":
        org_id = params.get("organization_id", 1)
        germplasm_ids = params.get("germplasm_ids", [])
        requested_traits = params.get("traits", [])
        plan_metadata = {"resolution_mode": "explicit_germplasm_comparison"}

        if not germplasm_ids or len(germplasm_ids) < 2:
            return _with_plan_execution_summary(
                {
                    "success": False,
                    "error": "At least 2 germplasm IDs required",
                    "message": "Please specify at least 2 germplasm IDs to compare",
                },
                _build_single_contract_plan_execution_summary(
                    function_name=function_name,
                    domain="breeding",
                    completed=False,
                    output_metadata={
                        "requested_germplasm_count": len(germplasm_ids),
                        "requested_trait_count": len(requested_traits),
                    },
                    missing_reason="at least two germplasm identifiers are required before phenotype comparison can run",
                    metadata=plan_metadata,
                ),
            )

        try:
            germplasm_data = await executor._resolve_germplasm_requests(
                organization_id=org_id,
                germplasm_ids=[str(gid) for gid in germplasm_ids],
            )

            observations: list[dict[str, Any]] = []
            observations_by_germplasm: dict[str, list[dict[str, Any]]] = {}
            for germplasm in germplasm_data:
                obs = await observation_search_service.get_by_germplasm(
                    db=executor.db,
                    organization_id=org_id,
                    germplasm_id=int(germplasm["id"]),
                    limit=100,
                )
                if requested_traits:
                    requested_traits_lower = {trait.lower() for trait in requested_traits}
                    obs = [
                        item
                        for item in obs
                        if (item.get("trait") or {}).get("name", "").lower() in requested_traits_lower
                        or (item.get("trait") or {}).get("trait_name", "").lower() in requested_traits_lower
                    ]
                germplasm["observation_count"] = len(obs)
                identifier = _get_germplasm_identifier(germplasm) or str(germplasm["id"])
                observations_by_germplasm[identifier] = obs
                observations.extend(obs)

            resolved_germplasm_ids = [
                identifier
                for germplasm in germplasm_data
                for identifier in [_get_germplasm_identifier(germplasm)]
                if identifier
            ]

            if len(germplasm_data) < 2:
                actual_outputs = ["germplasm"]
                if observations:
                    actual_outputs.append("observations")

                return _with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Not enough germplasm found",
                        "message": f"Only found {len(germplasm_data)} of {len(germplasm_ids)} requested germplasm",
                        "retrieval_audit": {
                            "services": [
                                "germplasm_search_service.search",
                                "observation_search_service.get_by_germplasm",
                            ],
                            "tables": ["Germplasm", "Observation", "ObservationVariable"],
                            "entities": {
                                "requested_germplasm_ids": [str(gid) for gid in germplasm_ids],
                                "resolved_germplasm_ids": resolved_germplasm_ids,
                            },
                            "scope": {
                                "organization_id": org_id,
                                "requested_traits": requested_traits,
                            },
                        },
                        "safe_failure": {
                            "error_category": "insufficient_retrieval_scope",
                            "searched": ["phenotype_comparison.compare", "germplasm_search_service"],
                            "missing": ["at least two resolvable germplasm identifiers"],
                            "next_steps": [
                                "Retry with exact accession or germplasm IDs.",
                                "Reduce the comparison to two explicitly named germplasm entries.",
                            ],
                        },
                    },
                    _build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="breeding",
                        completed=False,
                        services=[
                            "germplasm_search_service.search",
                            "observation_search_service.get_by_germplasm",
                        ],
                        actual_outputs=actual_outputs,
                        output_counts={
                            "germplasm": len(germplasm_data),
                            "observations": len(observations),
                        },
                        output_entity_ids={"germplasm": resolved_germplasm_ids},
                        output_metadata={
                            "requested_germplasm_count": len(germplasm_ids),
                            "requested_trait_count": len(requested_traits),
                        },
                        missing_reason="fewer than two germplasm identifiers resolved to grounded phenotype evidence",
                        metadata=plan_metadata,
                    ),
                )

            comparison_engine = PhenotypeComparisonEngine()
            primary_trait = str(requested_traits[0]) if requested_traits else None
            statistical_comparison = comparison_engine.compare(
                germplasm_ids=resolved_germplasm_ids,
                observations_by_germplasm=observations_by_germplasm,
                trait_name=primary_trait,
            )
            trait_profile = comparison_engine.build_trait_profile(
                germplasm_ids=resolved_germplasm_ids,
                observations_by_germplasm=observations_by_germplasm,
            )
            statistical_comparison_payload = asdict(statistical_comparison)
            statistical_comparison_payload["evidence_refs"] = [
                ref.model_dump() for ref in statistical_comparison.evidence_refs
            ]
            statistical_comparison_payload["calculation_steps"] = [
                step.model_dump() for step in statistical_comparison.calculation_steps
            ]
            trait_profile_payload = asdict(trait_profile)
            trait_profile_payload["evidence_refs"] = [
                ref.model_dump() for ref in trait_profile.evidence_refs
            ]
            trait_profile_payload["calculation_steps"] = [
                step.model_dump() for step in trait_profile.calculation_steps
            ]

            records = executor._build_interpretation_records_from_observations(observations)
            baseline_record = next(
                (record for record in records if record.role_hint == "baseline_candidate"),
                None,
            )
            interpretation = shared.phenotype_interpretation_service.build_interpretation(
                scope="reevu_compare_germplasm",
                records=records,
                methodology="database_observation_means_by_germplasm",
                entity_order=[
                    _get_germplasm_identifier(germplasm)
                    for germplasm in germplasm_data
                    if _get_germplasm_identifier(germplasm)
                ],
                baseline_entity_id=baseline_record.entity_db_id if baseline_record else None,
                baseline_entity_name=baseline_record.entity_name if baseline_record else None,
                baseline_selection="inferred_check_entry" if baseline_record else None,
                evidence_refs=[
                    f"db:germplasm:{_get_germplasm_identifier(germplasm)}"
                    for germplasm in germplasm_data
                    if _get_germplasm_identifier(germplasm)
                ],
            )
            candidates = executor._build_ranked_candidates(interpretation)
            envelope_observations = [
                EnvelopeObservationRecord(
                    id=observation.get("id"),
                    observation_db_id=observation.get("observation_db_id"),
                    observation_time_stamp=observation.get("observation_time_stamp"),
                )
                for observation in observations
            ]
            evidence_envelope = _build_phenotype_evidence_envelope(
                scope="compare",
                observations=envelope_observations,
                interpretation=interpretation,
            ).model_dump()
            contract_metadata = PhenotypeComparisonContractMetadata(
                scope="compare",
                confidence_score=evidence_envelope.get("uncertainty", {}).get("confidence"),
            )
            comparison_entities = [
                str(candidate.get("candidate"))
                for candidate in candidates
                if candidate.get("candidate")
            ]
            actual_outputs = [
                "comparison",
                "germplasm",
                "interpretation",
                "statistical_comparison",
                "trait_profile",
            ]
            if observations:
                actual_outputs.append("observations")
            plan_execution_summary = _build_single_contract_plan_execution_summary(
                function_name=function_name,
                domain="breeding",
                domains_involved=["breeding", "analytics"],
                completed=True,
                services=[
                    "germplasm_search_service.search",
                    "observation_search_service.get_by_germplasm",
                    "phenotype_interpretation_service.build_interpretation",
                ],
                actual_outputs=actual_outputs,
                output_counts={
                    "comparison": len(candidates),
                    "germplasm": len(germplasm_data),
                    "interpretation": 1,
                    "observations": len(observations),
                },
                output_entity_ids={
                    "comparison": comparison_entities,
                    "germplasm": resolved_germplasm_ids,
                },
                output_metadata={
                    "requested_trait_count": len(requested_traits),
                    "baseline_selection": "inferred_check_entry" if baseline_record else None,
                },
                metadata=plan_metadata,
            )

            return _with_plan_execution_summary(
                {
                    "success": True,
                    "function": function_name,
                    "result_type": "comparison",
                    "data": candidates,
                    "statistical_comparison": statistical_comparison_payload,
                    "trait_profile": trait_profile_payload,
                    "comparison_context": {
                        "germplasm_count": len(germplasm_data),
                        "items": germplasm_data,
                        "interpretation": interpretation.model_dump(),
                        "statistical_comparison": statistical_comparison_payload,
                        "trait_profile": trait_profile_payload,
                        "message": f"Compared {len(germplasm_data)} germplasm entries using the shared phenotype interpretation contract",
                    },
                    "evidence_refs": interpretation.evidence_refs,
                    "calculation_ids": list(dict.fromkeys(
                        [
                            *interpretation.calculation_ids,
                            *[
                                step.step_id
                                for step in statistical_comparison.calculation_steps
                            ],
                            *[step.step_id for step in trait_profile.calculation_steps],
                        ]
                    )),
                    "response_contract_version": contract_metadata.response_contract_version,
                    "trust_surface": contract_metadata.trust_surface,
                    "data_source": contract_metadata.data_source,
                    "schema_version": contract_metadata.schema_version,
                    "scope": contract_metadata.scope,
                    "confidence_score": contract_metadata.confidence_score,
                    "data_age_seconds": contract_metadata.data_age_seconds,
                    "evidence_envelope": evidence_envelope,
                    "retrieval_audit": {
                        "services": [
                            "germplasm_search_service.search",
                            "observation_search_service.get_by_germplasm",
                            "phenotype_interpretation_service.build_interpretation",
                        ],
                        "tables": [
                            "Germplasm",
                            "Observation",
                            "ObservationVariable",
                        ],
                        "entities": {
                            "requested_germplasm_ids": [str(gid) for gid in germplasm_ids],
                            "resolved_germplasm_ids": resolved_germplasm_ids,
                        },
                        "scope": {
                            "organization_id": org_id,
                            "requested_traits": requested_traits,
                        },
                    },
                    "demo": False,
                },
                plan_execution_summary,
            )
        except Exception as exc:
            logger.error(f"Compare germplasm failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "message": "Failed to compare germplasm",
            }

    return {"success": False, "error": f"Unhandled compare function: {function_name}"}
