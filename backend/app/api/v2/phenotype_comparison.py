"""
Phenotype Comparison API
Compare phenotypic data across germplasm entries using database-backed data.
"""

from datetime import UTC, datetime
from math import sqrt
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_organization_id
from app.core.database import get_db
from app.models.germplasm import Germplasm
from app.models.phenotyping import Observation, ObservationVariable
from app.modules.phenotyping.services.interpretation_service import (
    PhenotypeInterpretationRecord,
    normalize_trait_key,
    phenotype_interpretation_service,
    safe_float,
)
from app.modules.ai.services.reevu_provenance_validator import validate_all as validate_provenance
from app.schemas.phenotype_comparison_contract import attach_contract_metadata
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef, ReevuEnvelope, UncertaintyInfo


router = APIRouter(
    prefix="/phenotype-comparison",
    tags=["Phenotype Comparison"],
    dependencies=[Depends(get_current_user)],
)


class ObservationsRequest(BaseModel):
    germplasm_ids: list[str]
    traits: list[str] | None = None


class CompareRequest(BaseModel):
    germplasm_ids: list[str]
    check_id: str | None = None


def _external_germplasm_id(germplasm: Germplasm) -> str:
    return germplasm.germplasm_db_id or str(germplasm.id)


def _is_check_entry(germplasm: Germplasm) -> bool:
    combined_name = " ".join(
        filter(None, [germplasm.germplasm_name, germplasm.default_display_name])
    ).lower()
    return "check" in combined_name or "control" in combined_name


def _normalize_trait_name(name: str | None) -> str:
    return normalize_trait_key(name)


def _trait_matches(observation: Observation, traits: set[str] | None) -> bool:
    if not traits:
        return True

    variable = observation.observation_variable
    if not variable:
        return False

    candidates = {
        _normalize_trait_name(variable.observation_variable_name),
        _normalize_trait_name(variable.trait_name),
        (variable.observation_variable_db_id or "").lower(),
        (variable.trait_db_id or "").lower(),
    }
    return any(candidate in traits for candidate in candidates if candidate)


async def _load_germplasm_by_external_ids(
    db: AsyncSession,
    organization_id: int,
    germplasm_ids: list[str],
) -> list[Germplasm]:
    if not germplasm_ids:
        return []

    numeric_ids = [int(germplasm_id) for germplasm_id in germplasm_ids if germplasm_id.isdigit()]
    stmt = select(Germplasm).where(Germplasm.organization_id == organization_id)

    if numeric_ids:
        stmt = stmt.where(
            or_(
                Germplasm.germplasm_db_id.in_(germplasm_ids),
                Germplasm.id.in_(numeric_ids),
            )
        )
    else:
        stmt = stmt.where(Germplasm.germplasm_db_id.in_(germplasm_ids))

    result = await db.execute(stmt)
    germplasm_rows = result.scalars().all()

    by_external_id = {_external_germplasm_id(germplasm): germplasm for germplasm in germplasm_rows}
    by_internal_id = {str(germplasm.id): germplasm for germplasm in germplasm_rows}

    ordered_rows: list[Germplasm] = []
    seen_ids: set[int] = set()
    for germplasm_id in germplasm_ids:
        germplasm = by_external_id.get(germplasm_id) or by_internal_id.get(germplasm_id)
        if germplasm and germplasm.id not in seen_ids:
            ordered_rows.append(germplasm)
            seen_ids.add(germplasm.id)

    return ordered_rows


async def _load_observations(
    db: AsyncSession,
    organization_id: int,
    germplasm_rows: list[Germplasm],
    traits: list[str] | None = None,
) -> list[Observation]:
    if not germplasm_rows:
        return []

    trait_filters = {_normalize_trait_name(trait) for trait in traits or [] if trait}
    stmt = (
        select(Observation)
        .options(
            selectinload(Observation.observation_variable),
            selectinload(Observation.germplasm),
        )
        .where(Observation.organization_id == organization_id)
        .where(Observation.germplasm_id.in_([germplasm.id for germplasm in germplasm_rows]))
        .order_by(Observation.germplasm_id.asc(), Observation.observation_time_stamp.desc())
    )

    result = await db.execute(stmt)
    observations = result.scalars().all()
    return [observation for observation in observations if _trait_matches(observation, trait_filters)]


