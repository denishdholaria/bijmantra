"""
Trial Summary API
Comprehensive trial analysis and reporting

Converted to database queries per Zero Mock Data Policy (Session 77).
Queries Trial, Study, Observation tables for real data.
"""

from collections import defaultdict
from datetime import UTC, datetime
from math import sqrt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_organization_id
from app.core.database import get_db
from app.models.core import Location, Study, Trial
from app.models.germplasm import Germplasm
from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable
from app.modules.phenotyping.services.interpretation_service import (
    PhenotypeInterpretationRecord,
    normalize_trait_key,
    phenotype_interpretation_service,
    safe_float,
)
from app.schemas.phenotype_interpretation import PhenotypeInterpretation
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef, ReevuEnvelope, UncertaintyInfo
from app.schemas.trial_summary_contract import TrialSummaryContractMetadata


router = APIRouter(prefix="/trial-summary", tags=["Trial Summary"], dependencies=[Depends(get_current_user)])


class TrialInfo(BaseModel):
    trialDbId: str
    trialName: str
    programDbId: str | None = None
    programName: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    locations: int = 0
    entries: int = 0
    traits: int = 0
    observations: int = 0
    completionRate: float = 0.0
    leadScientist: str | None = None


class TopPerformer(BaseModel):
    rank: int
    germplasmDbId: str
    germplasmName: str
    yield_value: float
    change_percent: str
    traits: list[str]


class TraitSummary(BaseModel):
    trait: str
    mean: float
    cv: float
    lsd: float | None = None
    fValue: float | None = None
    significance: str | None = None


class LocationPerformance(BaseModel):
    locationDbId: str
    locationName: str
    entries: int
    meanYield: float
    cv: float
    completionRate: float


class TrialSummaryResponse(BaseModel):
    trial: TrialInfo
    topPerformers: list[TopPerformer]
    traitSummary: list[TraitSummary]
    locationPerformance: list[LocationPerformance]
    statistics: dict
    interpretation: PhenotypeInterpretation
    evidence_refs: list[str]
    calculation_ids: list[str]
    response_contract_version: str = TrialSummaryContractMetadata.model_fields["response_contract_version"].default
    trust_surface: str = TrialSummaryContractMetadata.model_fields["trust_surface"].default
    data_source: str = TrialSummaryContractMetadata.model_fields["data_source"].default
    schema_version: str = TrialSummaryContractMetadata.model_fields["schema_version"].default
    confidence_score: float | None = TrialSummaryContractMetadata.model_fields["confidence_score"].default
    data_age_seconds: int | None = TrialSummaryContractMetadata.model_fields["data_age_seconds"].default
    calculation_method_refs: list[str] = TrialSummaryContractMetadata.model_fields["calculation_method_refs"].default_factory()
    evidence_envelope: ReevuEnvelope | None = None


def _serialize_date(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _parse_timestamp(value: Any) -> datetime | None:
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


async def _resolve_trial(
    db: AsyncSession,
    organization_id: int,
    trial_id: str,
) -> Trial | None:
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    )
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()

    if not trial and trial_id.isdigit():
        stmt = select(Trial).where(
            and_(
                Trial.organization_id == organization_id,
                Trial.id == int(trial_id),
            )
        )
        result = await db.execute(stmt)
        trial = result.scalar_one_or_none()

    return trial


def _normalize_trait_key(name: str | None) -> str:
    return normalize_trait_key(name)


