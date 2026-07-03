"""Unit tests for the REEVU analytics engine foundation."""

from __future__ import annotations

import logging
import statistics

from hypothesis import given, settings, strategies as st
import pytest

from app.modules.ai.services.reevu.analytics_engine import (
    AnalyticsEngine,
    AnalyticsResult,
    ComparisonResult,
    GermplasmTraitStats,
    GroupStats,
    RankedEntry,
    SafeFailure,
    TraitStats,
    TraitSummary,
    TrialSummary,
    extract_observations,
)
from app.modules.ai.services.reevu.step_executor import IntermediateResultContext, StepResult
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef, UncertaintyInfo


def _context_with(*results: StepResult) -> IntermediateResultContext:
    context = IntermediateResultContext()
    for result in results:
        context.add(result)
    return context


def _observation(
    value: float,
    germplasm_id: str,
    *,
    trait_name: str = "Yield",
    germplasm_name: str | None = None,
) -> dict[str, object]:
    return {
        "value": value,
        "germplasm_id": germplasm_id,
        "germplasm_name": germplasm_name or germplasm_id,
        "trait_name": trait_name,
        "observation_db_id": f"{germplasm_id}-{value}",
        "source_step_id": "breed-1",
    }


def _observations_for_groups(
    group_values: dict[str, list[float]],
    *,
    trait_name: str = "Yield",
) -> list[dict[str, object]]:
    return [
        _observation(value, germplasm_id, trait_name=trait_name)
        for germplasm_id, values in group_values.items()
        for value in values
    ]


def _assert_evidence_envelope_complete(result: AnalyticsResult):
    assert result.evidence_refs
    assert any(
        ref.source_type == "function" and ref.query_or_method
        for ref in result.evidence_refs
    )
    assert result.calculation_steps
    assert all(step.step_id and step.formula for step in result.calculation_steps)
    assert result.uncertainty.confidence is not None
    assert 0.0 <= result.uncertainty.confidence <= 1.0


def test_analytics_data_models_construct_with_valid_data():
    """All analytics dataclasses can represent their documented output shapes."""
    germplasm_stats = GermplasmTraitStats(
        germplasm_id="G1",
        germplasm_name="Line A",
        n=3,
        mean=4.2,
        std_dev=0.2,
        cv=4.76,
        min_val=4.0,
        max_val=4.4,
    )
    trait_stats = TraitStats(
        trait_name="Grain yield",
        n_observations=3,
        n_germplasm=1,
        overall_mean=4.2,
        overall_std_dev=0.2,
        overall_cv=4.76,
        overall_min=4.0,
        overall_max=4.4,
        per_germplasm=[germplasm_stats],
    )
    ranked_entry = RankedEntry(
        rank=1,
        germplasm_id="G1",
        germplasm_name="Line A",
        trait_name="Grain yield",
        mean=4.2,
        n=3,
        cv=4.76,
    )
    group_stats = GroupStats(
        germplasm_id="G1",
        germplasm_name="Line A",
        n=3,
        mean=4.2,
        std_dev=0.2,
    )
    comparison = ComparisonResult(
        trait_name="Grain yield",
        test_type="t_test",
        groups=[group_stats],
        f_value=3.14,
        p_value=0.04,
        significant=True,
        lsd=0.5,
    )
    trait_summary = TraitSummary(
        trait_name="Grain yield",
        n_observations=3,
        mean=4.2,
        std_dev=0.2,
        cv=4.76,
        min_val=4.0,
        max_val=4.4,
    )
    trial_summary = TrialSummary(
        trial_name="Trial A",
        n_entries=1,
        n_observations=3,
        traits=[trait_summary],
        top_performers=[ranked_entry],
    )
    safe_failure = SafeFailure(
        reason="insufficient_observations",
        explanation="At least three observations are needed.",
        data_available={"observations": 2},
        data_needed={"min_observations": 3},
        suggestions=["Record more phenotypic observations."],
    )
    result = AnalyticsResult(
        status="success",
        data={
            "trait_stats": trait_stats,
            "comparison": comparison,
            "trial_summary": trial_summary,
            "safe_failure": safe_failure,
        },
        evidence_refs=[
            EvidenceRef(
                source_type="function",
                entity_id="analytics:test",
                query_or_method="analytics_engine.compute_descriptive_stats",
            )
        ],
        calculation_steps=[
            CalculationStep(
                step_id="analytics:basic_stats",
                formula="mean = sum(values) / n",
            )
        ],
        uncertainty=UncertaintyInfo(confidence=0.9, missing_data=[]),
    )

    assert result.status == "success"
    assert result.data["trait_stats"].per_germplasm == [germplasm_stats]
    assert result.data["comparison"].groups == [group_stats]
    assert result.data["trial_summary"].top_performers == [ranked_entry]
    assert result.data["safe_failure"].suggestions == ["Record more phenotypic observations."]
    assert result.evidence_refs[0].source_type == "function"
    assert result.calculation_steps[0].step_id == "analytics:basic_stats"
    assert result.uncertainty.confidence == 0.9