def _observation_to_response(observation: Observation) -> dict[str, Any]:
    variable = observation.observation_variable
    germplasm = observation.germplasm
    return {
        "observationDbId": observation.observation_db_id or str(observation.id),
        "germplasmDbId": _external_germplasm_id(germplasm) if germplasm else str(observation.germplasm_id),
        "observationVariableName": variable.observation_variable_name if variable else None,
        "observationVariableDbId": variable.observation_variable_db_id if variable else None,
        "value": observation.value or "",
        "observationTimeStamp": observation.observation_time_stamp,
    }


def _aggregate_traits(
    observations: list[Observation],
    germplasm_rows: list[Germplasm],
) -> tuple[dict[str, dict[str, float]], dict[str, str], dict[str, dict[str, str | None]]]:
    values_by_germplasm: dict[str, dict[str, list[float]]] = {}
    names_by_germplasm: dict[str, str] = {}
    trait_metadata: dict[str, dict[str, str | None]] = {}

    valid_germplasm_ids = {_external_germplasm_id(germplasm) for germplasm in germplasm_rows}
    for germplasm in germplasm_rows:
        external_id = _external_germplasm_id(germplasm)
        names_by_germplasm[external_id] = germplasm.germplasm_name
        values_by_germplasm.setdefault(external_id, {})

    for observation in observations:
        germplasm = observation.germplasm
        variable = observation.observation_variable
        numeric_value = safe_float(observation.value)
        if not germplasm or not variable or numeric_value is None:
            continue

        external_id = _external_germplasm_id(germplasm)
        if external_id not in valid_germplasm_ids:
            continue

        trait_key = _normalize_trait_name(variable.observation_variable_name or variable.trait_name)
        if not trait_key:
            continue

        trait_metadata.setdefault(
            trait_key,
            {
                "name": variable.observation_variable_name or variable.trait_name,
                "unit": variable.scale_name or variable.data_type,
            },
        )
        values_by_germplasm.setdefault(external_id, {}).setdefault(trait_key, []).append(numeric_value)

    aggregated = {
        germplasm_id: {
            trait_key: round(sum(values) / len(values), 4)
            for trait_key, values in trait_map.items()
            if values
        }
        for germplasm_id, trait_map in values_by_germplasm.items()
    }

    return aggregated, names_by_germplasm, trait_metadata


def _build_interpretation_records(
    observations: list[Observation],
    germplasm_rows: list[Germplasm],
) -> list[PhenotypeInterpretationRecord]:
    valid_germplasm_ids = {_external_germplasm_id(germplasm) for germplasm in germplasm_rows}
    records: list[PhenotypeInterpretationRecord] = []

    for observation in observations:
        germplasm = observation.germplasm
        variable = observation.observation_variable
        numeric_value = safe_float(observation.value)
        if not germplasm or not variable or numeric_value is None:
            continue

        external_id = _external_germplasm_id(germplasm)
        if external_id not in valid_germplasm_ids:
            continue

        trait_name = variable.observation_variable_name or variable.trait_name or variable.observation_variable_db_id
        trait_key = normalize_trait_key(trait_name)
        if not trait_key:
            continue

        role_hint = "baseline_candidate" if _is_check_entry(germplasm) else "candidate"
        records.append(
            PhenotypeInterpretationRecord(
                entity_db_id=external_id,
                entity_name=germplasm.germplasm_name or external_id,
                trait_key=trait_key,
                trait_name=trait_name or trait_key,
                unit=variable.scale_name or variable.data_type,
                value=numeric_value,
                observation_ref=observation.observation_db_id or f"db:observation:{observation.id}",
                role_hint=role_hint,
            )
        )

    return records