def _round_or_none(value: float | None, digits: int = 4) -> float | None:
    return round(value, digits) if value is not None else None


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _sample_variance(values: list[float], mean_value: float | None = None) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    center = mean_value if mean_value is not None else sum(values) / len(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def _coefficient_of_variation(values: list[float]) -> float | None:
    mean_value = _mean(values)
    variance = _sample_variance(values, mean_value)
    if mean_value in (None, 0) or variance is None:
        return None
    return sqrt(variance) / mean_value * 100


async def _load_trial_numeric_records(
    db: AsyncSession,
    organization_id: int,
    trial_internal_id: int,
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Observation.id.label("observation_id"),
            Observation.observation_db_id.label("observation_db_id"),
            Observation.value.label("value"),
            Observation.germplasm_id.label("germplasm_id"),
            ObservationUnit.entry_type.label("entry_type"),
            ObservationVariable.observation_variable_name.label("observation_variable_name"),
            ObservationVariable.trait_name.label("trait_name"),
            ObservationVariable.observation_variable_db_id.label("trait_db_id"),
            ObservationVariable.scale_name.label("trait_unit"),
            ObservationVariable.data_type.label("trait_data_type"),
            Germplasm.germplasm_name.label("germplasm_name"),
            Germplasm.germplasm_db_id.label("germplasm_db_id"),
            Study.id.label("study_id"),
            Location.id.label("location_id"),
            Location.location_name.label("location_name"),
            Observation.observation_time_stamp.label("observation_time_stamp"),
            Observation.updated_at.label("updated_at"),
            Observation.created_at.label("created_at"),
        )
        .join(Observation.observation_unit)
        .join(ObservationUnit.study)
        .join(Observation.observation_variable)
        .outerjoin(Observation.germplasm)
        .outerjoin(Study.location)
        .where(Observation.organization_id == organization_id)
        .where(Study.organization_id == organization_id)
        .where(Study.trial_id == trial_internal_id)
    )
    result = await db.execute(stmt)

    records: list[dict[str, Any]] = []
    for row in result.all():
        numeric_value = safe_float(row.value)
        if numeric_value is None:
            continue

        trait_name = row.observation_variable_name or row.trait_name or row.trait_db_id
        if not trait_name:
            continue

        germplasm_key = row.germplasm_db_id or (str(row.germplasm_id) if row.germplasm_id else None)
        location_key = str(row.location_id) if row.location_id is not None else f"study:{row.study_id}"
        records.append(
            {
                "value": numeric_value,
                "trait_name": trait_name,
                "trait_key": _normalize_trait_key(trait_name),
                "trait_unit": row.trait_unit or row.trait_data_type,
                "germplasm_key": germplasm_key,
                "germplasm_name": row.germplasm_name or germplasm_key or "Unknown",
                "entry_type": (row.entry_type or "").lower(),
                "study_id": row.study_id,
                "location_key": location_key,
                "location_name": row.location_name or "Unassigned Location",
                "observation_ref": row.observation_db_id or f"db:observation:{row.observation_id}",
                "observed_at": row.observation_time_stamp,
                "updated_at": row.updated_at,
                "created_at": row.created_at,
            }
        )

    return records


def _group_records_by_trait(records: list[dict[str, Any]]) -> dict[str, dict[str, list[float]]]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        germplasm_key = record.get("germplasm_key")
        trait_name = record.get("trait_name")
        if germplasm_key and trait_name:
            grouped[trait_name][germplasm_key].append(record["value"])
    return {trait: dict(germplasm_groups) for trait, germplasm_groups in grouped.items()}


def _select_primary_trait(trait_groups: dict[str, dict[str, list[float]]]) -> str | None:
    if not trait_groups:
        return None

    def priority(trait_name: str) -> tuple[int, int, int, str]:
        normalized = _normalize_trait_key(trait_name)
        exact_yield = int(normalized in {"yield", "grain_yield", "seed_yield", "plot_yield"})
        any_yield = int("yield" in normalized)
        observation_count = sum(len(values) for values in trait_groups[trait_name].values())
        return (exact_yield, any_yield, observation_count, trait_name)

    return max(trait_groups.keys(), key=priority)


def _anova_metrics(grouped_values: dict[str, list[float]]) -> dict[str, Any]:
    non_empty_groups = {key: values for key, values in grouped_values.items() if values}
    group_count = len(non_empty_groups)
    observation_count = sum(len(values) for values in non_empty_groups.values())
    if group_count < 2 or observation_count <= group_count:
        return {
            "f_value": None,
            "lsd": None,
            "significance": None,
            "genetic_variance": None,
            "error_variance": None,
            "heritability": None,
            "selection_intensity": None,
            "expected_gain": None,
            "anova": None,
        }

    means = {key: sum(values) / len(values) for key, values in non_empty_groups.items()}
    all_values = [value for values in non_empty_groups.values() for value in values]
    grand_mean = sum(all_values) / len(all_values)
    ss_between = sum(len(non_empty_groups[key]) * (means[key] - grand_mean) ** 2 for key in non_empty_groups)
    ss_within = sum(
        sum((value - means[key]) ** 2 for value in values)
        for key, values in non_empty_groups.items()
    )
    df_between = group_count - 1
    df_within = observation_count - group_count
    ms_between = ss_between / df_between if df_between > 0 else None
    ms_within = ss_within / df_within if df_within > 0 else None
    f_value = (ms_between / ms_within) if ms_between is not None and ms_within not in (None, 0) else None
    average_replicates = observation_count / group_count if group_count else None
    lsd = (
        1.96 * sqrt((2 * ms_within) / average_replicates)
        if ms_within is not None and average_replicates not in (None, 0)
        else None
    )
    mean_range = max(means.values()) - min(means.values()) if means else None
    significance = None
    if lsd is not None and mean_range is not None:
        significance = "*" if mean_range > lsd else "ns"

    genetic_variance = None
    heritability = None
    if ms_between is not None and ms_within is not None and average_replicates not in (None, 0):
        genetic_variance = max((ms_between - ms_within) / average_replicates, 0.0)
        denominator = genetic_variance + (ms_within / average_replicates)
        heritability = genetic_variance / denominator if denominator > 0 else None

    selection_intensity = 1.755 if group_count >= 10 else None
    phenotypic_std_dev = sqrt(_sample_variance(all_values, grand_mean) or 0.0) if len(all_values) > 1 else None
    expected_gain = None
    if selection_intensity is not None and heritability is not None and phenotypic_std_dev is not None:
        expected_gain = selection_intensity * heritability * phenotypic_std_dev

    return {
        "f_value": f_value,
        "lsd": lsd,
        "significance": significance,
        "genetic_variance": genetic_variance,
        "error_variance": ms_within,
        "heritability": heritability,
        "selection_intensity": selection_intensity,
        "expected_gain": expected_gain,
        "anova": {
            "df_between": df_between,
            "df_within": df_within,
            "ss_between": round(ss_between, 4),
            "ss_within": round(ss_within, 4),
            "ms_between": _round_or_none(ms_between),
            "ms_within": _round_or_none(ms_within),
        },
    }