def test_analytics_data_model_defaults_are_isolated():
    """Mutable defaults are independent across instances."""
    first_result = AnalyticsResult(status="success")
    second_result = AnalyticsResult(status="success")
    first_result.warnings.append("low_sample_size")

    first_failure = SafeFailure(reason="no_observations", explanation="No observations found.")
    second_failure = SafeFailure(reason="no_observations", explanation="No observations found.")
    first_failure.suggestions.append("Add observations.")

    comparison = ComparisonResult(trait_name="Yield", test_type="anova")
    trial_summary = TrialSummary(trial_name=None, n_entries=0, n_observations=0)

    assert first_result.warnings == ["low_sample_size"]
    assert second_result.warnings == []
    assert first_failure.suggestions == ["Add observations."]
    assert second_failure.suggestions == []
    assert comparison.groups == []
    assert trial_summary.traits == []
    assert trial_summary.top_performers == []


def test_analytics_engine_threshold_constants_match_spec():
    engine = AnalyticsEngine()

    assert engine.MIN_OBSERVATIONS_FOR_STATS == 3
    assert engine.MIN_OBSERVATIONS_FOR_COMPARISON == 3
    assert engine.MIN_GROUPS_FOR_ANOVA == 3


def test_extract_observations_from_breeding_step_records():
    context = _context_with(
        StepResult(
            step_id="breed-1",
            domain="breeding",
            status="success",
            records={
                "observations": [
                    {
                        "value": "4.2",
                        "germplasm": {"id": "G1", "name": "Line A"},
                        "trait_name": "Grain yield",
                        "observation_db_id": "OBS1",
                    }
                ]
            },
        )
    )

    observations = extract_observations(context)

    assert observations == [
        {
            "value": 4.2,
            "germplasm_id": "G1",
            "germplasm_name": "Line A",
            "trait_name": "Grain yield",
            "observation_db_id": "OBS1",
            "source_step_id": "breed-1",
        }
    ]


def test_extract_observations_from_trials_step_records():
    context = _context_with(
        StepResult(
            step_id="trial-1",
            domain="trials",
            status="success",
            records={
                "observations": [
                    {
                        "observationValue": 120,
                        "germplasmDbId": 42,
                        "germplasmName": "Line B",
                        "observationVariable": {"name": "Plant height"},
                        "observationDbId": "OBS2",
                    }
                ]
            },
        )
    )

    observations = extract_observations(context)

    assert observations == [
        {
            "value": 120.0,
            "germplasm_id": "42",
            "germplasm_name": "Line B",
            "trait_name": "Plant height",
            "observation_db_id": "OBS2",
            "source_step_id": "trial-1",
        }
    ]


def test_extract_observations_from_mixed_sources():
    context = _context_with(
        StepResult(
            step_id="trial-1",
            domain="trials",
            status="success",
            records={
                "observations": [
                    {
                        "observation_value": "8.0",
                        "germplasm_id": "T1",
                        "germplasm_name": "Trial line",
                        "variable_name": "Days to flowering",
                        "id": "TOBS1",
                    }
                ]
            },
        ),
        StepResult(
            step_id="breed-1",
            domain="breeding",
            status="success",
            records={
                "observations": [
                    {
                        "valueNumeric": "9.5",
                        "germplasm": {"dbId": "B1", "defaultDisplayName": "Breeding line"},
                        "trait": {"name": "Days to flowering"},
                        "observationId": "BOBS1",
                    }
                ]
            },
        ),
    )

    observations = extract_observations(context)

    assert [obs["source_step_id"] for obs in observations] == ["trial-1", "breed-1"]
    assert [obs["value"] for obs in observations] == [8.0, 9.5]
    assert [obs["germplasm_id"] for obs in observations] == ["T1", "B1"]
    assert {obs["trait_name"] for obs in observations} == {"Days to flowering"}


