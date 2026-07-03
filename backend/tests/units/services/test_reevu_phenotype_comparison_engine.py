"""Unit tests for the REEVU phenotype comparison engine."""

from __future__ import annotations

import statistics

from dataclasses import asdict

from hypothesis import given, settings, strategies as st
import pytest

from app.modules.ai.services.reevu.phenotype_comparison_engine import (
    ComparisonEngineResult,
    GermplasmProfile,
    GroupStats,
    MultiEnvComparisonResult,
    PhenotypeComparisonEngine,
    TraitProfileResult,
)


def _observation(
    value: float,
    germplasm_id: str,
    *,
    trait_name: str = "Yield",
    germplasm_name: str | None = None,
    environment: str | None = None,
) -> dict[str, object]:
    observation = {
        "value": value,
        "germplasm_id": germplasm_id,
        "germplasm_name": germplasm_name or germplasm_id,
        "trait_name": trait_name,
    }
    if environment:
        observation["environment"] = environment
    return observation


def _observations_by_germplasm(group_values: dict[str, list[float]]) -> dict[str, list[dict[str, object]]]:
    return {
        germplasm_id: [_observation(value, germplasm_id) for value in values]
        for germplasm_id, values in group_values.items()
    }


def test_data_models_construct_with_valid_data():
    group = GroupStats(
        germplasm_id="G1",
        germplasm_name="Line A",
        n=3,
        mean=4.2,
        std_dev=0.2,
    )
    comparison = ComparisonEngineResult(
        trait_name="Yield",
        test_type="t_test",
        groups=[group],
        f_value=3.0,
        p_value=0.04,
        significant=True,
        lsd=0.5,
    )
    profile = GermplasmProfile(
        germplasm_id="G1",
        germplasm_name="Line A",
        raw_values={"Yield": 4.2},
        normalized_values={"Yield": 1.0},
    )
    trait_profile = TraitProfileResult(traits=["Yield"], profiles=[profile])
    multi_env = MultiEnvComparisonResult(
        trait_name="Yield",
        environments=["Env A"],
        per_env_means={"Env A": {"G1": 4.2}},
        overall_means={"G1": 4.2},
        stability_flags={"G1": "stable"},
        gxe_detected=False,
    )

    assert comparison.groups == [group]
    assert trait_profile.profiles == [profile]
    assert multi_env.overall_means == {"G1": 4.2}
    assert asdict(comparison)["significant"] is True


def test_engine_skeleton_constant_matches_spec():
    assert PhenotypeComparisonEngine.MIN_OBSERVATIONS_PER_GROUP == 3


@settings(max_examples=100)
@given(group_means=st.lists(
    st.floats(min_value=1, max_value=100, allow_nan=False, allow_infinity=False),
    min_size=2,
    max_size=4,
    unique=True,
))
def test_compare_selects_test_type_and_significance(group_means: list[float]):
    group_values = {
        f"G{index}": [mean - 0.1, mean, mean + 0.1]
        for index, mean in enumerate(group_means, start=1)
    }
    result = PhenotypeComparisonEngine().compare(
        list(group_values),
        _observations_by_germplasm(group_values),
        trait_name="Yield",
    )

    assert result.insufficient_data is False
    assert result.test_type == ("t_test" if len(group_values) == 2 else "anova")
    assert isinstance(result.p_value, float)
    assert result.significant is (result.p_value < 0.05)
    assert result.evidence_refs
    assert result.calculation_steps


def test_compare_returns_insufficient_data_when_any_group_is_underpowered():
    result = PhenotypeComparisonEngine().compare(
        ["G1", "G2"],
        _observations_by_germplasm({
            "G1": [4.0, 4.2, 4.4],
            "G2": [5.0],
        }),
        trait_name="Yield",
    )

    assert result.insufficient_data is True
    assert result.reason
    assert [group.n for group in result.groups] == [3, 1]


def test_build_trait_profile_normalizes_trait_means():
    observations = {
        "G1": [
            _observation(4.0, "G1", trait_name="Yield"),
            _observation(90.0, "G1", trait_name="Height"),
        ],
        "G2": [
            _observation(6.0, "G2", trait_name="Yield"),
            _observation(100.0, "G2", trait_name="Height"),
        ],
    }

    result = PhenotypeComparisonEngine().build_trait_profile(["G1", "G2"], observations)

    profiles = {profile.germplasm_id: profile for profile in result.profiles}
    assert result.traits == ["Height", "Yield"]
    assert profiles["G1"].normalized_values == {"Height": 0.0, "Yield": 0.0}
    assert profiles["G2"].normalized_values == {"Height": 1.0, "Yield": 1.0}
    assert profiles["G1"].raw_values["Yield"] == 4.0


def test_compare_multi_environment_flags_stability_and_gxe():
    observations = {
        "G1": {
            "Env A": [_observation(10.0, "G1"), _observation(10.5, "G1")],
            "Env B": [_observation(3.0, "G1"), _observation(3.5, "G1")],
        },
        "G2": {
            "Env A": [_observation(8.0, "G2"), _observation(8.5, "G2")],
            "Env B": [_observation(12.0, "G2"), _observation(12.5, "G2")],
        },
    }

    result = PhenotypeComparisonEngine().compare_multi_environment(
        ["G1", "G2"],
        observations,
        trait_name="Yield",
    )

    assert result.gxe_detected is True
    assert result.stability_flags["G1"] == "unstable"
    assert result.stability_flags["G2"] == "unstable"
    assert result.overall_means["G1"] == pytest.approx(statistics.mean([10.25, 3.25]))
    assert result.overall_means["G2"] == pytest.approx(statistics.mean([8.25, 12.25]))