def _derive_trial_summary_contract_metadata(
    *,
    records: list[dict[str, Any]],
    interpretation: PhenotypeInterpretation,
) -> TrialSummaryContractMetadata:
    latest_timestamp: datetime | None = None
    for record in records:
        for key in ("observed_at", "updated_at", "created_at"):
            parsed = _parse_timestamp(record.get(key))
            if parsed is not None and (latest_timestamp is None or parsed > latest_timestamp):
                latest_timestamp = parsed

    data_age_seconds: int | None = None
    if latest_timestamp is not None:
        delta_seconds = (datetime.now(UTC) - latest_timestamp).total_seconds()
        data_age_seconds = max(int(delta_seconds), 0)

    summary = interpretation.summary
    confidence_score = 0.35
    if summary.observation_count > 0:
        confidence_score += 0.25
    if summary.trait_count > 0:
        confidence_score += 0.15
    if summary.entity_count >= 2:
        confidence_score += 0.15
    if not interpretation.warnings:
        confidence_score += 0.1

    method_refs = [
        "fn:trial_summary.mean",
        "fn:trial_summary.coefficient_of_variation",
        "fn:trial_summary.baseline_selection",
    ]
    if summary.entity_count >= 2 and summary.observation_count > summary.entity_count:
        method_refs.append("fn:trial_summary.anova")

    return TrialSummaryContractMetadata(
        confidence_score=round(min(confidence_score, 0.95), 2),
        data_age_seconds=data_age_seconds,
        calculation_method_refs=method_refs,
    )


def _extract_trial_claims(
    *,
    trial_info: TrialInfo,
    top_performers: list[TopPerformer],
    statistics: dict[str, Any],
    interpretation: PhenotypeInterpretation,
) -> list[str]:
    claims: list[str] = []
    claims.append(
        f"Trial {trial_info.trialName} includes {trial_info.observations} numeric observations across {trial_info.entries} entries and {trial_info.locations} locations."
    )

    primary_trait = statistics.get("primary_trait") or interpretation.primary_trait_name
    grand_mean = statistics.get("grand_mean")
    if primary_trait and grand_mean is not None:
        claims.append(
            f"Primary trait {primary_trait} has a grand mean of {grand_mean} across the observed trial dataset."
        )

    if top_performers:
        leader = top_performers[0]
        claims.append(
            f"Top-ranked entry {leader.germplasmName} recorded a score of {leader.yield_value} with change versus baseline of {leader.change_percent}."
        )

    heritability = statistics.get("heritability")
    if heritability is not None:
        claims.append(
            f"Estimated heritability for the primary trait is {heritability}."
        )

    return claims[:4]


