"""Extracted calculate-handler family for the REEVU function executor.

This module receives shared helpers and runtime surfaces from tools.py so the
calculate extraction can stay narrow, avoid circular imports, and preserve the
existing monkeypatch paths rooted at the tools module.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.phenotyping.services.interpretation_service import safe_float
from app.schemas.compute_contract import COMPUTE_CONTRACT_VERSION, ComputeInputSummary, GBLUPOutput
from app.services.compute_contract_service import build_compute_success_response


COMPUTE_CONTRACT_TRUST_SURFACE = "compute_contract"


@dataclass
class CalculateHandlerSharedContext:
    build_single_contract_plan_execution_summary: Any
    with_plan_execution_summary: Any
    sample_record_identifiers: Any
    build_compute_evidence_envelope: Any
    observation_search_service: Any
    compute_engine: Any
    resolve_database_backed_gblup_inputs: Any


def _normalize_training_population_label(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = " ".join(value.split()).strip()
    return normalized or None


def _coerce_genotype_dosage(genotype_value: Any, genotype_payload: Any = None) -> float | None:
    def _coerce(candidate: Any) -> float | None:
        if candidate is None or isinstance(candidate, bool):
            return None

        if isinstance(candidate, (int, float)):
            return float(candidate)

        if isinstance(candidate, list):
            alleles: list[int] = []
            for item in candidate:
                if isinstance(item, bool):
                    return None
                if isinstance(item, (int, float)):
                    alleles.append(int(item))
                    continue
                if isinstance(item, str) and item.strip().isdigit():
                    alleles.append(int(item.strip()))
                    continue
                return None
            return float(sum(alleles)) if alleles else None

        if isinstance(candidate, str):
            normalized = candidate.strip()
            if not normalized or normalized in {".", "./.", ".|."}:
                return None
            if normalized.isdigit():
                return float(int(normalized))

            if "/" in normalized or "|" in normalized:
                alleles: list[int] = []
                for token in normalized.replace("|", "/").split("/"):
                    stripped = token.strip()
                    if not stripped or stripped == "." or not stripped.isdigit():
                        return None
                    alleles.append(int(stripped))
                return float(sum(alleles)) if alleles else None

        return None

    dosage = _coerce(genotype_value)
    if dosage is not None:
        return dosage

    if isinstance(genotype_payload, dict):
        return _coerce(genotype_payload.get("values"))

    return _coerce(genotype_payload)


def _build_gblup_input_safe_failure(
    shared: CalculateHandlerSharedContext,
    *,
    organization_id: int,
    trait: str,
    germplasm_ids: list[str] | None,
    crop: str | None,
    study_id: str | None,
    missing_inputs: list[str],
    message: str,
    services: list[str],
    tables: list[str],
    extra_entities: dict[str, Any] | None = None,
    extra_scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entities: dict[str, Any] = {
        "trait": trait,
        "method": "GBLUP",
        "germplasm_ids": [
            str(germplasm_id)
            for germplasm_id in (germplasm_ids or [])
            if isinstance(germplasm_id, str) and germplasm_id.strip()
        ],
        "study_id": str(study_id) if study_id is not None else None,
    }
    if crop:
        entities["crop"] = crop
    if extra_entities:
        entities.update(extra_entities)

    scope: dict[str, Any] = {
        "organization_id": organization_id,
        "missing_inputs": missing_inputs,
    }
    if extra_scope:
        scope.update(extra_scope)

    plan_execution_summary = shared.build_single_contract_plan_execution_summary(
        function_name="calculate_breeding_value",
        domain="analytics",
        completed=False,
        services=services,
        output_metadata={
            "trait": trait,
            "method": "GBLUP",
            "crop": crop,
            "study_id": str(study_id) if study_id is not None else None,
            "missing_inputs": list(missing_inputs),
        },
        missing_reason=message,
        compute_methods=["fn:compute.gblup"],
    )

    return shared.with_plan_execution_summary(
        {
            "success": False,
            "error": "GBLUP requires genotype_matrix or g_matrix together with phenotypes",
            "message": message,
            "calculation_method_refs": ["fn:compute.gblup"],
            "retrieval_audit": {
                "services": services,
                "tables": tables,
                "entities": entities,
                "scope": scope,
            },
            "safe_failure": {
                "error_category": "insufficient_compute_inputs",
                "missing_inputs": missing_inputs,
                "required_inputs": ["phenotypes", "genotype_matrix or g_matrix"],
            },
            "response_contract_version": COMPUTE_CONTRACT_VERSION,
            "trust_surface": COMPUTE_CONTRACT_TRUST_SURFACE,
        },
        plan_execution_summary,
    )


async def _resolve_database_backed_gblup_inputs(
    *,
    db: AsyncSession,
    organization_id: int,
    trait: str,
    crop: str | None,
    germplasm_ids: list[str] | None,
    study_id: str | None,
) -> dict[str, Any]:
    from app.models.core import Study, Trial
    from app.models.germplasm import Germplasm
    from app.models.genotyping import Call, CallSet, Variant
    from app.models.phenotyping import Observation, ObservationVariable

    normalized_trait = " ".join(trait.lower().split())
    requested_labels = [
        normalized.lower()
        for label in (germplasm_ids or [])
        if (normalized := _normalize_training_population_label(label)) is not None
    ]
    crop_lower = crop.lower() if isinstance(crop, str) and crop.strip() else None
    study_id_int: int | None = None
    if study_id is not None:
        try:
            study_id_int = int(study_id)
        except (TypeError, ValueError):
            study_id_int = None

    phenotype_stmt = (
        select(
            Observation.value.label("value"),
            Germplasm.id.label("germplasm_id"),
            Germplasm.germplasm_name.label("germplasm_name"),
            Germplasm.accession_number.label("accession_number"),
            Germplasm.default_display_name.label("default_display_name"),
            Study.id.label("study_id"),
            Trial.id.label("trial_id"),
        )
        .join(ObservationVariable, ObservationVariable.id == Observation.observation_variable_id)
        .join(Germplasm, Germplasm.id == Observation.germplasm_id)
        .outerjoin(Study, Study.id == Observation.study_id)
        .outerjoin(Trial, Trial.id == Study.trial_id)
        .where(Observation.organization_id == organization_id)
        .where(
            or_(
                func.lower(ObservationVariable.observation_variable_name).like(f"%{normalized_trait}%"),
                func.lower(ObservationVariable.trait_name).like(f"%{normalized_trait}%"),
            )
        )
    )

    if study_id_int is not None:
        phenotype_stmt = phenotype_stmt.where(Observation.study_id == study_id_int)

    if crop_lower:
        phenotype_stmt = phenotype_stmt.where(
            or_(
                func.lower(Study.common_crop_name) == crop_lower,
                func.lower(Trial.common_crop_name) == crop_lower,
                func.lower(Germplasm.common_crop_name) == crop_lower,
            )
        )

    if requested_labels:
        phenotype_stmt = phenotype_stmt.where(
            or_(
                func.lower(Germplasm.germplasm_name).in_(requested_labels),
                func.lower(Germplasm.accession_number).in_(requested_labels),
                func.lower(Germplasm.default_display_name).in_(requested_labels),
                func.lower(Germplasm.germplasm_db_id).in_(requested_labels),
            )
        )

    phenotype_rows = (await db.execute(phenotype_stmt)).all()
    phenotype_entries: dict[str, dict[str, Any]] = {}
    phenotype_observation_count = 0
    resolved_study_ids: list[str] = []
    resolved_trial_ids: list[str] = []

    for row in phenotype_rows:
        value = safe_float(row.value)
        if value is None or row.germplasm_id is None:
            continue

        label = (
            _normalize_training_population_label(row.germplasm_name)
            or _normalize_training_population_label(row.accession_number)
            or _normalize_training_population_label(row.default_display_name)
            or str(row.germplasm_id)
        )
        normalized_label = label.lower()
        entry = phenotype_entries.setdefault(
            normalized_label,
            {
                "germplasm_id": str(row.germplasm_id),
                "label": label,
                "aliases": set(),
                "values": [],
                "study_ids": set(),
                "trial_ids": set(),
            },
        )
        entry["values"].append(value)
        phenotype_observation_count += 1

        for alias_candidate in (
            row.germplasm_name,
            row.accession_number,
            row.default_display_name,
            str(row.germplasm_id),
        ):
            alias = _normalize_training_population_label(alias_candidate)
            if alias:
                entry["aliases"].add(alias.lower())

        if row.study_id is not None:
            study_ref = str(row.study_id)
            entry["study_ids"].add(study_ref)
            if study_ref not in resolved_study_ids:
                resolved_study_ids.append(study_ref)
        if row.trial_id is not None:
            trial_ref = str(row.trial_id)
            entry["trial_ids"].add(trial_ref)
            if trial_ref not in resolved_trial_ids:
                resolved_trial_ids.append(trial_ref)

    if not phenotype_entries:
        return {
            "success": False,
            "missing_inputs": ["phenotypes"],
            "message": (
                "Matrix-backed deterministic GBLUP inputs are required, but no numeric phenotype "
                "observations matched the requested trait and crop scope."
            ),
            "services": ["calculate_breeding_value.database_training_population.observations"],
            "tables": ["Observation", "ObservationVariable", "Germplasm", "Study", "Trial"],
            "entities": {
                "resolved_study_ids": resolved_study_ids,
                "resolved_trial_ids": resolved_trial_ids,
                "observation_count": phenotype_observation_count,
            },
            "scope": {
                "execution_mode": "database_training_population_gblup_resolution",
                "resolution_stage": "phenotypes",
            },
        }

    call_stmt = (
        select(
            CallSet.call_set_name.label("call_set_name"),
            Variant.variant_db_id.label("variant_db_id"),
            Variant.variant_name.label("variant_name"),
            Variant.start.label("variant_start"),
            Call.genotype_value.label("genotype_value"),
            Call.genotype.label("genotype"),
        )
        .select_from(CallSet)
        .join(Call, Call.call_set_id == CallSet.id)
        .join(Variant, Variant.id == Call.variant_id)
        .where(CallSet.organization_id == organization_id)
        .where(func.lower(CallSet.call_set_name).in_(list(phenotype_entries.keys())))
        .order_by(CallSet.call_set_name.asc(), Variant.start.asc(), Variant.variant_name.asc())
    )
    call_rows = (await db.execute(call_stmt)).all()

    genotype_rows_by_label: dict[str, dict[str, float]] = defaultdict(dict)
    variant_rank: dict[str, tuple[float, str]] = {}
    for row in call_rows:
        label = _normalize_training_population_label(row.call_set_name)
        if label is None:
            continue

        dosage = _coerce_genotype_dosage(row.genotype_value, row.genotype)
        if dosage is None:
            continue

        variant_key = (
            _normalize_training_population_label(row.variant_db_id)
            or _normalize_training_population_label(row.variant_name)
            or f"variant-{len(variant_rank) + 1}"
        )
        genotype_rows_by_label[label.lower()][variant_key] = dosage
        variant_rank.setdefault(
            variant_key,
            (
                float(row.variant_start) if row.variant_start is not None else float("inf"),
                str(row.variant_name or variant_key),
            ),
        )

    requested_order: list[str] = []
    if requested_labels:
        for requested_label in requested_labels:
            for normalized_label, entry in phenotype_entries.items():
                if requested_label in entry["aliases"] and normalized_label not in requested_order:
                    requested_order.append(normalized_label)
                    break

    resolved_labels = requested_order or sorted(
        phenotype_entries.keys(),
        key=lambda normalized_label: phenotype_entries[normalized_label]["label"],
    )
    resolved_labels = [
        normalized_label
        for normalized_label in resolved_labels
        if genotype_rows_by_label.get(normalized_label)
    ]

    if len(resolved_labels) < 2:
        return {
            "success": False,
            "missing_inputs": ["genotype_matrix or g_matrix"],
            "message": (
                "Matrix-backed deterministic GBLUP inputs are required, but the resolved training "
                "population does not expose genotype calls for enough individuals."
            ),
            "services": [
                "calculate_breeding_value.database_training_population.observations",
                "calculate_breeding_value.database_training_population.genotypes",
            ],
            "tables": [
                "Observation",
                "ObservationVariable",
                "Germplasm",
                "Study",
                "Trial",
                "CallSet",
                "Call",
                "Variant",
            ],
            "entities": {
                "resolved_germplasm_ids": [
                    phenotype_entries[normalized_label]["label"] for normalized_label in resolved_labels
                ],
                "resolved_study_ids": resolved_study_ids,
                "resolved_trial_ids": resolved_trial_ids,
                "observation_count": phenotype_observation_count,
            },
            "scope": {
                "execution_mode": "database_training_population_gblup_resolution",
                "resolution_stage": "genotypes",
            },
        }

    shared_variant_keys = set(genotype_rows_by_label[resolved_labels[0]].keys())
    for normalized_label in resolved_labels[1:]:
        shared_variant_keys &= set(genotype_rows_by_label[normalized_label].keys())

    ordered_variant_keys = [
        variant_key
        for variant_key in sorted(shared_variant_keys, key=lambda key: variant_rank.get(key, (float("inf"), key)))
        if len({genotype_rows_by_label[normalized_label][variant_key] for normalized_label in resolved_labels}) > 1
    ]

    if not ordered_variant_keys:
        return {
            "success": False,
            "missing_inputs": ["genotype_matrix or g_matrix"],
            "message": (
                "Matrix-backed deterministic GBLUP inputs are required, but the resolved genotype calls "
                "do not produce a shared informative marker matrix."
            ),
            "services": [
                "calculate_breeding_value.database_training_population.observations",
                "calculate_breeding_value.database_training_population.genotypes",
            ],
            "tables": [
                "Observation",
                "ObservationVariable",
                "Germplasm",
                "Study",
                "Trial",
                "CallSet",
                "Call",
                "Variant",
            ],
            "entities": {
                "resolved_germplasm_ids": [
                    phenotype_entries[normalized_label]["label"] for normalized_label in resolved_labels
                ],
                "resolved_study_ids": resolved_study_ids,
                "resolved_trial_ids": resolved_trial_ids,
                "observation_count": phenotype_observation_count,
            },
            "scope": {
                "execution_mode": "database_training_population_gblup_resolution",
                "resolution_stage": "genotypes",
            },
        }

    phenotype_values = [
        float(sum(phenotype_entries[normalized_label]["values"]) / len(phenotype_entries[normalized_label]["values"]))
        for normalized_label in resolved_labels
    ]
    genotype_matrix = [
        [genotype_rows_by_label[normalized_label][variant_key] for variant_key in ordered_variant_keys]
        for normalized_label in resolved_labels
    ]

    return {
        "success": True,
        "phenotype_values": phenotype_values,
        "genotype_matrix": genotype_matrix,
        "germplasm_labels": [phenotype_entries[normalized_label]["label"] for normalized_label in resolved_labels],
        "retrieval_audit": {
            "services": [
                "calculate_breeding_value.database_training_population.observations",
                "calculate_breeding_value.database_training_population.genotypes",
            ],
            "tables": [
                "Observation",
                "ObservationVariable",
                "Germplasm",
                "Study",
                "Trial",
                "CallSet",
                "Call",
                "Variant",
            ],
            "entities": {
                "trait": trait,
                "method": "GBLUP",
                "crop": crop,
                "requested_germplasm_ids": [
                    str(germplasm_id)
                    for germplasm_id in (germplasm_ids or [])
                    if isinstance(germplasm_id, str) and germplasm_id.strip()
                ],
                "resolved_germplasm_ids": [
                    phenotype_entries[normalized_label]["label"] for normalized_label in resolved_labels
                ],
                "resolved_study_ids": resolved_study_ids,
                "resolved_trial_ids": resolved_trial_ids,
                "observation_count": phenotype_observation_count,
                "n_individuals": len(resolved_labels),
                "n_markers": len(ordered_variant_keys),
                "variant_ids": ordered_variant_keys[:10],
            },
            "scope": {
                "organization_id": organization_id,
                "execution_mode": "database_training_population_gblup",
                "study_id": str(study_id) if study_id is not None else None,
            },
        },
    }


def _build_genetic_diversity_message(result: dict[str, Any]) -> str:
    existing_message = result.get("message")
    if isinstance(existing_message, str):
        normalized_message = existing_message.strip()
        if normalized_message:
            return normalized_message

    sample_size = result.get("sample_size")
    loci_analyzed = result.get("loci_analyzed")
    if isinstance(sample_size, int) and isinstance(loci_analyzed, int):
        return f"Calculated genetic diversity metrics for {sample_size} samples across {loci_analyzed} loci."

    return "Calculated genetic diversity metrics for the requested population."


def _build_gblup_compute_response(
    shared: CalculateHandlerSharedContext,
    *,
    trait: str,
    heritability: float,
    germplasm_ids: list[str] | None,
    phenotype_values: list[float],
    genotype_matrix: list[list[float]] | None,
    g_matrix: list[list[float]] | None,
    retrieval_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started_at = perf_counter()
    phenotypes_array = np.asarray(phenotype_values, dtype=np.float64)
    routine_method_name = "compute_engine.compute_gblup"
    input_summary = ComputeInputSummary(
        n_observations=len(phenotypes_array),
        n_individuals=len(phenotypes_array),
        heritability=heritability,
    )

    if g_matrix is not None:
        grm_array = np.asarray(g_matrix, dtype=np.float64)
        compute_result = shared.compute_engine.compute_gblup_from_grm(
            phenotypes=phenotypes_array,
            grm=grm_array,
            heritability=heritability,
        )
        input_summary.relationship_matrix_shape = list(grm_array.shape)
        routine_method_name = "compute_engine.compute_gblup_from_grm"
    else:
        genotype_array = np.asarray(genotype_matrix, dtype=np.float64)
        compute_result = shared.compute_engine.compute_gblup(
            genotypes=genotype_array,
            phenotypes=phenotypes_array,
            heritability=heritability,
        )
        input_summary.n_markers = int(genotype_array.shape[1]) if genotype_array.ndim == 2 else None

    compute_time_ms = (perf_counter() - started_at) * 1000.0
    output = GBLUPOutput(
        breeding_values=compute_result.breeding_values.tolist(),
        reliability=compute_result.reliability.tolist() if compute_result.reliability is not None else None,
        accuracy=compute_result.accuracy.tolist() if compute_result.accuracy is not None else None,
        genetic_variance=compute_result.genetic_variance,
        error_variance=compute_result.error_variance,
        mean=float(compute_result.fixed_effects[0]) if len(compute_result.fixed_effects) > 0 else 0.0,
        converged=compute_result.converged,
    )
    success_response = build_compute_success_response(
        routine="gblup",
        output_kind="breeding_values",
        output=output,
        compute_time_ms=compute_time_ms,
        backend=shared.compute_engine.backend.value,
        execution_mode="sync",
        input_summary=input_summary,
        method_name=routine_method_name,
    ).model_dump(mode="json")

    breeding_values = output.breeding_values
    reliabilities = output.reliability or [0.0] * len(breeding_values)
    valid_germplasm_labels = [
        label.strip()
        for label in (germplasm_ids or [])
        if isinstance(label, str) and label.strip()
    ]
    labels = (
        valid_germplasm_labels
        if len(valid_germplasm_labels) == len(breeding_values)
        else [f"candidate-{idx}" for idx in range(1, len(breeding_values) + 1)]
    )
    ranked_items = sorted(
        [
            {
                "candidate": label,
                "score": breeding_value,
                "reliability": reliabilities[idx],
                "evidence_refs": [ref["entity_id"] for ref in success_response["provenance"]["evidence_refs"]],
                "calculation_method_refs": [
                    ref["entity_id"]
                    for ref in success_response["provenance"]["evidence_refs"]
                    if str(ref.get("entity_id", "")).startswith("fn:compute.")
                ],
                "rationale": (
                    f"Deterministic GBLUP breeding value for trait '{trait}' "
                    f"with reliability {reliabilities[idx]:.2f}"
                ),
            }
            for idx, (label, breeding_value) in enumerate(zip(labels, breeding_values, strict=False))
        ],
        key=lambda item: item["score"],
        reverse=True,
    )
    evidence_refs = [ref["entity_id"] for ref in success_response["provenance"]["evidence_refs"]]
    calculation_ids = [step["step_id"] for step in success_response["provenance"]["calculation_steps"]]
    confidence_score = round(sum(reliabilities) / len(reliabilities), 2) if reliabilities else 0.0
    evidence_envelope = shared.build_compute_evidence_envelope(
        routine="gblup",
        claim=f"GBLUP breeding values were computed deterministically for trait '{trait}'.",
        success_response=success_response,
        confidence_score=confidence_score,
    )

    retrieval_audit_payload = {
        "services": [],
        "tables": [],
        "entities": {
            "trait": trait,
            "method": "GBLUP",
        },
        "scope": {},
    }
    if retrieval_audit:
        retrieval_audit_payload.update(retrieval_audit)
        retrieval_audit_payload["entities"] = {
            **(
                {}
                if not isinstance(retrieval_audit_payload.get("entities"), dict)
                else retrieval_audit_payload["entities"]
            ),
        }
        retrieval_audit_payload["scope"] = {
            **(
                {}
                if not isinstance(retrieval_audit_payload.get("scope"), dict)
                else retrieval_audit_payload["scope"]
            ),
        }

    services = list(retrieval_audit_payload.get("services") or [])
    if routine_method_name not in services:
        services.append(routine_method_name)
    retrieval_audit_payload["services"] = services
    retrieval_audit_payload["tables"] = list(retrieval_audit_payload.get("tables") or [])
    retrieval_audit_payload["entities"].setdefault("trait", trait)
    retrieval_audit_payload["entities"].setdefault("method", "GBLUP")
    retrieval_audit_payload["entities"]["n_individuals"] = len(labels)
    if g_matrix is not None:
        retrieval_audit_payload["entities"]["relationship_matrix_shape"] = input_summary.relationship_matrix_shape
    else:
        retrieval_audit_payload["entities"]["n_markers"] = input_summary.n_markers

    plan_execution_summary = shared.build_single_contract_plan_execution_summary(
        function_name="calculate_breeding_value",
        domain="analytics",
        domains_involved=["genomics", "analytics"],
        completed=True,
        services=services,
        actual_outputs=["breeding_values"],
        output_counts={
            "breeding_values": len(ranked_items),
            "n_individuals": len(labels),
        },
        output_entity_ids={
            "breeding_values": shared.sample_record_identifiers(
                ranked_items,
                keys=("candidate",),
                limit=5,
            ),
        },
        output_metadata={
            "trait": trait,
            "method": "GBLUP",
            "n_individuals": len(labels),
            "n_markers": input_summary.n_markers,
            "relationship_matrix_shape": input_summary.relationship_matrix_shape,
        },
        compute_methods=[ref for ref in evidence_refs if str(ref).startswith("fn:compute.")],
    )

    return shared.with_plan_execution_summary(
        {
            "success": True,
            "function": "calculate_breeding_value",
            "result_type": "breeding_values",
            "message": (
                f"Calculated deterministic GBLUP breeding values for trait '{trait}' "
                "across the resolved training population."
            ),
            "data": ranked_items,
            "summary": {
                "method": "GBLUP",
                "trait": trait,
                "n_individuals": len(labels),
                "n_markers": input_summary.n_markers,
                "heritability": heritability,
                "genetic_variance": output.genetic_variance,
                "error_variance": output.error_variance,
                "converged": output.converged,
            },
            "calculation_method_refs": [ref for ref in evidence_refs if str(ref).startswith("fn:compute.")],
            "evidence_refs": evidence_refs,
            "calculation_ids": calculation_ids,
            "response_contract_version": COMPUTE_CONTRACT_VERSION,
            "trust_surface": COMPUTE_CONTRACT_TRUST_SURFACE,
            "data_source": "database",
            "schema_version": "1",
            "confidence_score": confidence_score,
            "data_age_seconds": None,
            "evidence_envelope": evidence_envelope,
            "retrieval_audit": retrieval_audit_payload,
        },
        plan_execution_summary,
    )


async def handle_calculate(
    executor: Any,
    function_name: str,
    params: dict[str, Any],
    *,
    shared: CalculateHandlerSharedContext,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Handle calculate_* functions for FunctionExecutor."""

    if function_name == "calculate_breeding_value":
        org_id = params.get("organization_id", 1)
        trait = params.get("trait")
        method = params.get("method", "BLUP").upper()
        blup_method_ref = "fn:calculate_breeding_value.blup_heuristic"
        heritability = params.get("heritability", 0.3)
        germplasm_ids = params.get("germplasm_ids", [])
        crop = params.get("crop")
        study_id = params.get("study_id")
        phenotype_values = params.get("phenotypes")
        genotype_matrix = params.get("genotype_matrix")
        g_matrix = params.get("g_matrix")

        if not trait:
            return shared.with_plan_execution_summary(
                {
                    "success": False,
                    "error": "trait is required",
                    "message": "Please specify a trait for breeding value calculation",
                },
                shared.build_single_contract_plan_execution_summary(
                    function_name=function_name,
                    domain="analytics",
                    completed=False,
                    output_metadata={"method": method},
                    missing_reason="a trait is required before deterministic breeding-value computation can run",
                ),
            )

        try:
            if method == "GBLUP":
                retrieval_audit: dict[str, Any] | None = None
                if g_matrix is None and genotype_matrix is None:
                    if not hasattr(executor.db, "execute"):
                        return _build_gblup_input_safe_failure(
                            shared,
                            organization_id=org_id,
                            trait=trait,
                            germplasm_ids=germplasm_ids if isinstance(germplasm_ids, list) else None,
                            crop=crop,
                            study_id=study_id,
                            missing_inputs=["phenotypes", "genotype_matrix or g_matrix"],
                            message="Matrix-backed deterministic GBLUP inputs are required; REEVU will not silently substitute BLUP.",
                            services=["calculate_breeding_value.input_validation"],
                            tables=[],
                        )

                    resolved_inputs = await shared.resolve_database_backed_gblup_inputs(
                        db=executor.db,
                        organization_id=org_id,
                        trait=trait,
                        crop=crop,
                        germplasm_ids=germplasm_ids if isinstance(germplasm_ids, list) else None,
                        study_id=study_id,
                    )
                    if not resolved_inputs.get("success"):
                        return _build_gblup_input_safe_failure(
                            shared,
                            organization_id=org_id,
                            trait=trait,
                            germplasm_ids=germplasm_ids if isinstance(germplasm_ids, list) else None,
                            crop=crop,
                            study_id=study_id,
                            missing_inputs=list(
                                resolved_inputs.get("missing_inputs") or ["phenotypes", "genotype_matrix or g_matrix"]
                            ),
                            message=str(
                                resolved_inputs.get("message")
                                or "Matrix-backed deterministic GBLUP inputs are required; REEVU will not silently substitute BLUP."
                            ),
                            services=list(
                                resolved_inputs.get("services") or ["calculate_breeding_value.input_validation"]
                            ),
                            tables=list(resolved_inputs.get("tables") or []),
                            extra_entities=(
                                resolved_inputs.get("entities") if isinstance(resolved_inputs.get("entities"), dict) else None
                            ),
                            extra_scope=(
                                resolved_inputs.get("scope") if isinstance(resolved_inputs.get("scope"), dict) else None
                            ),
                        )

                    phenotype_values = resolved_inputs.get("phenotype_values")
                    genotype_matrix = resolved_inputs.get("genotype_matrix")
                    germplasm_ids = resolved_inputs.get("germplasm_labels") or germplasm_ids
                    retrieval_audit = (
                        resolved_inputs.get("retrieval_audit")
                        if isinstance(resolved_inputs.get("retrieval_audit"), dict)
                        else None
                    )

                else:
                    retrieval_audit = {
                        "services": [],
                        "tables": [],
                        "entities": {
                            "trait": trait,
                            "method": method,
                            "crop": crop,
                            "germplasm_ids": [
                                str(germplasm_id)
                                for germplasm_id in germplasm_ids
                                if isinstance(germplasm_id, str) and germplasm_id.strip()
                            ]
                            if isinstance(germplasm_ids, list)
                            else [],
                            "study_id": str(study_id) if study_id is not None else None,
                        },
                        "scope": {
                            "organization_id": org_id,
                            "execution_mode": "matrix_backed_compute",
                        },
                    }

                if not isinstance(phenotype_values, list) or not phenotype_values:
                    return _build_gblup_input_safe_failure(
                        shared,
                        organization_id=org_id,
                        trait=trait,
                        germplasm_ids=germplasm_ids if isinstance(germplasm_ids, list) else None,
                        crop=crop,
                        study_id=study_id,
                        missing_inputs=["phenotypes"],
                        message="Provide matrix-backed deterministic inputs for GBLUP instead of falling back to BLUP.",
                        services=["calculate_breeding_value.input_validation"],
                        tables=[],
                    )

                return _build_gblup_compute_response(
                    shared,
                    trait=trait,
                    heritability=heritability,
                    germplasm_ids=germplasm_ids if isinstance(germplasm_ids, list) else None,
                    phenotype_values=phenotype_values,
                    genotype_matrix=genotype_matrix if isinstance(genotype_matrix, list) else None,
                    g_matrix=g_matrix if isinstance(g_matrix, list) else None,
                    retrieval_audit=retrieval_audit,
                )

            observations = await shared.observation_search_service.search(
                db=executor.db,
                organization_id=org_id,
                trait=trait,
                study_id=int(study_id) if study_id else None,
                limit=500,
            )

            if len(observations) < 3:
                return shared.with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Insufficient data",
                        "message": f"Need at least 3 observations for BLUP. Found {len(observations)} for trait '{trait}'",
                    },
                    shared.build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="analytics",
                        completed=False,
                        services=["observation_search_service.search"],
                        actual_outputs=["observations"] if observations else [],
                        output_counts={"observations": len(observations)},
                        output_metadata={"trait": trait, "method": method},
                        missing_reason=f"at least 3 grounded observations are required for BLUP, but only {len(observations)} matched the query scope",
                        compute_methods=[blup_method_ref],
                    ),
                )

            phenotypes = []
            for obs in observations:
                try:
                    value = float(obs.get("value", 0))
                    germ = obs.get("germplasm", {})
                    phenotypes.append(
                        {
                            "id": germ.get("id", obs.get("id")),
                            "name": germ.get("name", f"Unknown-{obs.get('id')}"),
                            "value": value,
                        }
                    )
                except (ValueError, TypeError):
                    continue

            if len(phenotypes) < 3:
                return shared.with_plan_execution_summary(
                    {
                        "success": False,
                        "error": "Insufficient numeric data",
                        "message": f"Need at least 3 numeric observations. Found {len(phenotypes)} valid records.",
                    },
                    shared.build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="analytics",
                        completed=False,
                        services=["observation_search_service.search"],
                        actual_outputs=["numeric_observations"] if phenotypes else [],
                        output_counts={"numeric_observations": len(phenotypes)},
                        output_metadata={"trait": trait, "method": method},
                        missing_reason=f"at least 3 numeric phenotype records are required for BLUP, but only {len(phenotypes)} could be coerced",
                        compute_methods=[blup_method_ref],
                    ),
                )

            result = executor.breeding_value_service.estimate_blup(
                phenotypes=phenotypes,
                trait="value",
                heritability=heritability,
            )

            if "error" in result:
                return shared.with_plan_execution_summary(
                    {
                        "success": False,
                        "error": result["error"],
                        "message": f"Breeding value calculation failed: {result['error']}",
                    },
                    shared.build_single_contract_plan_execution_summary(
                        function_name=function_name,
                        domain="analytics",
                        completed=False,
                        services=[
                            "observation_search_service.search",
                            "breeding_value_service.estimate_blup",
                        ],
                        actual_outputs=["observations"] if observations else [],
                        output_counts={"observations": len(observations)},
                        output_metadata={"trait": trait, "method": method},
                        missing_reason=str(result["error"]),
                        compute_methods=[blup_method_ref],
                    ),
                )

            observation_refs = [
                {
                    "source_type": "database",
                    "entity_id": f"db:observation:{observation_id}",
                    "query_or_method": "observation_search_service.search",
                }
                for observation in observations[:10]
                if (observation_id := observation.get("id"))
            ]
            evidence_ref_payloads = [
                *observation_refs,
                {
                    "source_type": "function",
                    "entity_id": blup_method_ref,
                    "query_or_method": "breeding_value_service.estimate_blup",
                },
            ]
            reliability_values = [
                float(item["reliability"])
                for item in result.get("breeding_values") or result.get("top_10") or []
                if isinstance(item, dict) and isinstance(item.get("reliability"), (int, float))
            ]
            confidence_score = round(sum(reliability_values) / len(reliability_values), 2) if reliability_values else 0.0
            calculation_step = {
                "step_id": blup_method_ref,
                "formula": "EBV = h^2 x (phenotype - mean)",
                "inputs": {
                    "trait": trait,
                    "heritability": result.get("heritability", heritability),
                    "n_observations": len(observations),
                    "n_individuals": result.get("n_individuals", len(phenotypes)),
                },
            }
            evidence_envelope = shared.build_compute_evidence_envelope(
                routine="blup_heuristic",
                claim=(
                    f"Heuristic BLUP breeding values were estimated deterministically for trait '{trait}' "
                    f"from {len(observations)} database observations."
                ),
                success_response={
                    "provenance": {
                        "evidence_refs": evidence_ref_payloads,
                        "calculation_steps": [calculation_step],
                    }
                },
                confidence_score=confidence_score,
            )
            evidence_refs = [ref["entity_id"] for ref in evidence_ref_payloads]
            calculation_ids = [calculation_step["step_id"]]
            success_message = (
                f"Calculated heuristic BLUP breeding values for {result.get('n_individuals', 0)} individuals "
                f"on trait '{trait}' from {len(observations)} database observations."
            )

            plan_execution_summary = shared.build_single_contract_plan_execution_summary(
                function_name=function_name,
                domain="analytics",
                completed=True,
                services=[
                    "observation_search_service.search",
                    "breeding_value_service.estimate_blup",
                ],
                actual_outputs=["breeding_values"],
                output_counts={
                    "breeding_values": result.get("n_individuals", len(phenotypes)),
                    "observations": len(observations),
                },
                output_entity_ids={
                    "breeding_values": shared.sample_record_identifiers(
                        result.get("top_10"),
                        keys=("candidate", "name"),
                        limit=5,
                    ),
                },
                output_metadata={
                    "trait": trait,
                    "method": result.get("method", method),
                    "n_individuals": result.get("n_individuals", len(phenotypes)),
                    "observation_count": len(observations),
                },
                compute_methods=[blup_method_ref],
            )

            return shared.with_plan_execution_summary(
                {
                    "success": True,
                    "function": function_name,
                    "result_type": "breeding_values",
                    "message": success_message,
                    "data": {
                        "method": result.get("method", method),
                        "trait": trait,
                        "n_individuals": result.get("n_individuals", len(phenotypes)),
                        "heritability": result.get("heritability", heritability),
                        "overall_mean": result.get("overall_mean"),
                        "genetic_variance": result.get("genetic_variance"),
                        "top_10": result.get("top_10", []),
                        "analysis_id": result.get("analysis_id"),
                        "message": success_message,
                    },
                    "calculation_method_refs": [blup_method_ref],
                    "evidence_refs": evidence_refs,
                    "calculation_ids": calculation_ids,
                    "response_contract_version": COMPUTE_CONTRACT_VERSION,
                    "trust_surface": COMPUTE_CONTRACT_TRUST_SURFACE,
                    "data_source": "database",
                    "schema_version": "1",
                    "confidence_score": confidence_score,
                    "data_age_seconds": None,
                    "evidence_envelope": evidence_envelope,
                    "retrieval_audit": {
                        "services": [
                            "observation_search_service.search",
                            "breeding_value_service.estimate_blup",
                        ],
                        "tables": ["Observation", "ObservationVariable", "Germplasm"],
                        "entities": {
                            "trait": trait,
                            "method": method,
                            "study_id": str(study_id) if study_id is not None else None,
                            "observation_count": len(observations),
                            "n_individuals": result.get("n_individuals", len(phenotypes)),
                        },
                        "scope": {
                            "organization_id": org_id,
                            "execution_mode": "database_observation_blup",
                        },
                    },
                    "demo": False,
                },
                plan_execution_summary,
            )
        except Exception as e:
            logger.error(f"Calculate breeding value failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to calculate breeding values",
            }

    if function_name == "calculate_genetic_diversity":
        from app.modules.genomics.services.genetic_diversity_service import genetic_diversity_service

        org_id = params.get("organization_id", 1)
        population_id = params.get("population_id")
        program_id = params.get("program_id")
        germplasm_ids = params.get("germplasm_ids", [])

        try:
            result = await genetic_diversity_service.calculate_diversity_metrics(
                db=executor.db,
                organization_id=org_id,
                population_id=population_id,
                program_id=int(program_id) if program_id else None,
                germplasm_ids=[int(g) for g in germplasm_ids] if germplasm_ids else None,
            )
            result_with_message = {
                **result,
                "message": _build_genetic_diversity_message(result),
            }

            return {
                "success": True,
                "function": function_name,
                "result_type": "diversity_metrics",
                "data": result_with_message,
                "demo": False,
            }
        except Exception as e:
            logger.error(f"Calculate genetic diversity failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to calculate genetic diversity",
            }

    return {"success": False, "error": f"Unhandled calculate function: {function_name}"}