def _build_trait_summary(aggregated: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    trait_values: dict[str, list[float]] = {}
    for trait_map in aggregated.values():
        for trait_key, value in trait_map.items():
            trait_values.setdefault(trait_key, []).append(value)

    summary: dict[str, dict[str, float]] = {}
    for trait_key, values in trait_values.items():
        mean_value = sum(values) / len(values)
        variance = (
            sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
            if len(values) > 1
            else 0.0
        )
        summary[trait_key] = {
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "mean": round(mean_value, 4),
            "std": round(sqrt(variance), 4),
        }

    return summary


def _parse_observation_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        try:
            parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return None


def _extract_phenotype_claims(scope: str, interpretation: Any) -> list[str]:
    entity_count, trait_count, observation_count = _derive_interpretation_counts(interpretation)
    claims = [
        f"Phenotype comparison scope {scope} covers {entity_count} entities, {trait_count} traits, and {observation_count} observations.",
    ]

    ranking = getattr(interpretation, "ranking", []) or []
    if ranking:
        leader = ranking[0]
        leader_name = getattr(leader, "entity_name", getattr(leader, "entity_db_id", "unknown"))
        leader_score = getattr(leader, "score", None)
        trait_name = getattr(leader, "score_trait_name", getattr(leader, "score_trait_key", None))
        if leader_score is not None and trait_name:
            claims.append(
                f"Top-ranked entry {leader_name} leads on {trait_name} with score {leader_score}."
            )

    methodology = getattr(interpretation, "methodology", None)
    if methodology:
        claims.append(f"Interpretation methodology: {methodology}.")

    return claims[:4]


def _build_phenotype_evidence_refs(observations: list[Observation], interpretation: Any) -> list[EvidenceRef]:
    freshness_by_ref: dict[str, float | None] = {}
    observation_ref_ids: set[str] = set()
    for observation in observations:
        observation_ref = observation.observation_db_id or f"db:observation:{observation.id}"
        observation_ref_ids.add(observation_ref)
        observed_at = _parse_observation_timestamp(observation.observation_time_stamp)
        freshness = None
        if observed_at is not None:
            freshness = max((datetime.now(UTC) - observed_at).total_seconds(), 0.0)
        freshness_by_ref[observation_ref] = freshness

    ranking_refs = [ref for item in (getattr(interpretation, "ranking", []) or []) for ref in getattr(item, "evidence_refs", [])]
    all_refs = sorted({*(getattr(interpretation, "evidence_refs", []) or []), *ranking_refs})
    return [
        EvidenceRef(
            source_type="database" if str(ref).startswith("db:") or str(ref) in observation_ref_ids else "function",
            entity_id=str(ref),
            query_or_method="phenotype_comparison.query",
            freshness_seconds=freshness_by_ref.get(str(ref)),
        )
        for ref in all_refs
    ]


def _derive_interpretation_counts(interpretation: Any) -> tuple[int, int, int]:
    summary = getattr(interpretation, "summary", None)
    entity_count = getattr(summary, "entity_count", None)
    trait_count = getattr(summary, "trait_count", None)
    observation_count = getattr(summary, "observation_count", None)

    entities = getattr(interpretation, "entities", []) or []
    if entity_count in (None, 0) and entities:
        entity_count = len(entities)

    if trait_count in (None, 0):
        trait_keys = {
            getattr(metric, "trait_key", None)
            for entity in entities
            for metric in getattr(entity, "metrics", []) or []
            if getattr(metric, "trait_key", None)
        }
        ranking = getattr(interpretation, "ranking", []) or []
        trait_keys.update(
            getattr(item, "score_trait_key", None)
            for item in ranking
            if getattr(item, "score_trait_key", None)
        )
        trait_count = len(trait_keys)

    if observation_count in (None, 0):
        observation_count = sum(
            getattr(metric, "observation_count", 0)
            for entity in entities
            for metric in getattr(entity, "metrics", []) or []
        )

    return entity_count or 0, trait_count or 0, observation_count or 0


def _build_phenotype_calculation_steps(interpretation: Any) -> list[CalculationStep]:
    return [
        CalculationStep(step_id=str(calc_id))
        for calc_id in (getattr(interpretation, "calculation_ids", []) or [])
    ]


def _build_phenotype_evidence_envelope(
    *,
    scope: str,
    observations: list[Observation],
    interpretation: Any,
) -> ReevuEnvelope:
    entity_count, trait_count, observation_count = _derive_interpretation_counts(interpretation)

    confidence = 0.35
    if observation_count > 0:
        confidence += 0.25
    if trait_count > 0:
        confidence += 0.15
    if entity_count >= 2:
        confidence += 0.15
    if not (getattr(interpretation, "warnings", []) or []):
        confidence += 0.1

    missing_data: list[str] = []
    if observation_count == 0:
        missing_data.append("numeric_observations")
    if trait_count == 0:
        missing_data.append("trait_coverage")
    if entity_count < 2:
        missing_data.append("comparison_subjects")

    envelope = ReevuEnvelope(
        claims=_extract_phenotype_claims(scope, interpretation),
        evidence_refs=_build_phenotype_evidence_refs(observations, interpretation),
        calculation_steps=_build_phenotype_calculation_steps(interpretation),
        uncertainty=UncertaintyInfo(
            confidence=round(min(confidence, 0.95), 2),
            missing_data=missing_data,
        ),
        policy_flags=list(getattr(interpretation, "warnings", []) or []),
    )
    provenance_flags = validate_provenance(envelope)
    if provenance_flags:
        envelope = envelope.model_copy(
            update={"policy_flags": envelope.policy_flags + provenance_flags}
        )
    return envelope


@router.get("/germplasm")
async def get_germplasm_for_comparison(
    limit: int = Query(default=20, le=100),
    search: str | None = None,
    species: str | None = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get germplasm entries available for comparison."""
    stmt = select(Germplasm).where(Germplasm.organization_id == organization_id)

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Germplasm.germplasm_name.ilike(search_pattern),
                Germplasm.default_display_name.ilike(search_pattern),
                Germplasm.germplasm_db_id.ilike(search_pattern),
            )
        )

    if species:
        stmt = stmt.where(Germplasm.species.ilike(f"%{species}%"))

    stmt = stmt.order_by(Germplasm.germplasm_name.asc()).limit(limit)
    result = await db.execute(stmt)
    germplasm_rows = result.scalars().all()

    data = [
        {
            "germplasmDbId": _external_germplasm_id(germplasm),
            "germplasmName": germplasm.germplasm_name,
            "defaultDisplayName": germplasm.default_display_name,
            "species": germplasm.species,
            "isCheck": _is_check_entry(germplasm),
        }
        for germplasm in germplasm_rows
    ]

    return attach_contract_metadata({
        "result": {"data": data},
        "metadata": {
            "pagination": {
                "currentPage": 0,
                "pageSize": limit,
                "totalCount": len(data),
                "totalPages": 1,
            }
        },
    }, scope="germplasm")


@router.post("/observations")
async def get_observations_for_germplasm(
    request: ObservationsRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get observations for selected germplasm entries."""
    germplasm_rows = await _load_germplasm_by_external_ids(
        db, organization_id, request.germplasm_ids
    )
    observations = await _load_observations(
        db, organization_id, germplasm_rows, request.traits
    )

    return attach_contract_metadata({
        "result": {"data": [_observation_to_response(observation) for observation in observations]},
        "metadata": {
            "pagination": {
                "currentPage": 0,
                "pageSize": len(observations),
                "totalCount": len(observations),
                "totalPages": 1,
            }
        },
    }, scope="observations")


@router.get("/traits")
async def get_comparison_traits(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get available traits for comparison."""
    stmt = (
        select(ObservationVariable)
        .where(ObservationVariable.organization_id == organization_id)
        .order_by(ObservationVariable.observation_variable_name.asc())
        .limit(200)
    )
    result = await db.execute(stmt)
    variables = result.scalars().all()

    return attach_contract_metadata({
        "data": [
            {
                "id": variable.observation_variable_db_id or str(variable.id),
                "name": variable.observation_variable_name,
                "unit": variable.scale_name or variable.data_type or "value",
                "higher_is_better": True,
            }
            for variable in variables
        ]
    }, scope="traits")


@router.post("/compare")
async def compare_germplasm(
    request: CompareRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Compare germplasm entries against a selected or inferred check variety."""
    germplasm_rows = await _load_germplasm_by_external_ids(
        db, organization_id, request.germplasm_ids
    )
    observations = await _load_observations(db, organization_id, germplasm_rows)
    check_germplasm = None
    baseline_selection = "explicit_check_id"
    if request.check_id:
        check_germplasm = next(
            (
                germplasm
                for germplasm in germplasm_rows
                if _external_germplasm_id(germplasm) == request.check_id or str(germplasm.id) == request.check_id
            ),
            None,
        )
    if check_germplasm is None:
        baseline_selection = "inferred_check_entry"
        check_germplasm = next((germplasm for germplasm in germplasm_rows if _is_check_entry(germplasm)), None)
    if check_germplasm is None and germplasm_rows:
        baseline_selection = "first_requested_entry"
        check_germplasm = germplasm_rows[0]

    check_external_id = _external_germplasm_id(check_germplasm) if check_germplasm else None
    interpretation = phenotype_interpretation_service.build_interpretation(
        scope="germplasm_comparison",
        records=_build_interpretation_records(observations, germplasm_rows),
        methodology="database_observation_means_by_germplasm",
        entity_order=[_external_germplasm_id(germplasm) for germplasm in germplasm_rows],
        baseline_entity_id=check_external_id,
        baseline_entity_name=check_germplasm.germplasm_name if check_germplasm else None,
        baseline_selection=baseline_selection,
        evidence_refs=[f"db:germplasm:{_external_germplasm_id(germplasm)}" for germplasm in germplasm_rows],
    )
    evidence_envelope = _build_phenotype_evidence_envelope(
        scope="compare",
        observations=observations,
        interpretation=interpretation,
    )

    results = []
    for entity in interpretation.entities:
        traits = {metric.trait_key: metric.mean for metric in entity.metrics}
        vs_check = {
            metric.trait_key: metric.delta_percent_vs_baseline
            for metric in entity.metrics
            if entity.entity_db_id != check_external_id and metric.delta_percent_vs_baseline is not None
        }
        results.append(
            {
                "germplasm_id": entity.entity_db_id,
                "germplasm_name": entity.entity_name,
                "traits": traits,
                "vs_check": vs_check or None,
            }
        )

    return attach_contract_metadata({
        "data": results,
        "check_id": check_external_id,
        "check_name": check_germplasm.germplasm_name if check_germplasm else None,
        "interpretation": interpretation.model_dump(),
        "evidence_refs": interpretation.evidence_refs,
        "calculation_ids": interpretation.calculation_ids,
        "evidence_envelope": evidence_envelope.model_dump(),
    }, scope="compare")


@router.get("/statistics")
async def get_comparison_statistics(
    germplasm_ids: str | None = None,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get summary statistics for phenotype comparison."""
    selected_ids = [germplasm_id.strip() for germplasm_id in germplasm_ids.split(",")] if germplasm_ids else []

    if selected_ids:
        germplasm_rows = await _load_germplasm_by_external_ids(db, organization_id, selected_ids)
    else:
        stmt = select(Germplasm).where(Germplasm.organization_id == organization_id).limit(100)
        result = await db.execute(stmt)
        germplasm_rows = result.scalars().all()

    observations = await _load_observations(db, organization_id, germplasm_rows)
    interpretation = phenotype_interpretation_service.build_interpretation(
        scope="germplasm_comparison_statistics",
        records=_build_interpretation_records(observations, germplasm_rows),
        methodology="database_observation_means_by_germplasm",
        entity_order=[_external_germplasm_id(germplasm) for germplasm in germplasm_rows],
        evidence_refs=[f"db:germplasm:{_external_germplasm_id(germplasm)}" for germplasm in germplasm_rows],
    )
    evidence_envelope = _build_phenotype_evidence_envelope(
        scope="statistics",
        observations=observations,
        interpretation=interpretation,
    )
    trait_summary = {
        trait.trait_key: {
            "min": trait.min,
            "max": trait.max,
            "mean": trait.mean,
            "std": trait.std,
        }
        for trait in interpretation.traits
    }

    return attach_contract_metadata({
        "total_germplasm": len(germplasm_rows),
        "total_traits": interpretation.summary.trait_count,
        "trait_summary": trait_summary,
        "interpretation": interpretation.model_dump(),
        "evidence_refs": interpretation.evidence_refs,
        "calculation_ids": interpretation.calculation_ids,
        "evidence_envelope": evidence_envelope.model_dump(),
    }, scope="statistics")