def _build_trial_evidence_refs(
    *,
    records: list[dict[str, Any]],
    interpretation: PhenotypeInterpretation,
    data_age_seconds: int | None,
) -> list[EvidenceRef]:
    latest_by_entity: dict[str, float | None] = {}
    for record in records:
        observation_ref = record.get("observation_ref")
        observed_at = None
        for key in ("observed_at", "updated_at", "created_at"):
            parsed = _parse_timestamp(record.get(key))
            if parsed is not None:
                observed_at = max(observed_at, parsed) if observed_at is not None else parsed
        freshness_seconds = None
        if observed_at is not None:
            freshness_seconds = max((datetime.now(UTC) - observed_at).total_seconds(), 0.0)
        if observation_ref:
            latest_by_entity[observation_ref] = freshness_seconds

    all_refs = sorted(
        {
            *interpretation.evidence_refs,
            *(ref for item in interpretation.ranking for ref in item.evidence_refs),
        }
    )
    return [
        EvidenceRef(
            source_type="database" if ref.startswith("db:") else "function",
            entity_id=ref,
            query_or_method="trial_summary.query",
            freshness_seconds=latest_by_entity.get(ref, float(data_age_seconds) if data_age_seconds is not None else None),
        )
        for ref in all_refs
    ]


def _build_trial_calculation_steps(
    *,
    statistics: dict[str, Any],
    method_refs: list[str],
    trial_info: TrialInfo,
) -> list[CalculationStep]:
    steps: list[CalculationStep] = []
    for method_ref in method_refs:
        if method_ref == "fn:trial_summary.mean":
            steps.append(
                CalculationStep(
                    step_id=method_ref,
                    formula="sum(values) / n",
                    inputs={
                        "observation_count": trial_info.observations,
                        "primary_trait": statistics.get("primary_trait"),
                    },
                )
            )
        elif method_ref == "fn:trial_summary.coefficient_of_variation":
            steps.append(
                CalculationStep(
                    step_id=method_ref,
                    formula="(sample_std / mean) * 100",
                    inputs={
                        "grand_mean": statistics.get("grand_mean"),
                        "overall_cv": statistics.get("overall_cv"),
                    },
                )
            )
        elif method_ref == "fn:trial_summary.baseline_selection":
            steps.append(
                CalculationStep(
                    step_id=method_ref,
                    formula="select first check or control entry ordered deterministically",
                    inputs={"entry_count": trial_info.entries, "location_count": trial_info.locations},
                )
            )
        elif method_ref == "fn:trial_summary.anova":
            steps.append(
                CalculationStep(
                    step_id=method_ref,
                    formula="F = MS_between / MS_within",
                    inputs=statistics.get("anova"),
                )
            )
    return steps


def _derive_trial_missing_data(
    *,
    trial_info: TrialInfo,
    interpretation: PhenotypeInterpretation,
    statistics: dict[str, Any],
) -> list[str]:
    missing_data: list[str] = []
    if trial_info.observations == 0:
        missing_data.append("numeric_observations")
    if trial_info.completionRate < 100:
        missing_data.append("incomplete_observation_matrix")
    if not interpretation.ranking:
        missing_data.append("ranked_entities")
    if statistics.get("anova") is None:
        missing_data.append("anova_support")
    return missing_data


def _derive_trial_policy_flags(
    *,
    trial_info: TrialInfo,
    interpretation: PhenotypeInterpretation,
    contract_metadata: TrialSummaryContractMetadata,
) -> list[str]:
    policy_flags: list[str] = []
    if contract_metadata.data_age_seconds is not None and contract_metadata.data_age_seconds > 90 * 24 * 3600:
        policy_flags.append("stale_evidence")
    if interpretation.summary.entity_count < 3:
        policy_flags.append("low_entity_count")
    if interpretation.summary.observation_count < max(interpretation.summary.entity_count * max(interpretation.summary.trait_count, 1), 1):
        policy_flags.append("low_observation_density")
    if trial_info.completionRate < 75:
        policy_flags.append("incomplete_observation_matrix")
    if interpretation.warnings:
        policy_flags.extend(f"interpretation_warning:{warning}" for warning in interpretation.warnings)
    return policy_flags


def _build_trial_evidence_envelope(
    *,
    trial_info: TrialInfo,
    top_performers: list[TopPerformer],
    statistics: dict[str, Any],
    records: list[dict[str, Any]],
    interpretation: PhenotypeInterpretation,
    contract_metadata: TrialSummaryContractMetadata,
) -> ReevuEnvelope:
    missing_data = _derive_trial_missing_data(
        trial_info=trial_info,
        interpretation=interpretation,
        statistics=statistics,
    )
    return ReevuEnvelope(
        claims=_extract_trial_claims(
            trial_info=trial_info,
            top_performers=top_performers,
            statistics=statistics,
            interpretation=interpretation,
        ),
        evidence_refs=_build_trial_evidence_refs(
            records=records,
            interpretation=interpretation,
            data_age_seconds=contract_metadata.data_age_seconds,
        ),
        calculation_steps=_build_trial_calculation_steps(
            statistics=statistics,
            method_refs=contract_metadata.calculation_method_refs,
            trial_info=trial_info,
        ),
        uncertainty=UncertaintyInfo(
            confidence=contract_metadata.confidence_score,
            missing_data=missing_data,
        ),
        policy_flags=_derive_trial_policy_flags(
            trial_info=trial_info,
            interpretation=interpretation,
            contract_metadata=contract_metadata,
        ),
    )


