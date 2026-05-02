"""
REEVU analytics engine.

Normalizes accumulated step observations and provides the computation
surface for descriptive statistics, ranking, comparison, and trial summary.
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, TYPE_CHECKING

from scipy import stats as scipy_stats

from app.modules.ai.services.statistics_calculator_service import ObservationData, TrialStatistics
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef, UncertaintyInfo

if TYPE_CHECKING:
    from app.modules.ai.services.reevu.step_executor import IntermediateResultContext


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SafeFailure:
    """Structured safe failure when analytics input data is insufficient."""

    reason: str
    explanation: str
    data_available: dict[str, int] = field(default_factory=dict)
    data_needed: dict[str, int] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GermplasmTraitStats:
    """Descriptive statistics for one germplasm entry on one trait."""

    germplasm_id: str
    germplasm_name: str
    n: int
    mean: float
    std_dev: float | None
    cv: float | None
    min_val: float
    max_val: float
    insufficient_data: bool = False


@dataclass(slots=True)
class TraitStats:
    """Descriptive statistics for one trait across germplasm entries."""

    trait_name: str
    n_observations: int
    n_germplasm: int
    overall_mean: float
    overall_std_dev: float | None
    overall_cv: float | None
    overall_min: float
    overall_max: float
    per_germplasm: list[GermplasmTraitStats] = field(default_factory=list)


@dataclass(slots=True)
class RankedEntry:
    """A single germplasm entry in a ranked list."""

    rank: int
    germplasm_id: str
    germplasm_name: str
    trait_name: str
    mean: float
    n: int
    cv: float | None
    insufficient_data: bool = False
    flag: str | None = None


@dataclass(slots=True)
class GroupStats:
    """Statistics for one group in a comparison."""

    germplasm_id: str
    germplasm_name: str
    n: int
    mean: float
    std_dev: float | None


@dataclass(slots=True)
class ComparisonResult:
    """Result of comparing two or more germplasm groups."""

    trait_name: str
    test_type: Literal["t_test", "anova"]
    groups: list[GroupStats] = field(default_factory=list)
    f_value: float | None = None
    p_value: float | None = None
    significant: bool | None = None
    lsd: float | None = None
    insufficient_data: bool = False
    reason: str | None = None


@dataclass(slots=True)
class TraitSummary:
    """Summary for one trait within a trial."""

    trait_name: str
    n_observations: int
    mean: float
    std_dev: float | None
    cv: float | None
    min_val: float
    max_val: float


@dataclass(slots=True)
class TrialSummary:
    """Summary statistics for a trial."""

    trial_name: str | None
    n_entries: int
    n_observations: int
    traits: list[TraitSummary] = field(default_factory=list)
    top_performers: list[RankedEntry] = field(default_factory=list)


@dataclass(slots=True)
class AnalyticsResult:
    """Result of a single analytics computation."""

    status: Literal["success", "insufficient_data", "error"]
    data: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    calculation_steps: list[CalculationStep] = field(default_factory=list)
    uncertainty: UncertaintyInfo = field(default_factory=UncertaintyInfo)
    warnings: list[str] = field(default_factory=list)


class AnalyticsEngine:
    """Computes statistics from accumulated REEVU step observations."""

    MIN_OBSERVATIONS_FOR_STATS: int = 3
    MIN_OBSERVATIONS_FOR_COMPARISON: int = 3
    MIN_GROUPS_FOR_ANOVA: int = 3

    def compute_descriptive_stats(
        self,
        observations: list[dict[str, Any]],
        trait_filter: str | None = None,
    ) -> AnalyticsResult:
        """Compute per-trait, per-germplasm descriptive statistics."""
        filtered_observations = _filter_observations_by_trait(observations, trait_filter)
        if len(filtered_observations) < self.MIN_OBSERVATIONS_FOR_STATS:
            return self._safe_failure_result(
                reason="insufficient_observations",
                explanation=(
                    "At least three numeric observations are needed to compute "
                    "descriptive statistics."
                ),
                data_available={
                    "observations": len(filtered_observations),
                    "germplasm": len(_distinct_values(filtered_observations, "germplasm_id")),
                },
                data_needed={"min_observations": self.MIN_OBSERVATIONS_FOR_STATS},
                suggestions=[
                    "Record more phenotypic observations for the selected trait or trial.",
                    "Broaden the query to include more germplasm or study observations.",
                ],
            )

        observations_by_trait: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for observation in filtered_observations:
            observations_by_trait[str(observation.get("trait_name") or "unknown_trait")].append(
                observation
            )

        trait_stats: list[TraitStats] = []
        warnings: list[str] = []
        for trait_name, trait_observations in sorted(observations_by_trait.items()):
            per_germplasm = self._compute_germplasm_trait_stats(
                trait_name=trait_name,
                observations=trait_observations,
                warnings=warnings,
            )
            if not per_germplasm:
                continue

            overall = _calculate_basic_stats(trait_observations)
            trait_stats.append(
                TraitStats(
                    trait_name=trait_name,
                    n_observations=int(overall["count"]),
                    n_germplasm=len(per_germplasm),
                    overall_mean=float(overall["mean"]),
                    overall_std_dev=_std_dev_for_count(overall, int(overall["count"])),
                    overall_cv=_cv_for_stats(overall, int(overall["count"])),
                    overall_min=float(overall["min"]),
                    overall_max=float(overall["max"]),
                    per_germplasm=per_germplasm,
                )
            )

        if not any(
            germplasm_stats.insufficient_data is False
            for stats in trait_stats
            for germplasm_stats in stats.per_germplasm
        ):
            return self._safe_failure_result(
                reason="insufficient_sample_size",
                explanation=(
                    "Observations were found, but no germplasm entry has enough "
                    "replicated observations for reliable descriptive statistics."
                ),
                data_available={
                    "observations": len(filtered_observations),
                    "germplasm": len(_distinct_values(filtered_observations, "germplasm_id")),
                },
                data_needed={
                    "min_observations_per_entry": self.MIN_OBSERVATIONS_FOR_STATS,
                },
                suggestions=[
                    "Add replicate observations for each germplasm entry.",
                    "Use the flagged low-sample entries only as provisional signals.",
                ],
            )

        return AnalyticsResult(
            status="success",
            data={
                "traits": [asdict(stats) for stats in trait_stats],
                "trait_filter": trait_filter,
                "n_observations": len(filtered_observations),
            },
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id="analytics:descriptive_stats",
                    query_or_method="analytics_engine.compute_descriptive_stats",
                )
            ],
            calculation_steps=[
                CalculationStep(
                    step_id="analytics:descriptive_stats",
                    formula="mean, sample standard deviation, coefficient of variation, min, max",
                    inputs={
                        "n_observations": len(filtered_observations),
                        "trait_filter": trait_filter,
                    },
                )
            ],
            uncertainty=UncertaintyInfo(
                confidence=0.75 if warnings else 0.85,
                missing_data=warnings,
            ),
            warnings=warnings,
        )

    def compute_ranking(
        self,
        observations: list[dict[str, Any]],
        trait_name: str,
        direction: Literal["desc", "asc"] = "desc",
    ) -> AnalyticsResult:
        """Rank germplasm entries by trait mean."""
        trait_observations = _filter_observations_by_trait(observations, trait_name)
        if not trait_observations:
            return self._safe_failure_result(
                reason="no_trait_observations",
                explanation=f"No numeric observations were found for trait '{trait_name}'.",
                data_available={
                    "observations": 0,
                    "germplasm": 0,
                },
                data_needed={"min_observations": 1},
                suggestions=[
                    "Check the trait name used in the query.",
                    "Add phenotypic observations for the requested trait.",
                ],
            )

        grouped = _group_by_germplasm(trait_observations)
        warnings: list[str] = []
        entries: list[RankedEntry] = []
        for germplasm_id, germplasm_observations in grouped.items():
            stats = _calculate_basic_stats(germplasm_observations)
            count = int(stats["count"])
            insufficient_data = count < self.MIN_OBSERVATIONS_FOR_STATS
            flag = "low_sample_size" if insufficient_data else None
            if insufficient_data:
                warnings.append(
                    f"{germplasm_id} has only {count} observations for {trait_name}"
                )
            first = germplasm_observations[0]
            entries.append(
                RankedEntry(
                    rank=0,
                    germplasm_id=germplasm_id,
                    germplasm_name=str(first.get("germplasm_name") or germplasm_id),
                    trait_name=trait_name,
                    mean=float(stats["mean"]),
                    n=count,
                    cv=_cv_for_stats(stats, count),
                    insufficient_data=insufficient_data,
                    flag=flag,
                )
            )

        reverse = direction != "asc"
        entries.sort(key=lambda entry: entry.mean, reverse=reverse)
        for index, entry in enumerate(entries, start=1):
            entry.rank = index

        return AnalyticsResult(
            status="success",
            data={
                "trait_name": trait_name,
                "direction": direction,
                "entries": [asdict(entry) for entry in entries],
                "n_observations": len(trait_observations),
            },
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id="analytics:ranking",
                    query_or_method="analytics_engine.compute_ranking",
                )
            ],
            calculation_steps=[
                CalculationStep(
                    step_id="analytics:ranking",
                    formula="rank germplasm by trait mean",
                    inputs={
                        "trait_name": trait_name,
                        "direction": direction,
                        "n_observations": len(trait_observations),
                    },
                )
            ],
            uncertainty=UncertaintyInfo(
                confidence=0.72 if warnings else 0.85,
                missing_data=warnings,
            ),
            warnings=warnings,
        )

    def compute_comparison(
        self,
        observations: list[dict[str, Any]],
        trait_name: str,
        group_ids: list[str] | None = None,
    ) -> AnalyticsResult:
        """Compare groups with t-test for two groups or ANOVA for more groups."""
        trait_observations = _filter_observations_by_trait(observations, trait_name)
        if group_ids is not None:
            requested_group_ids = {str(group_id) for group_id in group_ids}
            trait_observations = [
                observation
                for observation in trait_observations
                if str(observation.get("germplasm_id") or "unknown") in requested_group_ids
            ]

        grouped = _group_by_germplasm(trait_observations)
        group_stats = [
            _build_group_stats(germplasm_id, germplasm_observations)
            for germplasm_id, germplasm_observations in grouped.items()
        ]
        qualifying_group_ids = {
            group.germplasm_id
            for group in group_stats
            if group.n >= self.MIN_OBSERVATIONS_FOR_COMPARISON
        }
        if len(qualifying_group_ids) < 2:
            return self._safe_failure_result(
                reason="insufficient_comparison_groups",
                explanation=(
                    "At least two germplasm groups need three or more observations "
                    "for comparison."
                ),
                data_available={
                    "observations": len(trait_observations),
                    "groups": len(grouped),
                    "qualifying_groups": len(qualifying_group_ids),
                },
                data_needed={
                    "min_groups": 2,
                    "min_observations_per_group": self.MIN_OBSERVATIONS_FOR_COMPARISON,
                },
                suggestions=[
                    "Add replicate observations for the groups being compared.",
                    "Broaden the comparison to include groups with enough observations.",
                ],
            )

        qualifying_observations = [
            observation
            for observation in trait_observations
            if str(observation.get("germplasm_id") or "unknown") in qualifying_group_ids
        ]
        trial_statistics = _trial_statistics_for_observations(qualifying_observations)
        anova = trial_statistics.calculate_anova()
        f_value = _float_or_none(anova.get("f_value"))
        df_genotype = anova.get("df_genotype")
        df_error = anova.get("df_error")
        p_value = _anova_p_value(f_value, df_genotype, df_error)
        lsd = trial_statistics.calculate_lsd(anova.get("ms_error"))

        test_type: Literal["t_test", "anova"] = (
            "t_test" if len(qualifying_group_ids) == 2 else "anova"
        )
        warnings = [
            f"{group.germplasm_id} excluded from comparison because n={group.n}"
            for group in group_stats
            if group.germplasm_id not in qualifying_group_ids
        ]
        comparison = ComparisonResult(
            trait_name=trait_name,
            test_type=test_type,
            groups=group_stats,
            f_value=f_value,
            p_value=p_value,
            significant=(p_value < 0.05) if p_value is not None else None,
            lsd=lsd,
            insufficient_data=False,
            reason=None,
        )

        return AnalyticsResult(
            status="success",
            data={
                "comparison": asdict(comparison),
                "included_group_ids": sorted(qualifying_group_ids),
                "group_ids": group_ids,
                "n_observations": len(qualifying_observations),
            },
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id="analytics:comparison",
                    query_or_method="analytics_engine.compute_comparison",
                )
            ],
            calculation_steps=[
                CalculationStep(
                    step_id="analytics:comparison",
                    formula="one-way ANOVA on germplasm groups",
                    inputs={
                        "trait_name": trait_name,
                        "group_ids": group_ids,
                        "df_genotype": df_genotype,
                        "df_error": df_error,
                    },
                )
            ],
            uncertainty=UncertaintyInfo(
                confidence=0.7 if warnings else 0.82,
                missing_data=warnings,
            ),
            warnings=warnings,
        )

    def compute_trial_summary(
        self,
        observations: list[dict[str, Any]],
        trial_name: str | None = None,
    ) -> AnalyticsResult:
        """Compute per-trait summary statistics for a trial."""
        if not observations:
            return self._safe_failure_result(
                reason="no_observations",
                explanation="No numeric observations were available for trial summary.",
                data_available={"observations": 0, "germplasm": 0, "traits": 0},
                data_needed={"min_observations_per_trait": self.MIN_OBSERVATIONS_FOR_STATS},
                suggestions=[
                    "Add trial phenotyping observations before requesting a summary.",
                    "Run the query against a trial or study that has observation records.",
                ],
            )

        observations_by_trait: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for observation in observations:
            observations_by_trait[str(observation.get("trait_name") or "unknown_trait")].append(
                observation
            )

        summaries: list[TraitSummary] = []
        warnings: list[str] = []
        for trait_name, trait_observations in sorted(observations_by_trait.items()):
            count = len(trait_observations)
            if count < self.MIN_OBSERVATIONS_FOR_STATS:
                warnings.append(
                    f"{trait_name} has only {count} observations and was excluded from summary"
                )
                continue
            stats = _calculate_basic_stats(trait_observations)
            summaries.append(
                TraitSummary(
                    trait_name=trait_name,
                    n_observations=int(stats["count"]),
                    mean=float(stats["mean"]),
                    std_dev=_std_dev_for_count(stats, int(stats["count"])),
                    cv=_cv_for_stats(stats, int(stats["count"])),
                    min_val=float(stats["min"]),
                    max_val=float(stats["max"]),
                )
            )

        if not summaries:
            return self._safe_failure_result(
                reason="insufficient_trial_observations",
                explanation=(
                    "Observations were found, but no trait has enough records for a "
                    "trial-level summary."
                ),
                data_available={
                    "observations": len(observations),
                    "germplasm": len(_distinct_values(observations, "germplasm_id")),
                    "traits": len(observations_by_trait),
                },
                data_needed={"min_observations_per_trait": self.MIN_OBSERVATIONS_FOR_STATS},
                suggestions=[
                    "Add more observations for at least one trait.",
                    "Broaden the summary to include more study records.",
                ],
            )

        primary_trait = _select_primary_trait(summaries)
        ranking = self.compute_ranking(observations, primary_trait)
        top_performers = [
            RankedEntry(**entry)
            for entry in ranking.data.get("entries", [])[:5]
            if ranking.status == "success"
        ]
        summary = TrialSummary(
            trial_name=trial_name,
            n_entries=len(_distinct_values(observations, "germplasm_id")),
            n_observations=len(observations),
            traits=summaries,
            top_performers=top_performers,
        )

        return AnalyticsResult(
            status="success",
            data={
                "trial_summary": asdict(summary),
                "primary_trait": primary_trait,
            },
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id="analytics:trial_summary",
                    query_or_method="analytics_engine.compute_trial_summary",
                )
            ],
            calculation_steps=[
                CalculationStep(
                    step_id="analytics:trial_summary",
                    formula="per-trait summary statistics and top performers by primary trait",
                    inputs={
                        "trial_name": trial_name,
                        "primary_trait": primary_trait,
                        "n_observations": len(observations),
                    },
                )
            ],
            uncertainty=UncertaintyInfo(
                confidence=0.73 if warnings else 0.84,
                missing_data=warnings,
            ),
            warnings=warnings,
        )

    def _compute_germplasm_trait_stats(
        self,
        trait_name: str,
        observations: list[dict[str, Any]],
        warnings: list[str],
    ) -> list[GermplasmTraitStats]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for observation in observations:
            grouped[str(observation.get("germplasm_id") or "unknown")].append(observation)

        result: list[GermplasmTraitStats] = []
        for germplasm_id, germplasm_observations in sorted(grouped.items()):
            stats = _calculate_basic_stats(germplasm_observations)
            count = int(stats["count"])
            insufficient_data = count < self.MIN_OBSERVATIONS_FOR_STATS
            if insufficient_data:
                warnings.append(
                    f"{germplasm_id} has only {count} observations for {trait_name}"
                )

            first = germplasm_observations[0]
            result.append(
                GermplasmTraitStats(
                    germplasm_id=germplasm_id,
                    germplasm_name=str(first.get("germplasm_name") or germplasm_id),
                    n=count,
                    mean=float(stats["mean"]),
                    std_dev=_std_dev_for_count(stats, count),
                    cv=_cv_for_stats(stats, count),
                    min_val=float(stats["min"]),
                    max_val=float(stats["max"]),
                    insufficient_data=insufficient_data,
                )
            )
        return result

    def _safe_failure_result(
        self,
        *,
        reason: str,
        explanation: str,
        data_available: dict[str, int],
        data_needed: dict[str, int],
        suggestions: list[str],
    ) -> AnalyticsResult:
        failure = SafeFailure(
            reason=reason,
            explanation=explanation,
            data_available=data_available,
            data_needed=data_needed,
            suggestions=suggestions,
        )
        return AnalyticsResult(
            status="insufficient_data",
            data={"safe_failure": asdict(failure)},
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id=f"analytics:{reason}",
                    query_or_method="analytics_engine.safe_failure",
                )
            ],
            calculation_steps=[
                CalculationStep(
                    step_id=f"analytics:{reason}",
                    formula="input_count < required_minimum",
                    inputs={
                        "data_available": data_available,
                        "data_needed": data_needed,
                    },
                )
            ],
            uncertainty=UncertaintyInfo(
                confidence=0.25,
                missing_data=[explanation],
            ),
            warnings=[explanation],
        )


def extract_observations(context: IntermediateResultContext) -> list[dict[str, Any]]:
    """Walk successful REEVU step results and normalize numeric observations."""
    normalized: list[dict[str, Any]] = []
    dropped_non_numeric = 0

    for result in context.all_results():
        if result.status != "success":
            continue

        observations = result.records.get("observations", [])
        if not isinstance(observations, list):
            continue

        for observation in observations:
            if not isinstance(observation, dict):
                continue

            value = _parse_numeric_value(_first_present(
                observation,
                ("value", "observation_value", "observationValue", "value_numeric", "valueNumeric"),
            ))
            if value is None:
                dropped_non_numeric += 1
                continue

            germplasm = _nested_dict(observation, "germplasm")
            trait = _nested_dict(observation, "trait")
            observation_variable = _nested_dict(observation, "observation_variable")
            if not observation_variable:
                observation_variable = _nested_dict(observation, "observationVariable")

            germplasm_id = _string_or_none(
                _first_present(
                    observation,
                    (
                        "germplasm_id",
                        "germplasmId",
                        "germplasm_db_id",
                        "germplasmDbId",
                    ),
                )
            ) or _string_or_none(_first_present(germplasm, ("id", "db_id", "dbId")))
            germplasm_name = _string_or_none(
                _first_present(observation, ("germplasm_name", "germplasmName"))
            ) or _string_or_none(_first_present(germplasm, ("name", "defaultDisplayName")))

            trait_name = (
                _string_or_none(
                    _first_present(
                        observation,
                        (
                            "trait_name",
                            "traitName",
                            "variable_name",
                            "variableName",
                            "observation_variable_name",
                            "observationVariableName",
                        ),
                    )
                )
                or _string_or_none(_first_present(trait, ("name", "traitName")))
                or _string_or_none(_first_present(observation_variable, ("name", "traitName")))
            )

            observation_db_id = _string_or_none(
                _first_present(
                    observation,
                    ("observation_db_id", "observationDbId", "observation_id", "observationId", "id"),
                )
            )

            normalized.append({
                "value": value,
                "germplasm_id": germplasm_id or "unknown",
                "germplasm_name": germplasm_name or germplasm_id or "Unknown germplasm",
                "trait_name": trait_name or "unknown_trait",
                "observation_db_id": observation_db_id,
                "source_step_id": result.step_id,
            })

    if dropped_non_numeric:
        logger.warning(
            "Dropped %s non-numeric REEVU observations during analytics extraction",
            dropped_non_numeric,
        )

    return normalized


def _first_present(source: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in source and source[key] is not None:
            return source[key]
    return None


def _nested_dict(source: dict[str, Any], key: str) -> dict[str, Any]:
    value = source.get(key)
    return value if isinstance(value, dict) else {}


def _parse_numeric_value(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _filter_observations_by_trait(
    observations: list[dict[str, Any]],
    trait_filter: str | None,
) -> list[dict[str, Any]]:
    if not trait_filter:
        return list(observations)
    normalized_filter = trait_filter.casefold()
    return [
        observation
        for observation in observations
        if str(observation.get("trait_name") or "").casefold() == normalized_filter
    ]


def _calculate_basic_stats(observations: list[dict[str, Any]]) -> dict[str, Any]:
    return _trial_statistics_for_observations(observations).calculate_basic_stats()


def _trial_statistics_for_observations(observations: list[dict[str, Any]]) -> TrialStatistics:
    return TrialStatistics(
        [
            ObservationData(
                value=float(observation["value"]),
                germplasm_id=str(observation.get("germplasm_id") or "unknown"),
            )
            for observation in observations
        ]
    )


def _group_by_germplasm(
    observations: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        grouped[str(observation.get("germplasm_id") or "unknown")].append(observation)
    return grouped


def _build_group_stats(
    germplasm_id: str,
    observations: list[dict[str, Any]],
) -> GroupStats:
    stats = _calculate_basic_stats(observations)
    count = int(stats["count"])
    first = observations[0]
    return GroupStats(
        germplasm_id=germplasm_id,
        germplasm_name=str(first.get("germplasm_name") or germplasm_id),
        n=count,
        mean=float(stats["mean"]),
        std_dev=_std_dev_for_count(stats, count),
    )


def _std_dev_for_count(stats: dict[str, Any], count: int) -> float | None:
    if count < 2 or stats.get("std_dev") is None:
        return None
    return float(stats["std_dev"])


def _cv_for_stats(stats: dict[str, Any], count: int) -> float | None:
    mean = stats.get("mean")
    cv = stats.get("cv")
    if count < 2 or mean in (None, 0) or cv is None:
        return None
    return float(cv)


def _distinct_values(observations: list[dict[str, Any]], key: str) -> set[str]:
    return {str(observation.get(key) or "unknown") for observation in observations}


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _anova_p_value(
    f_value: float | None,
    df_genotype: Any,
    df_error: Any,
) -> float | None:
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


def _select_primary_trait(summaries: list[TraitSummary]) -> str:
    return sorted(
        summaries,
        key=lambda summary: (-summary.n_observations, summary.trait_name),
    )[0].trait_name