def test_extract_observations_drops_non_numeric_values(caplog: pytest.LogCaptureFixture):
    context = _context_with(
        StepResult(
            step_id="breed-1",
            domain="breeding",
            status="success",
            records={
                "observations": [
                    {"value": "bad", "germplasm_id": "G1", "trait_name": "Yield"},
                    {"value": "nan", "germplasm_id": "G2", "trait_name": "Yield"},
                    {"value": "4.8", "germplasm_id": "G3", "trait_name": "Yield"},
                ]
            },
        )
    )

    with caplog.at_level(logging.WARNING):
        observations = extract_observations(context)

    assert [obs["value"] for obs in observations] == [4.8]
    assert "Dropped 2 non-numeric REEVU observations" in caplog.text


def test_extract_observations_empty_context_returns_empty_list():
    assert extract_observations(IntermediateResultContext()) == []


def test_extract_observations_skips_failed_and_skipped_steps():
    context = _context_with(
        StepResult(
            step_id="failed-1",
            domain="breeding",
            status="failed",
            records={
                "observations": [
                    {"value": 4.2, "germplasm_id": "G1", "trait_name": "Yield"}
                ]
            },
        ),
        StepResult(
            step_id="skipped-1",
            domain="trials",
            status="skipped",
            records={
                "observations": [
                    {"value": 5.2, "germplasm_id": "G2", "trait_name": "Yield"}
                ]
            },
        ),
    )

    assert extract_observations(context) == []


@settings(max_examples=100)
@given(
    values=st.lists(
        st.floats(
            min_value=0.001,
            max_value=1_000,
            allow_nan=False,
            allow_infinity=False,
        ),
        min_size=3,
        max_size=20,
    )
)
def test_compute_descriptive_stats_matches_independent_statistics(values: list[float]):
    """Feature: reevu-analytics-engine, Property 1: descriptive stats correctness."""
    observations = [
        {
            "value": value,
            "germplasm_id": "G1",
            "germplasm_name": "Line A",
            "trait_name": "Grain yield",
            "observation_db_id": f"OBS{index}",
            "source_step_id": "breed-1",
        }
        for index, value in enumerate(values)
    ]

    result = AnalyticsEngine().compute_descriptive_stats(observations)

    assert result.status == "success"
    trait_stats = result.data["traits"][0]
    germplasm_stats = trait_stats["per_germplasm"][0]
    expected_mean = statistics.mean(values)
    expected_std_dev = statistics.stdev(values)
    expected_cv = None if expected_mean == 0 else expected_std_dev / expected_mean * 100

    assert trait_stats["overall_mean"] == pytest.approx(expected_mean)
    assert trait_stats["overall_std_dev"] == pytest.approx(expected_std_dev)
    if expected_cv is None:
        assert trait_stats["overall_cv"] is None
    else:
        assert trait_stats["overall_cv"] == pytest.approx(expected_cv)
    assert trait_stats["overall_min"] == min(values)
    assert trait_stats["overall_max"] == max(values)
    assert germplasm_stats["mean"] == pytest.approx(expected_mean)
    assert germplasm_stats["std_dev"] == pytest.approx(expected_std_dev)
    assert germplasm_stats["n"] == len(values)
    assert germplasm_stats["insufficient_data"] is False


def test_compute_descriptive_stats_empty_observations_returns_safe_failure():
    result = AnalyticsEngine().compute_descriptive_stats([])

    assert result.status == "insufficient_data"
    assert result.data["safe_failure"]["reason"] == "insufficient_observations"
    assert result.data["safe_failure"]["suggestions"]
    assert result.evidence_refs[0].source_type == "function"


def test_compute_descriptive_stats_single_observation_returns_safe_failure():
    result = AnalyticsEngine().compute_descriptive_stats([
        {
            "value": 4.2,
            "germplasm_id": "G1",
            "germplasm_name": "Line A",
            "trait_name": "Grain yield",
        }
    ])

    assert result.status == "insufficient_data"
    assert result.data["safe_failure"]["data_available"] == {
        "observations": 1,
        "germplasm": 1,
    }