def _build_trial_info(trial: Trial, studies: list[Study], records: list[dict[str, Any]]) -> TrialInfo:
    additional = trial.additional_info or {}
    distinct_locations = {record["location_key"] for record in records if record.get("location_key")}
    distinct_germplasm = {record["germplasm_key"] for record in records if record.get("germplasm_key")}
    distinct_traits = {record["trait_name"] for record in records if record.get("trait_name")}
    observed_pairs = {
        (record["germplasm_key"], record["trait_name"])
        for record in records
        if record.get("germplasm_key") and record.get("trait_name")
    }
    total_pairs = len(distinct_germplasm) * len(distinct_traits)
    completion_rate = additional.get("completionRate")
    if completion_rate is None:
        completion_rate = round((len(observed_pairs) / total_pairs) * 100, 2) if total_pairs else 0.0

    return TrialInfo(
        trialDbId=trial.trial_db_id or str(trial.id),
        trialName=trial.trial_name or "",
        programDbId=str(trial.program_id) if trial.program_id else None,
        programName=trial.program.program_name if trial.program else None,
        startDate=_serialize_date(trial.start_date),
        endDate=_serialize_date(trial.end_date),
        locations=len(distinct_locations) or len(studies) or additional.get("locations", 0),
        entries=len(distinct_germplasm) or additional.get("entries", 0),
        traits=len(distinct_traits) or additional.get("traits", 0),
        observations=len(records) or additional.get("observations", 0),
        completionRate=completion_rate,
        leadScientist=additional.get("leadScientist"),
    )


def _build_trial_interpretation_records(
    records: list[dict[str, Any]],
) -> list[PhenotypeInterpretationRecord]:
    interpretation_records: list[PhenotypeInterpretationRecord] = []
    for record in records:
        germplasm_key = record.get("germplasm_key")
        trait_key = record.get("trait_key")
        if not germplasm_key or not trait_key:
            continue

        role_hint = "baseline_candidate" if "check" in record.get("entry_type", "") or "control" in record.get("entry_type", "") else "candidate"
        interpretation_records.append(
            PhenotypeInterpretationRecord(
                entity_db_id=germplasm_key,
                entity_name=record.get("germplasm_name") or germplasm_key,
                trait_key=trait_key,
                trait_name=record.get("trait_name") or trait_key,
                unit=record.get("trait_unit"),
                value=record["value"],
                observation_ref=record.get("observation_ref"),
                role_hint=role_hint,
            )
        )
    return interpretation_records


def _select_trial_baseline(records: list[dict[str, Any]]) -> tuple[str | None, str | None, str | None]:
    baseline_candidates = sorted(
        {
            (
                record["germplasm_key"],
                record.get("germplasm_name") or record["germplasm_key"],
            )
            for record in records
            if record.get("germplasm_key")
            and (
                "check" in record.get("entry_type", "")
                or "control" in record.get("entry_type", "")
            )
        },
        key=lambda item: (item[1].lower(), item[0]),
    )
    if not baseline_candidates:
        return None, None, None

    entity_id, entity_name = baseline_candidates[0]
    return entity_id, entity_name, "entry_type_check"


def _format_change_percent(delta_percent: float | None) -> str:
    if delta_percent is None:
        return "0%"
    sign = "+" if delta_percent > 0 else ""
    return f"{sign}{delta_percent:.1f}%"


def _build_top_performers_from_interpretation(
    interpretation: PhenotypeInterpretation,
    limit: int,
) -> list[TopPerformer]:
    entity_traits = {
        entity.entity_db_id: [metric.trait_name for metric in entity.metrics]
        for entity in interpretation.entities
    }
    return [
        TopPerformer(
            rank=item.rank,
            germplasmDbId=item.entity_db_id,
            germplasmName=item.entity_name,
            yield_value=round(item.score or 0.0, 4),
            change_percent=_format_change_percent(item.delta_percent_vs_baseline),
            traits=sorted(entity_traits.get(item.entity_db_id, []))[:3],
        )
        for item in interpretation.ranking[:limit]
    ]


