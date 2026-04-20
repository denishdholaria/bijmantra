"""Deterministic interpretation builder for phenotype comparison and trial summary."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from app.schemas.phenotype_interpretation import (
    PhenotypeInterpretation,
    PhenotypeInterpretationBaseline,
    PhenotypeInterpretationEntity,
    PhenotypeInterpretationEntityMetric,
    PhenotypeInterpretationRankingItem,
    PhenotypeInterpretationSummary,
    PhenotypeInterpretationTrait,
)


@dataclass(frozen=True)
class PhenotypeInterpretationRecord:
    entity_db_id: str
    entity_name: str
    trait_key: str
    trait_name: str
    unit: str | None
    value: float
    observation_ref: str | None = None
    role_hint: str | None = None


def normalize_trait_key(name: str | None) -> str:
    normalized = (name or "").strip().lower().replace("-", "_").replace(" ", "_")
    normalized = normalized.replace("grain_", "")
    normalized = normalized.replace("plant_", "")
    normalized = normalized.replace("days_to_", "")
    normalized = normalized.replace("_content", "")
    normalized = normalized.replace("_resistance", "")
    return normalized


def safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_or_none(value: float | None, digits: int = 4) -> float | None:
    return round(value, digits) if value is not None else None


def _sample_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
    return sqrt(variance)


def _select_primary_trait_key(
    trait_subject_means: dict[str, list[float]],
    trait_names: dict[str, str],
) -> str | None:
    if not trait_subject_means:
        return None

    def priority(trait_key: str) -> tuple[int, int, int, str]:
        normalized = normalize_trait_key(trait_key)
        display_name = normalize_trait_key(trait_names.get(trait_key))
        exact_yield = int(normalized in {"yield", "grain_yield", "seed_yield", "plot_yield"})
        any_yield = int("yield" in normalized or "yield" in display_name)
        subject_count = len(trait_subject_means[trait_key])
        return (exact_yield, any_yield, subject_count, trait_key)

    return max(trait_subject_means.keys(), key=priority)


class PhenotypeInterpretationService:
    """Build one shared interpretation surface from numeric phenotyping records."""

    def build_interpretation(
        self,
        *,
        scope: str,
        records: list[PhenotypeInterpretationRecord],
        methodology: str,
        entity_order: list[str] | None = None,
        baseline_entity_id: str | None = None,
        baseline_entity_name: str | None = None,
        baseline_selection: str | None = None,
        primary_trait_key: str | None = None,
        evidence_refs: list[str] | None = None,
        calculation_ids: list[str] | None = None,
    ) -> PhenotypeInterpretation:
        sorted_records = sorted(
            records,
            key=lambda record: (
                record.entity_db_id,
                record.trait_key,
                record.observation_ref or "",
                record.value,
            ),
        )
        warnings: list[str] = []

        entity_names: dict[str, str] = {}
        entity_roles: dict[str, str] = {}
        trait_names: dict[str, str] = {}
        trait_units: dict[str, str | None] = {}
        value_groups: dict[str, dict[str, list[float]]] = {}
        ref_groups: dict[str, dict[str, list[str]]] = {}

        for record in sorted_records:
            entity_names.setdefault(record.entity_db_id, record.entity_name)
            entity_roles.setdefault(record.entity_db_id, record.role_hint or "candidate")
            trait_names.setdefault(record.trait_key, record.trait_name or record.trait_key)
            trait_units.setdefault(record.trait_key, record.unit)
            value_groups.setdefault(record.entity_db_id, {}).setdefault(record.trait_key, []).append(record.value)
            if record.observation_ref:
                ref_groups.setdefault(record.entity_db_id, {}).setdefault(record.trait_key, []).append(record.observation_ref)

        ordered_entity_ids: list[str] = []
        seen_entity_ids: set[str] = set()
        for entity_id in entity_order or []:
            if entity_id in value_groups and entity_id not in seen_entity_ids:
                ordered_entity_ids.append(entity_id)
                seen_entity_ids.add(entity_id)
        for entity_id in sorted(value_groups):
            if entity_id not in seen_entity_ids:
                ordered_entity_ids.append(entity_id)
                seen_entity_ids.add(entity_id)

        entity_means: dict[str, dict[str, float]] = {}
        entities: list[PhenotypeInterpretationEntity] = []
        for entity_id in ordered_entity_ids:
            metric_models: list[PhenotypeInterpretationEntityMetric] = []
            entity_trait_values = value_groups.get(entity_id, {})
            baseline_trait_values = value_groups.get(baseline_entity_id or "", {})
            entity_means[entity_id] = {}
            for trait_key in sorted(entity_trait_values):
                values = entity_trait_values[trait_key]
                mean_value = round(sum(values) / len(values), 4)
                entity_means[entity_id][trait_key] = mean_value
                delta_percent = None
                baseline_values = baseline_trait_values.get(trait_key)
                if baseline_entity_id and entity_id != baseline_entity_id and baseline_values:
                    baseline_mean = sum(baseline_values) / len(baseline_values)
                    if baseline_mean != 0:
                        delta_percent = round(((mean_value - baseline_mean) / baseline_mean) * 100, 1)
                metric_models.append(
                    PhenotypeInterpretationEntityMetric(
                        trait_key=trait_key,
                        trait_name=trait_names.get(trait_key, trait_key),
                        unit=trait_units.get(trait_key),
                        mean=mean_value,
                        observation_count=len(values),
                        delta_percent_vs_baseline=delta_percent,
                    )
                )

            role = entity_roles.get(entity_id, "candidate")
            if baseline_entity_id and entity_id == baseline_entity_id:
                role = "baseline"

            entities.append(
                PhenotypeInterpretationEntity(
                    entity_db_id=entity_id,
                    entity_name=entity_names.get(entity_id, entity_id),
                    role=role,
                    metric_count=len(metric_models),
                    metrics=metric_models,
                )
            )

        trait_models: list[PhenotypeInterpretationTrait] = []
        trait_subject_means: dict[str, list[float]] = {}
        for trait_key in sorted(trait_names):
            subject_means = [
                entity_means[entity_id][trait_key]
                for entity_id in ordered_entity_ids
                if trait_key in entity_means.get(entity_id, {})
            ]
            if not subject_means:
                continue

            trait_subject_means[trait_key] = subject_means
            mean_value = sum(subject_means) / len(subject_means)
            std_value = _sample_std(subject_means)
            observation_count = sum(len(value_groups[entity_id][trait_key]) for entity_id in ordered_entity_ids if trait_key in value_groups.get(entity_id, {}))
            cv_value = (std_value / mean_value * 100) if mean_value != 0 else None
            trait_models.append(
                PhenotypeInterpretationTrait(
                    trait_key=trait_key,
                    trait_name=trait_names.get(trait_key, trait_key),
                    unit=trait_units.get(trait_key),
                    subject_count=len(subject_means),
                    observation_count=observation_count,
                    min=round(min(subject_means), 4),
                    max=round(max(subject_means), 4),
                    mean=round(mean_value, 4),
                    std=round(std_value, 4),
                    cv=_round_or_none(cv_value),
                )
            )

        selected_primary_trait = primary_trait_key if primary_trait_key in trait_subject_means else None
        selected_primary_trait = selected_primary_trait or _select_primary_trait_key(trait_subject_means, trait_names)

        if not sorted_records:
            warnings.append("No numeric observations available for interpretation.")
        elif not selected_primary_trait:
            warnings.append("No primary trait could be inferred from the available records.")

        ranking: list[PhenotypeInterpretationRankingItem] = []
        if selected_primary_trait:
            ranked_entities = []
            for entity in entities:
                metric = next(
                    (metric for metric in entity.metrics if metric.trait_key == selected_primary_trait),
                    None,
                )
                if metric is None:
                    continue
                ranked_entities.append((entity, metric))

            ranked_entities.sort(
                key=lambda item: (
                    -(item[1].mean or 0.0),
                    item[0].entity_name.lower(),
                    item[0].entity_db_id,
                )
            )
            for rank, (entity, metric) in enumerate(ranked_entities, start=1):
                trait_refs = sorted(set(ref_groups.get(entity.entity_db_id, {}).get(metric.trait_key, [])))
                rationale = f"{metric.trait_name} mean {metric.mean:.4f} from {metric.observation_count} observations"
                if metric.delta_percent_vs_baseline is not None and baseline_entity_id and baseline_entity_id != entity.entity_db_id:
                    rationale = f"{rationale}; {metric.delta_percent_vs_baseline:+.1f}% vs baseline"
                ranking.append(
                    PhenotypeInterpretationRankingItem(
                        rank=rank,
                        entity_db_id=entity.entity_db_id,
                        entity_name=entity.entity_name,
                        role=entity.role,
                        score_trait_key=metric.trait_key,
                        score_trait_name=metric.trait_name,
                        score=metric.mean,
                        delta_percent_vs_baseline=metric.delta_percent_vs_baseline,
                        rationale=rationale,
                        evidence_refs=trait_refs,
                    )
                )

        baseline = None
        if baseline_entity_id and baseline_entity_id in entity_names:
            baseline = PhenotypeInterpretationBaseline(
                entity_db_id=baseline_entity_id,
                entity_name=baseline_entity_name or entity_names.get(baseline_entity_id, baseline_entity_id),
                selection_method=baseline_selection or "explicit",
            )
            if selected_primary_trait and selected_primary_trait not in entity_means.get(baseline_entity_id, {}):
                warnings.append("Baseline entity has no observations for the primary trait.")

        default_evidence_refs = sorted(
            {
                *(evidence_refs or []),
                *(f"db:entity:{entity_id}" for entity_id in ordered_entity_ids),
                *(f"db:trait:{trait_key}" for trait_key in sorted(trait_subject_means)),
            }
        )
        default_calculation_ids = sorted(
            {
                *(calculation_ids or []),
                f"fn:build_phenotype_interpretation:{scope}",
                "calc:entity_trait_mean",
            }
        )
        if baseline is not None:
            default_calculation_ids.append("calc:delta_percent_vs_baseline")
            default_calculation_ids = sorted(set(default_calculation_ids))

        return PhenotypeInterpretation(
            scope=scope,
            methodology=methodology,
            primary_trait_key=selected_primary_trait,
            primary_trait_name=trait_names.get(selected_primary_trait) if selected_primary_trait else None,
            summary=PhenotypeInterpretationSummary(
                entity_count=len(entities),
                trait_count=len(trait_models),
                observation_count=len(sorted_records),
            ),
            baseline=baseline,
            entities=entities,
            traits=trait_models,
            ranking=ranking,
            evidence_refs=default_evidence_refs,
            calculation_ids=default_calculation_ids,
            warnings=warnings,
        )


phenotype_interpretation_service = PhenotypeInterpretationService()