def test_compute_descriptive_stats_trait_filter_limits_output_to_one_trait():
    observations = [
        {"value": 4.0, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Yield"},
        {"value": 4.2, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Yield"},
        {"value": 4.4, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Yield"},
        {"value": 90, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Height"},
        {"value": 95, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Height"},
        {"value": 100, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Height"},
    ]

    result = AnalyticsEngine().compute_descriptive_stats(observations, trait_filter="Yield")

    assert result.status == "success"
    assert result.data["trait_filter"] == "Yield"
    assert [stats["trait_name"] for stats in result.data["traits"]] == ["Yield"]


def test_compute_descriptive_stats_cv_is_none_when_mean_is_zero():
    observations = [
        {"value": -1.0, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Yield"},
        {"value": 0.0, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Yield"},
        {"value": 1.0, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Yield"},
    ]

    result = AnalyticsEngine().compute_descriptive_stats(observations)

    assert result.status == "success"
    trait_stats = result.data["traits"][0]
    assert trait_stats["overall_mean"] == 0.0
    assert trait_stats["overall_cv"] is None
    assert trait_stats["per_germplasm"][0]["cv"] is None


def test_compute_descriptive_stats_all_low_sample_groups_returns_safe_failure():
    observations = [
        {"value": 4.0, "germplasm_id": "G1", "germplasm_name": "Line A", "trait_name": "Yield"},
        {"value": 4.5, "germplasm_id": "G2", "germplasm_name": "Line B", "trait_name": "Yield"},
        {"value": 5.0, "germplasm_id": "G3", "germplasm_name": "Line C", "trait_name": "Yield"},
    ]

    result = AnalyticsEngine().compute_descriptive_stats(observations)

    assert result.status == "insufficient_data"
    assert result.data["safe_failure"]["reason"] == "insufficient_sample_size"
    assert result.data["safe_failure"]["data_needed"] == {"min_observations_per_entry": 3}


@settings(max_examples=100)
@given(
    group_values=st.dictionaries(
        keys=st.sampled_from(["G1", "G2", "G3", "G4"]),
        values=st.lists(
            st.floats(
                min_value=-1_000,
                max_value=1_000,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=1,
            max_size=5,
        ),
        min_size=2,
        max_size=4,
    )
)
def test_compute_ranking_orders_by_mean_and_flags_low_sample_entries(
    group_values: dict[str, list[float]],
):
    """Feature: reevu-analytics-engine, Property 2: ranking correctness."""
    result = AnalyticsEngine().compute_ranking(_observations_for_groups(group_values), "Yield")

    assert result.status == "success"
    entries = result.data["entries"]
    expected_order = [
        germplasm_id
        for germplasm_id, _mean in sorted(
            (
                (germplasm_id, statistics.mean(values))
                for germplasm_id, values in group_values.items()
            ),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    assert [entry["germplasm_id"] for entry in entries] == expected_order
    assert [entry["rank"] for entry in entries] == list(range(1, len(entries) + 1))
    for entry in entries:
        values = group_values[entry["germplasm_id"]]
        assert entry["mean"] == pytest.approx(statistics.mean(values))
        assert entry["n"] == len(values)
        assert entry["insufficient_data"] is (len(values) < 3)
        assert entry["flag"] == ("low_sample_size" if len(values) < 3 else None)


def test_compute_ranking_with_all_sufficient_entries():
    observations = _observations_for_groups({
        "G1": [4.0, 4.2, 4.4],
        "G2": [5.0, 5.2, 5.4],
    })

    result = AnalyticsEngine().compute_ranking(observations, "Yield")

    assert result.status == "success"
    assert [entry["germplasm_id"] for entry in result.data["entries"]] == ["G2", "G1"]
    assert all(entry["insufficient_data"] is False for entry in result.data["entries"])
    assert result.evidence_refs[0].query_or_method == "analytics_engine.compute_ranking"


def test_compute_ranking_flags_low_sample_entries_without_dropping_them():
    observations = _observations_for_groups({
        "G1": [4.0, 4.2, 4.4],
        "G2": [6.0],
    })

    result = AnalyticsEngine().compute_ranking(observations, "Yield")

    assert result.status == "success"
    entries_by_id = {entry["germplasm_id"]: entry for entry in result.data["entries"]}
    assert set(entries_by_id) == {"G1", "G2"}
    assert entries_by_id["G2"]["insufficient_data"] is True
    assert entries_by_id["G2"]["flag"] == "low_sample_size"
    assert result.warnings == ["G2 has only 1 observations for Yield"]


def test_compute_ranking_supports_ascending_direction():
    observations = _observations_for_groups({
        "G1": [4.0, 4.2, 4.4],
        "G2": [5.0, 5.2, 5.4],
    })

    result = AnalyticsEngine().compute_ranking(observations, "Yield", direction="asc")

    assert result.status == "success"
    assert [entry["germplasm_id"] for entry in result.data["entries"]] == ["G1", "G2"]


def test_compute_ranking_no_trait_observations_returns_safe_failure():
    result = AnalyticsEngine().compute_ranking(
        [_observation(4.2, "G1", trait_name="Height")],
        "Yield",
    )

    assert result.status == "insufficient_data"
    assert result.data["safe_failure"]["reason"] == "no_trait_observations"


@settings(max_examples=100)
@given(group_means=st.lists(
    st.floats(min_value=1, max_value=100, allow_nan=False, allow_infinity=False),
    min_size=2,
    max_size=4,
    unique=True,
))
def test_compute_comparison_selects_test_type_and_significance(group_means: list[float]):
    """Feature: reevu-analytics-engine, Property 3: comparison test selection."""
    group_values = {
        f"G{index}": [mean - 0.1, mean, mean + 0.1]
        for index, mean in enumerate(group_means, start=1)
    }

    result = AnalyticsEngine().compute_comparison(_observations_for_groups(group_values), "Yield")

    assert result.status == "success"
    comparison = result.data["comparison"]
    assert comparison["test_type"] == ("t_test" if len(group_values) == 2 else "anova")
    assert isinstance(comparison["p_value"], float)
    assert 0.0 <= comparison["p_value"] <= 1.0
    assert comparison["significant"] is (comparison["p_value"] < 0.05)


def test_compute_comparison_uses_t_test_for_two_groups():
    observations = _observations_for_groups({
        "G1": [4.0, 4.2, 4.4],
        "G2": [5.0, 5.2, 5.4],
    })

    result = AnalyticsEngine().compute_comparison(observations, "Yield")

    assert result.status == "success"
    assert result.data["comparison"]["test_type"] == "t_test"
    assert result.data["comparison"]["f_value"] is not None
    assert result.data["comparison"]["groups"][0]["n"] == 3


def test_compute_comparison_uses_anova_for_three_groups():
    observations = _observations_for_groups({
        "G1": [4.0, 4.2, 4.4],
        "G2": [5.0, 5.2, 5.4],
        "G3": [6.0, 6.2, 6.4],
    })

    result = AnalyticsEngine().compute_comparison(observations, "Yield")

    assert result.status == "success"
    assert result.data["comparison"]["test_type"] == "anova"
    assert result.data["included_group_ids"] == ["G1", "G2", "G3"]


def test_compute_comparison_fewer_than_two_qualifying_groups_returns_safe_failure():
    observations = _observations_for_groups({
        "G1": [4.0, 4.2, 4.4],
        "G2": [5.0],
    })

    result = AnalyticsEngine().compute_comparison(observations, "Yield")

    assert result.status == "insufficient_data"
    assert result.data["safe_failure"]["reason"] == "insufficient_comparison_groups"
    assert result.data["safe_failure"]["data_available"]["qualifying_groups"] == 1


def test_compute_comparison_group_ids_filter_limits_groups():
    observations = _observations_for_groups({
        "G1": [4.0, 4.2, 4.4],
        "G2": [5.0, 5.2, 5.4],
        "G3": [6.0, 6.2, 6.4],
    })

    result = AnalyticsEngine().compute_comparison(observations, "Yield", group_ids=["G1", "G3"])

    assert result.status == "success"
    assert result.data["comparison"]["test_type"] == "t_test"
    assert result.data["included_group_ids"] == ["G1", "G3"]
    assert [group["germplasm_id"] for group in result.data["comparison"]["groups"]] == ["G1", "G3"]


@settings(max_examples=100)
@given(
    trait_values=st.dictionaries(
        keys=st.sampled_from(["Flowering", "Height", "Yield"]),
        values=st.lists(
            st.floats(
                min_value=0.001,
                max_value=1_000,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=3,
            max_size=6,
        ),
        min_size=1,
        max_size=3,
    )
)
def test_compute_trial_summary_reports_trait_statistics_and_top_performers(
    trait_values: dict[str, list[float]],
):
    """Feature: reevu-analytics-engine, Property 4: trial summary correctness."""
    observations: list[dict[str, object]] = []
    for trait_name, values in trait_values.items():
        for index, value in enumerate(values):
            observations.append(_observation(value, f"G{index % 3}", trait_name=trait_name))

    result = AnalyticsEngine().compute_trial_summary(observations, trial_name="Trial A")

    assert result.status == "success"
    summary = result.data["trial_summary"]
    assert summary["trial_name"] == "Trial A"
    assert summary["n_observations"] == len(observations)
    assert summary["n_entries"] == len({observation["germplasm_id"] for observation in observations})

    trait_summaries = {trait["trait_name"]: trait for trait in summary["traits"]}
    for trait_name, values in trait_values.items():
        assert trait_summaries[trait_name]["mean"] == pytest.approx(statistics.mean(values))
        assert trait_summaries[trait_name]["n_observations"] == len(values)

    primary_trait = result.data["primary_trait"]
    primary_groups: dict[str, list[float]] = {}
    for observation in observations:
        if observation["trait_name"] == primary_trait:
            primary_groups.setdefault(str(observation["germplasm_id"]), []).append(
                float(observation["value"])
            )
    expected_top = [
        germplasm_id
        for germplasm_id, _mean in sorted(
            (
                (germplasm_id, statistics.mean(values))
                for germplasm_id, values in primary_groups.items()
            ),
            key=lambda item: item[1],
            reverse=True,
        )
    ][:5]
    assert [entry["germplasm_id"] for entry in summary["top_performers"]] == expected_top


def test_compute_trial_summary_with_single_trait():
    observations = _observations_for_groups({
        "G1": [4.0, 4.2, 4.4],
        "G2": [5.0, 5.2, 5.4],
    })

    result = AnalyticsEngine().compute_trial_summary(observations, trial_name="Trial A")

    assert result.status == "success"
    summary = result.data["trial_summary"]
    assert summary["n_entries"] == 2
    assert summary["n_observations"] == 6
    assert [trait["trait_name"] for trait in summary["traits"]] == ["Yield"]
    assert len(summary["top_performers"]) == 2


def test_compute_trial_summary_with_multiple_traits_selects_most_observed_trait():
    observations = [
        *_observations_for_groups(
            {"G1": [4.0, 4.2, 4.4], "G2": [5.0, 5.2, 5.4]},
            trait_name="Yield",
        ),
        *_observations_for_groups(
            {"G1": [90.0, 91.0, 92.0]},
            trait_name="Height",
        ),
    ]

    result = AnalyticsEngine().compute_trial_summary(observations, trial_name="Trial A")

    assert result.status == "success"
    assert result.data["primary_trait"] == "Yield"
    assert [trait["trait_name"] for trait in result.data["trial_summary"]["traits"]] == [
        "Height",
        "Yield",
    ]


def test_compute_trial_summary_no_observations_returns_safe_failure():
    result = AnalyticsEngine().compute_trial_summary([])

    assert result.status == "insufficient_data"
    assert result.data["safe_failure"]["reason"] == "no_observations"


def test_compute_trial_summary_no_trait_with_enough_observations_returns_safe_failure():
    observations = [
        _observation(4.0, "G1", trait_name="Yield"),
        _observation(90.0, "G1", trait_name="Height"),
    ]

    result = AnalyticsEngine().compute_trial_summary(observations)

    assert result.status == "insufficient_data"
    assert result.data["safe_failure"]["reason"] == "insufficient_trial_observations"


@settings(max_examples=100)
@given(base=st.floats(min_value=1, max_value=100, allow_nan=False, allow_infinity=False))
def test_successful_computations_emit_complete_evidence_envelopes(base: float):
    """Feature: reevu-analytics-engine, Property 5: evidence envelope completeness."""
    observations = _observations_for_groups({
        "G1": [base, base + 0.1, base + 0.2],
        "G2": [base + 1.0, base + 1.1, base + 1.2],
        "G3": [base + 2.0, base + 2.1, base + 2.2],
    })
    engine = AnalyticsEngine()

    results = [
        engine.compute_descriptive_stats(observations),
        engine.compute_ranking(observations, "Yield"),
        engine.compute_comparison(observations, "Yield"),
        engine.compute_trial_summary(observations),
    ]

    for result in results:
        assert result.status == "success"
        _assert_evidence_envelope_complete(result)


@settings(max_examples=100)
@given(count=st.integers(min_value=0, max_value=2))
def test_safe_failure_threshold_for_insufficient_data(count: int):
    """Feature: reevu-analytics-engine, Property 6: safe failure threshold."""
    observations = [
        _observation(float(index + 1), "G1")
        for index in range(count)
    ]

    result = AnalyticsEngine().compute_descriptive_stats(observations)

    assert result.status == "insufficient_data"
    failure = result.data["safe_failure"]
    assert failure["explanation"]
    assert failure["suggestions"]
    assert "traits" not in result.data
    _assert_evidence_envelope_complete(result)