def _build_top_performers(
    records: list[dict[str, Any]],
    limit: int,
    requested_trait: str | None = None,
) -> tuple[list[TopPerformer], str | None]:
    trait_groups = _group_records_by_trait(records)
    selected_trait = requested_trait if requested_trait in trait_groups else None
    primary_trait = selected_trait or _select_primary_trait(trait_groups)
    if not primary_trait:
        return [], None

    grouped_values = trait_groups[primary_trait]
    germplasm_traits: dict[str, set[str]] = defaultdict(set)
    germplasm_names: dict[str, str] = {}
    entry_types: dict[str, str] = {}
    for record in records:
        germplasm_key = record.get("germplasm_key")
        if not germplasm_key:
            continue
        germplasm_names[germplasm_key] = record.get("germplasm_name") or germplasm_key
        germplasm_traits[germplasm_key].add(record["trait_name"])
        if record.get("entry_type"):
            entry_types[germplasm_key] = record["entry_type"]

    means = {
        germplasm_key: sum(values) / len(values)
        for germplasm_key, values in grouped_values.items()
        if values
    }
    if not means:
        return [], primary_trait

    check_values = [
        mean_value
        for germplasm_key, mean_value in means.items()
        if "check" in entry_types.get(germplasm_key, "") or "control" in entry_types.get(germplasm_key, "")
    ]
    baseline = (sum(check_values) / len(check_values)) if check_values else (sum(means.values()) / len(means))
    ranked = sorted(means.items(), key=lambda item: item[1], reverse=True)[:limit]

    top_performers: list[TopPerformer] = []
    for index, (germplasm_key, mean_value) in enumerate(ranked, start=1):
        change_percent = "0%"
        if baseline not in (None, 0):
            delta = ((mean_value - baseline) / baseline) * 100
            sign = "+" if delta > 0 else ""
            change_percent = f"{sign}{delta:.1f}%"

        top_performers.append(
            TopPerformer(
                rank=index,
                germplasmDbId=germplasm_key,
                germplasmName=germplasm_names.get(germplasm_key, germplasm_key),
                yield_value=round(mean_value, 4),
                change_percent=change_percent,
                traits=sorted(germplasm_traits.get(germplasm_key, set()))[:3],
            )
        )

    return top_performers, primary_trait


def _build_trait_summary(records: list[dict[str, Any]]) -> list[TraitSummary]:
    trait_groups = _group_records_by_trait(records)
    summary_list: list[TraitSummary] = []
    for trait_name in sorted(trait_groups):
        grouped_values = trait_groups[trait_name]
        values = [value for trait_values in grouped_values.values() for value in trait_values]
        metrics = _anova_metrics(grouped_values)
        summary_list.append(
            TraitSummary(
                trait=trait_name,
                mean=round(_mean(values) or 0.0, 4),
                cv=round(_coefficient_of_variation(values) or 0.0, 4),
                lsd=_round_or_none(metrics["lsd"]),
                fValue=_round_or_none(metrics["f_value"]),
                significance=metrics["significance"],
            )
        )
    return summary_list


def _build_location_performance(records: list[dict[str, Any]]) -> list[LocationPerformance]:
    trait_groups = _group_records_by_trait(records)
    primary_trait = _select_primary_trait(trait_groups)
    trial_trait_count = len(trait_groups)
    location_groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "name": "Unassigned Location",
            "entries": set(),
            "primary_values": [],
            "pairs": set(),
        }
    )

    for record in records:
        location_key = record["location_key"]
        group = location_groups[location_key]
        group["name"] = record["location_name"]
        if record.get("germplasm_key"):
            group["entries"].add(record["germplasm_key"])
            group["pairs"].add((record["germplasm_key"], record["trait_name"]))
        if primary_trait and record["trait_name"] == primary_trait:
            group["primary_values"].append(record["value"])

    results: list[LocationPerformance] = []
    for location_key, group in sorted(location_groups.items(), key=lambda item: item[1]["name"]):
        entry_count = len(group["entries"])
        total_pairs = entry_count * trial_trait_count
        completion_rate = round((len(group["pairs"]) / total_pairs) * 100, 2) if total_pairs else 0.0
        results.append(
            LocationPerformance(
                locationDbId=location_key,
                locationName=group["name"],
                entries=entry_count,
                meanYield=round(_mean(group["primary_values"]) or 0.0, 4),
                cv=round(_coefficient_of_variation(group["primary_values"]) or 0.0, 4),
                completionRate=completion_rate,
            )
        )

    return results


