"""REEVU phenotype comparison engine."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Literal

from scipy import stats as scipy_stats

from app.modules.ai.services.statistics_calculator_service import ObservationData, TrialStatistics
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef


@dataclass(slots=True)
class GroupStats:
    germplasm_id: str
    germplasm_name: str
    n: int
    mean: float | None
    std_dev: float | None


@dataclass(slots=True)
class ComparisonEngineResult:
    trait_name: str | None
    test_type: Literal["t_test", "anova"] | None
    groups: list[GroupStats] = field(default_factory=list)
    f_value: float | None = None
    p_value: float | None = None
    significant: bool | None = None
    lsd: float | None = None
    insufficient_data: bool = False
    reason: str | None = None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    calculation_steps: list[CalculationStep] = field(default_factory=list)


@dataclass(slots=True)
class GermplasmProfile:
    germplasm_id: str
    germplasm_name: str
    raw_values: dict[str, float] = field(default_factory=dict)
    normalized_values: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class TraitProfileResult:
    traits: list[str] = field(default_factory=list)
    profiles: list[GermplasmProfile] = field(default_factory=list)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    calculation_steps: list[CalculationStep] = field(default_factory=list)


@dataclass(slots=True)
class MultiEnvComparisonResult:
    trait_name: str
    environments: list[str] = field(default_factory=list)
    per_env_means: dict[str, dict[str, float]] = field(default_factory=dict)
    overall_means: dict[str, float] = field(default_factory=dict)
    stability_flags: dict[str, str] = field(default_factory=dict)
    gxe_detected: bool = False
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    calculation_steps: list[CalculationStep] = field(default_factory=list)


class PhenotypeComparisonEngine:
    """Computes statistical comparisons for REEVU germplasm phenotype queries."""

    MIN_OBSERVATIONS_PER_GROUP = 3

    def compare(
        self,
        germplasm_ids: list[str],
        observations_by_germplasm: dict[str, list[dict[str, Any]]],
        trait_name: str | None = None,
    ) -> ComparisonEngineResult:
        """Compare germplasm groups with a t-test-equivalent ANOVA or multi-group ANOVA."""
        selected_trait = trait_name or _select_primary_trait(observations_by_germplasm)
        filtered = {
            germplasm_id: [
                {**observation, "germplasm_id": germplasm_id}
                for observation in _filter_observations(observations, selected_trait)
            ]
            for germplasm_id, observations in observations_by_germplasm.items()
        }
        group_stats = [
            _build_group_stats(germplasm_id, filtered.get(germplasm_id, []))
            for germplasm_id in germplasm_ids
        ]
        underpowered = [
            group.germplasm_id
            for group in group_stats
            if group.n < self.MIN_OBSERVATIONS_PER_GROUP
        ]
        if underpowered or len(group_stats) < 2:
            return ComparisonEngineResult(
                trait_name=selected_trait,
                test_type=None,
                groups=group_stats,
                insufficient_data=True,
                reason=(
                    "Each germplasm group needs at least three numeric observations "
                    "for phenotype comparison."
                ),
                evidence_refs=_evidence_refs("comparison_insufficient_data"),
                calculation_steps=_calculation_steps(
                    "comparison_insufficient_data",
                    "group_n < min_observations_per_group",
                    {
                        "underpowered_groups": underpowered,
                        "min_observations_per_group": self.MIN_OBSERVATIONS_PER_GROUP,
                    },
                ),
            )

        comparison_observations = [
            observation
            for germplasm_id in germplasm_ids
            for observation in filtered.get(germplasm_id, [])
        ]
        trial_statistics = _trial_statistics(comparison_observations)
        anova = trial_statistics.calculate_anova()
        f_value = _float_or_none(anova.get("f_value"))
        p_value = _anova_p_value(f_value, anova.get("df_genotype"), anova.get("df_error"))
        lsd = trial_statistics.calculate_lsd(anova.get("ms_error"))
        test_type: Literal["t_test", "anova"] = "t_test" if len(germplasm_ids) == 2 else "anova"

        return ComparisonEngineResult(
            trait_name=selected_trait,
            test_type=test_type,
            groups=group_stats,
            f_value=f_value,
            p_value=p_value,
            significant=(p_value < 0.05) if p_value is not None else None,
            lsd=lsd,
            insufficient_data=False,
            reason=None,
            evidence_refs=_evidence_refs("compare"),
            calculation_steps=_calculation_steps(
                "compare",
                "one-way ANOVA over germplasm phenotype groups",
                {
                    "trait_name": selected_trait,
                    "germplasm_ids": germplasm_ids,
                    "df_genotype": anova.get("df_genotype"),
                    "df_error": anova.get("df_error"),
                },
            ),
        )

    def build_trait_profile(
        self,
        germplasm_ids: list[str],
        observations_by_germplasm: dict[str, list[dict[str, Any]]],
    ) -> TraitProfileResult:
        """Build normalized multi-trait profiles for radar chart-style comparison."""
        raw_by_germplasm: dict[str, dict[str, float]] = {}
        trait_names: set[str] = set()
        for germplasm_id in germplasm_ids:
            grouped_values: dict[str, list[float]] = defaultdict(list)
            for observation in observations_by_germplasm.get(germplasm_id, []):
                value = _numeric_value(observation)
                trait_name = _trait_name(observation)
                if value is None or trait_name is None:
                    continue
                grouped_values[trait_name].append(value)
            raw_by_germplasm[germplasm_id] = {
                trait: statistics.mean(values)
                for trait, values in grouped_values.items()
                if values
            }
            trait_names.update(raw_by_germplasm[germplasm_id])

        traits = sorted(trait_names)
        ranges: dict[str, tuple[float, float]] = {}
        for trait in traits:
            values = [
                raw_values[trait]
                for raw_values in raw_by_germplasm.values()
                if trait in raw_values
            ]
            ranges[trait] = (min(values), max(values))

        profiles = []
        for germplasm_id in germplasm_ids:
            raw_values = raw_by_germplasm.get(germplasm_id, {})
            normalized_values = {
                trait: _normalize(raw_values[trait], *ranges[trait])
                for trait in traits
                if trait in raw_values
            }
            profiles.append(
                GermplasmProfile(
                    germplasm_id=germplasm_id,
                    germplasm_name=_germplasm_name(
                        germplasm_id,
                        observations_by_germplasm.get(germplasm_id, []),
                    ),
                    raw_values=raw_values,
                    normalized_values=normalized_values,
                )
            )

        return TraitProfileResult(
            traits=traits,
            profiles=profiles,
            evidence_refs=_evidence_refs("trait_profile"),
            calculation_steps=_calculation_steps(
                "trait_profile",
                "normalized = (mean - trait_min) / (trait_max - trait_min)",
                {"traits": traits, "germplasm_ids": germplasm_ids},
            ),
        )

    def compare_multi_environment(
        self,
        germplasm_ids: list[str],
        observations_by_germplasm_and_env: dict[str, dict[str, list[dict[str, Any]]]],
        trait_name: str,
    ) -> MultiEnvComparisonResult:
        """Compare germplasm across environments and flag instability/GxE."""
        environments = sorted({
            environment
            for by_environment in observations_by_germplasm_and_env.values()
            for environment in by_environment
        })
        per_env_means: dict[str, dict[str, float]] = {environment: {} for environment in environments}
        per_germplasm_env_means: dict[str, list[float]] = defaultdict(list)

        for germplasm_id in germplasm_ids:
            for environment in environments:
                values = [
                    value
                    for observation in observations_by_germplasm_and_env
                    .get(germplasm_id, {})
                    .get(environment, [])
                    for value in [_numeric_value(observation)]
                    if value is not None and _trait_name(observation) == trait_name
                ]
                if not values:
                    continue
                mean = statistics.mean(values)
                per_env_means[environment][germplasm_id] = mean
                per_germplasm_env_means[germplasm_id].append(mean)

        overall_means = {
            germplasm_id: statistics.mean(values)
            for germplasm_id, values in per_germplasm_env_means.items()
            if values
        }
        stability_flags = {
            germplasm_id: _stability_flag(values)
            for germplasm_id, values in per_germplasm_env_means.items()
        }
        rankings = [
            [
                germplasm_id
                for germplasm_id, _mean in sorted(
                    env_means.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ]
            for env_means in per_env_means.values()
            if env_means
        ]
        gxe_detected = any(ranking != rankings[0] for ranking in rankings[1:]) if rankings else False

        return MultiEnvComparisonResult(
            trait_name=trait_name,
            environments=environments,
            per_env_means=per_env_means,
            overall_means=overall_means,
            stability_flags=stability_flags,
            gxe_detected=gxe_detected,
            evidence_refs=_evidence_refs("multi_environment"),
            calculation_steps=_calculation_steps(
                "multi_environment",
                "environment means, overall means, CV stability, and rank-order change",
                {"trait_name": trait_name, "environments": environments},
            ),
        )


def _filter_observations(
    observations: list[dict[str, Any]],
    trait_name: str | None,
) -> list[dict[str, Any]]:
    result = []
    for observation in observations:
        value = _numeric_value(observation)
        if value is None:
            continue
        observed_trait = _trait_name(observation)
        if trait_name and observed_trait != trait_name:
            continue
        result.append({**observation, "value": value, "trait_name": observed_trait})
    return result


def _select_primary_trait(observations_by_germplasm: dict[str, list[dict[str, Any]]]) -> str | None:
    counts: dict[str, int] = defaultdict(int)
    for observations in observations_by_germplasm.values():
        for observation in observations:
            if _numeric_value(observation) is None:
                continue
            trait_name = _trait_name(observation)
            if trait_name:
                counts[trait_name] += 1
    if not counts:
        return None
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _build_group_stats(germplasm_id: str, observations: list[dict[str, Any]]) -> GroupStats:
    if not observations:
        return GroupStats(
            germplasm_id=germplasm_id,
            germplasm_name=germplasm_id,
            n=0,
            mean=None,
            std_dev=None,
        )
    stats = _trial_statistics(observations).calculate_basic_stats()
    count = int(stats["count"])
    return GroupStats(
        germplasm_id=germplasm_id,
        germplasm_name=_germplasm_name(germplasm_id, observations),
        n=count,
        mean=float(stats["mean"]) if stats["mean"] is not None else None,
        std_dev=float(stats["std_dev"]) if count >= 2 and stats["std_dev"] is not None else None,
    )


def _trial_statistics(observations: list[dict[str, Any]]) -> TrialStatistics:
    return TrialStatistics(
        [
            ObservationData(
                value=float(observation["value"]),
                germplasm_id=str(observation.get("germplasm_id") or "unknown"),
            )
            for observation in observations
        ]
    )


def _numeric_value(observation: dict[str, Any]) -> float | None:
    value = None
    for key in ("value", "observation_value", "observationValue", "value_numeric", "valueNumeric"):
        if observation.get(key) is not None:
            value = observation[key]
            break
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _trait_name(observation: dict[str, Any]) -> str | None:
    for key in ("trait_name", "traitName", "variable_name", "observationVariableName"):
        if observation.get(key):
            return str(observation[key]).strip()
    trait = observation.get("trait")
    if isinstance(trait, dict):
        for key in ("name", "trait_name", "traitName"):
            if trait.get(key):
                return str(trait[key]).strip()
    observation_variable = observation.get("observation_variable") or observation.get(
        "observationVariable"
    )
    if isinstance(observation_variable, dict) and observation_variable.get("name"):
        return str(observation_variable["name"]).strip()
    return None


def _germplasm_name(germplasm_id: str, observations: list[dict[str, Any]]) -> str:
    for observation in observations:
        if observation.get("germplasm_name"):
            return str(observation["germplasm_name"])
        germplasm = observation.get("germplasm")
        if isinstance(germplasm, dict) and germplasm.get("name"):
            return str(germplasm["name"])
    return germplasm_id


def _normalize(value: float, min_value: float, max_value: float) -> float:
    if max_value == min_value:
        return 0.5
    return (value - min_value) / (max_value - min_value)


def _stability_flag(values: list[float]) -> str:
    if len(values) < 2:
        return "stable"
    mean = statistics.mean(values)
    std_dev = statistics.stdev(values)
    cv = math.inf if mean == 0 and std_dev > 0 else (std_dev / mean * 100 if mean else 0.0)
    return "unstable" if abs(cv) > 20 else "stable"


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _anova_p_value(f_value: float | None, df_genotype: Any, df_error: Any) -> float | None:
    if f_value is None:
        return None
    try:
        df_num = int(df_genotype)
        df_den = int(df_error)
    except (TypeError, ValueError):
        return None
    if df_num <= 0 or df_den <= 0:
        return None
    return float(scipy_stats.f.sf(f_value, df_num, df_den))


def _evidence_refs(method: str) -> list[EvidenceRef]:
    return [
        EvidenceRef(
            source_type="function",
            entity_id=f"phenotype_comparison:{method}",
            query_or_method=f"phenotype_comparison_engine.{method}",
        )
    ]


def _calculation_steps(
    step: str,
    formula: str,
    inputs: dict[str, Any],
) -> list[CalculationStep]:
    return [
        CalculationStep(
            step_id=f"phenotype_comparison:{step}",
            formula=formula,
            inputs=inputs,
        )
    ]