def _build_trial_statistics(records: list[dict[str, Any]]) -> dict[str, Any]:
    trait_groups = _group_records_by_trait(records)
    primary_trait = _select_primary_trait(trait_groups)
    if not primary_trait:
        return {
            "grand_mean": None,
            "overall_cv": None,
            "heritability": None,
            "genetic_variance": None,
            "error_variance": None,
            "lsd_5_percent": None,
            "selection_intensity": None,
            "expected_gain": None,
            "anova": None,
            "message": "Statistics require numeric trial observations.",
        }

    primary_values = [value for values in trait_groups[primary_trait].values() for value in values]
    metrics = _anova_metrics(trait_groups[primary_trait])
    return {
        "primary_trait": primary_trait,
        "grand_mean": _round_or_none(_mean(primary_values)),
        "overall_cv": _round_or_none(_coefficient_of_variation(primary_values)),
        "heritability": _round_or_none(metrics["heritability"]),
        "genetic_variance": _round_or_none(metrics["genetic_variance"]),
        "error_variance": _round_or_none(metrics["error_variance"]),
        "genotype_variance": _round_or_none(metrics["genetic_variance"]),
        "gxe_variance": None,
        "lsd_5_percent": _round_or_none(metrics["lsd"]),
        "lsd_1_percent": None,
        "selection_intensity": _round_or_none(metrics["selection_intensity"]),
        "expected_gain": _round_or_none(metrics["expected_gain"]),
        "realized_gain": None,
        "anova": metrics["anova"],
        "message": f"Statistics are calculated from observed values for the primary trait '{primary_trait}'.",
    }


@router.get("/trials")
async def get_trials(
    program_id: str | None = Query(None, description="Filter by program"),
    status: str | None = Query(None, description="Filter by status: active, completed, planned"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get list of trials with summary info.

    Queries Trial table with related Program and Study data.
    Returns empty list when no trials exist.
    """
    stmt = select(Trial).where(Trial.organization_id == organization_id).options(selectinload(Trial.program))
    if program_id:
        stmt = stmt.where(Trial.program_id == int(program_id))

    result = await db.execute(stmt)
    trials = result.scalars().all()
    data = []
    for trial in trials:
        study_count_result = await db.execute(
            select(func.count()).select_from(Study).where(
                and_(
                    Study.trial_id == trial.id,
                    Study.organization_id == organization_id,
                )
            )
        )
        study_count = study_count_result.scalar() or 0
        additional = trial.additional_info or {}
        data.append(
            TrialInfo(
                trialDbId=trial.trial_db_id or str(trial.id),
                trialName=trial.trial_name or "",
                programDbId=str(trial.program_id) if trial.program_id else None,
                programName=trial.program.program_name if trial.program else None,
                startDate=_serialize_date(trial.start_date),
                endDate=_serialize_date(trial.end_date),
                locations=study_count,
                entries=additional.get("entries", 0),
                traits=additional.get("traits", 0),
                observations=additional.get("observations", 0),
                completionRate=additional.get("completionRate", 0.0),
                leadScientist=additional.get("leadScientist"),
            ).model_dump()
        )

    return {"data": data, "total": len(data)}


@router.get("/trials/{trial_id}")
async def get_trial(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get trial details.

    Returns 404 if trial not found.
    """
    stmt = select(Trial).where(
        and_(
            Trial.organization_id == organization_id,
            Trial.trial_db_id == trial_id,
        )
    ).options(selectinload(Trial.program))
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()

    if not trial and trial_id.isdigit():
        stmt = select(Trial).where(
            and_(
                Trial.organization_id == organization_id,
                Trial.id == int(trial_id),
            )
        ).options(selectinload(Trial.program))
        result = await db.execute(stmt)
        trial = result.scalar_one_or_none()

    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    additional = trial.additional_info or {}
    return {
        "data": TrialInfo(
            trialDbId=trial.trial_db_id or str(trial.id),
            trialName=trial.trial_name or "",
            programDbId=str(trial.program_id) if trial.program_id else None,
            programName=trial.program.program_name if trial.program else None,
            startDate=_serialize_date(trial.start_date),
            endDate=_serialize_date(trial.end_date),
            locations=additional.get("locations", 0),
            entries=additional.get("entries", 0),
            traits=additional.get("traits", 0),
            observations=additional.get("observations", 0),
            completionRate=additional.get("completionRate", 0.0),
            leadScientist=additional.get("leadScientist"),
        ).model_dump()
    }


@router.get("/trials/{trial_id}/summary", response_model=TrialSummaryResponse)
async def get_trial_summary(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get comprehensive trial summary."""
    trial = await _resolve_trial(db, organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    trial = (
        await db.execute(
            select(Trial)
            .where(Trial.id == trial.id, Trial.organization_id == organization_id)
            .options(selectinload(Trial.program))
        )
    ).scalar_one()
    studies = (
        await db.execute(
            select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.trial_id == trial.id,
                )
            )
        )
    ).scalars().all()
    records = await _load_trial_numeric_records(db, organization_id, trial.id)
    baseline_entity_id, baseline_entity_name, baseline_selection = _select_trial_baseline(records)
    interpretation = phenotype_interpretation_service.build_interpretation(
        scope="trial_summary",
        records=_build_trial_interpretation_records(records),
        methodology="database_trial_observation_means_by_germplasm",
        baseline_entity_id=baseline_entity_id,
        baseline_entity_name=baseline_entity_name,
        baseline_selection=baseline_selection,
        evidence_refs=[
            f"db:trial:{trial.trial_db_id or trial.id}",
            *[f"db:study:{study.id}" for study in studies],
        ],
    )
    contract_metadata = _derive_trial_summary_contract_metadata(
        records=records,
        interpretation=interpretation,
    )
    trial_info = TrialInfo.model_validate(_build_trial_info(trial, studies, records))
    top_performers = _build_top_performers_from_interpretation(interpretation, limit=5)
    statistics = _build_trial_statistics(records)
    evidence_envelope = _build_trial_evidence_envelope(
        trial_info=trial_info,
        top_performers=top_performers,
        statistics=statistics,
        records=records,
        interpretation=interpretation,
        contract_metadata=contract_metadata,
    )

    return TrialSummaryResponse(
        trial=trial_info,
        topPerformers=top_performers,
        traitSummary=_build_trait_summary(records),
        locationPerformance=_build_location_performance(records),
        statistics=statistics,
        interpretation=interpretation,
        evidence_refs=interpretation.evidence_refs,
        calculation_ids=interpretation.calculation_ids,
        confidence_score=contract_metadata.confidence_score,
        data_age_seconds=contract_metadata.data_age_seconds,
        calculation_method_refs=contract_metadata.calculation_method_refs,
        evidence_envelope=evidence_envelope,
    )


@router.get("/trials/{trial_id}/top-performers")
async def get_top_performers(
    trial_id: str,
    limit: int = Query(10, ge=1, le=50),
    trait: str | None = Query(None, description="Sort by specific trait"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get top performing entries in a trial."""
    trial = await _resolve_trial(db, organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    records = await _load_trial_numeric_records(db, organization_id, trial.id)
    performers, resolved_trait = _build_top_performers(records, limit=limit, requested_trait=trait)
    return {
        "data": [performer.model_dump() for performer in performers],
        "trait": resolved_trait or trait or "No numeric trait available",
        "message": "Top performers rank by mean observed value for the selected trial trait.",
    }


@router.get("/trials/{trial_id}/traits")
async def get_trait_summary(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get trait summary statistics for a trial."""
    trial = await _resolve_trial(db, organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    records = await _load_trial_numeric_records(db, organization_id, trial.id)
    summary_list = _build_trait_summary(records)
    return {
        "data": [summary.model_dump() for summary in summary_list],
        "message": "Trait statistics are derived from observed trial values. ANOVA-style metrics are returned when group structure supports them.",
    }


@router.get("/trials/{trial_id}/locations")
async def get_location_performance(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get performance by location for a trial."""
    trial = await _resolve_trial(db, organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    records = await _load_trial_numeric_records(db, organization_id, trial.id)
    return {"data": [location.model_dump() for location in _build_location_performance(records)]}


@router.get("/trials/{trial_id}/statistics")
async def get_trial_statistics(
    trial_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get detailed statistical analysis for a trial."""
    trial = await _resolve_trial(db, organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    records = await _load_trial_numeric_records(db, organization_id, trial.id)
    return _build_trial_statistics(records)


@router.post("/trials/{trial_id}/export")
async def export_trial_summary(
    trial_id: str,
    format: str = Query("pdf", description="Export format: pdf, xlsx, docx"),
    sections: str | None = Query(None, description="Comma-separated sections to include"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Export trial summary report.

    Note: Export functionality requires report generation service.
    """
    trial = await _resolve_trial(db, organization_id, trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    return {
        "message": f"Report generation pending - {format.upper()} format",
        "trial_id": trial_id,
        "format": format,
        "sections": sections.split(",") if sections else ["all"],
        "download_url": None,
        "note": "Export functionality requires report generation service",
    }
