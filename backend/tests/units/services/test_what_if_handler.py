"""
TDD tests for REEVU What-If & Predictive Queries.

Written BEFORE the implementation. RED → GREEN → REFACTOR.

Covers:
- Task 1: What-if detection (_classify_what_if, _extract_what_if_params)
- Task 2: WhatIfResult dataclass + WhatIfQueryHandler skeleton
- Task 3: Cross prediction handler
- Task 4: Selection scenario handler
- Task 5: Environmental scenario handler
- Task 6: FunctionExecutor wiring (intent detection)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.ai.services.reevu.what_if_handler import (
    WhatIfQueryHandler,
    WhatIfResult,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_db() -> AsyncMock:
    return AsyncMock()


def _make_germplasm_service(results: list[dict] | None = None) -> AsyncMock:
    svc = AsyncMock()
    svc.search = AsyncMock(return_value=results or [])
    return svc


def _make_obs_service(results: list[dict] | None = None) -> AsyncMock:
    svc = AsyncMock()
    svc.search = AsyncMock(return_value=results or [])
    return svc


def _obs(value: float, germplasm_id: str = "G1", trait: str = "yield") -> dict:
    return {
        "observation_variable_name": trait,
        "value": str(value),
        "germplasm_id": germplasm_id,
        "germplasm_name": f"Germplasm {germplasm_id}",
    }


# ── Task 1: What-if detection ─────────────────────────────────────────────────

def test_classify_what_if_cross_prediction():
    """Messages with parent/cross terms → 'cross_prediction'."""
    handler = WhatIfQueryHandler()
    for msg in [
        "what if I crossed IR64 with Swarna?",
        "what would happen if I cross parent A with parent B?",
        "predict the cross between variety X and variety Y",
        "if i cross these two parents",
    ]:
        result = handler._classify_what_if(msg)
        assert result == "cross_prediction", f"Expected cross_prediction for: '{msg}'"


def test_classify_what_if_selection_scenario():
    """Messages with selection/advance/top N% terms → 'selection_scenario'."""
    handler = WhatIfQueryHandler()
    for msg in [
        "what if I select the top 10%?",
        "what happens when I advance the top 5 entries?",
        "simulate selecting the best 20% for yield",
        "if i select top 15 percent",
    ]:
        result = handler._classify_what_if(msg)
        assert result == "selection_scenario", f"Expected selection_scenario for: '{msg}'"


def test_classify_what_if_environmental_scenario():
    """Messages with weather/rainfall/drought/climate terms → 'environmental_scenario'."""
    handler = WhatIfQueryHandler()
    for msg in [
        "what if rainfall drops 20%?",
        "what would happen if drought hits during flowering?",
        "simulate a 30% reduction in rainfall",
        "if drought occurs what yield can I expect",
        "what if temperature rises by 2 degrees",
    ]:
        result = handler._classify_what_if(msg)
        assert result == "environmental_scenario", f"Expected environmental_scenario for: '{msg}'"


def test_classify_what_if_returns_unknown_for_ambiguous():
    """Ambiguous what-if messages → 'unknown'."""
    handler = WhatIfQueryHandler()
    result = handler._classify_what_if("what if something happens?")
    assert result == "unknown"


def test_extract_what_if_params_cross_prediction():
    """Extracts parent names from cross prediction message."""
    handler = WhatIfQueryHandler()
    params = handler._extract_what_if_params(
        "what if I crossed IR64 with Swarna?", "cross_prediction"
    )
    assert "parent1" in params or "parents" in params


def test_extract_what_if_params_selection_scenario():
    """Extracts selection intensity from selection scenario message."""
    handler = WhatIfQueryHandler()
    params = handler._extract_what_if_params(
        "what if I select the top 10%?", "selection_scenario"
    )
    assert "selection_intensity" in params
    assert abs(params["selection_intensity"] - 0.10) < 0.01


def test_extract_what_if_params_selection_scenario_top_n():
    """Extracts top N count from selection scenario message."""
    handler = WhatIfQueryHandler()
    params = handler._extract_what_if_params(
        "what if I advance the top 5 entries?", "selection_scenario"
    )
    assert "top_n" in params or "selection_intensity" in params


def test_extract_what_if_params_environmental_scenario():
    """Extracts environmental parameter and magnitude."""
    handler = WhatIfQueryHandler()
    params = handler._extract_what_if_params(
        "what if rainfall drops 20%?", "environmental_scenario"
    )
    assert "environmental_factor" in params
    assert "magnitude" in params
    assert abs(params["magnitude"] - (-20.0)) < 0.1 or abs(params["magnitude"] - 20.0) < 0.1


# ── Task 2: WhatIfResult dataclass ────────────────────────────────────────────

def test_what_if_result_has_required_fields():
    result = WhatIfResult(
        query_type="cross_prediction",
        prediction={"predicted_mean": 4.5},
        confidence=0.7,
        assumptions=["Additive genetic model assumed"],
        limitations=["Prediction accuracy depends on training data size"],
        insufficient_data=False,
        reason=None,
        evidence_refs=[],
        is_prediction=True,
    )
    assert result.is_prediction is True
    assert result.query_type == "cross_prediction"
    assert len(result.assumptions) >= 1
    assert len(result.limitations) >= 1


def test_what_if_result_insufficient_data_flag():
    result = WhatIfResult(
        query_type="cross_prediction",
        prediction={},
        confidence=0.0,
        assumptions=[],
        limitations=[],
        insufficient_data=True,
        reason="Parent germplasm not found",
        evidence_refs=[],
        is_prediction=True,
    )
    assert result.insufficient_data is True
    assert result.reason is not None


# ── Task 3: Cross prediction handler ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_cross_prediction_returns_result_with_is_prediction_true():
    """Valid parent IDs → WhatIfResult with is_prediction=True and non-empty assumptions."""
    handler = WhatIfQueryHandler()
    germplasm_svc = _make_germplasm_service([
        {"id": "10", "germplasm_name": "IR64", "gebv": 0.85},
        {"id": "20", "germplasm_name": "Swarna", "gebv": 0.72},
    ])

    result = await handler._handle_cross_prediction(
        params={"parent1": "IR64", "parent2": "Swarna"},
        db=_make_db(),
        organization_id=1,
        germplasm_search_service=germplasm_svc,
    )

    assert isinstance(result, WhatIfResult)
    assert result.is_prediction is True
    assert len(result.assumptions) >= 1
    assert len(result.limitations) >= 1
    assert not result.insufficient_data


@pytest.mark.asyncio
async def test_cross_prediction_returns_insufficient_data_when_parents_not_found():
    """When parent germplasm cannot be resolved → insufficient_data=True."""
    handler = WhatIfQueryHandler()
    germplasm_svc = _make_germplasm_service([])  # no results

    result = await handler._handle_cross_prediction(
        params={"parent1": "UnknownA", "parent2": "UnknownB"},
        db=_make_db(),
        organization_id=1,
        germplasm_search_service=germplasm_svc,
    )

    assert result.insufficient_data is True
    assert result.reason is not None


@pytest.mark.asyncio
async def test_cross_prediction_includes_predicted_mean_in_prediction():
    """Cross prediction includes predicted_mean in prediction dict."""
    handler = WhatIfQueryHandler()
    # Use side_effect so each call returns a different parent
    germplasm_svc = AsyncMock()
    germplasm_svc.search = AsyncMock(side_effect=[
        [{"id": "10", "germplasm_name": "IR64", "gebv": 0.8}],   # parent1 query
        [{"id": "20", "germplasm_name": "Swarna", "gebv": 0.6}], # parent2 query
    ])

    result = await handler._handle_cross_prediction(
        params={"parent1": "IR64", "parent2": "Swarna"},
        db=_make_db(),
        organization_id=1,
        germplasm_search_service=germplasm_svc,
    )

    assert "predicted_mean" in result.prediction
    # Mid-parent value: (0.8 + 0.6) / 2 = 0.7
    assert abs(result.prediction["predicted_mean"] - 0.7) < 0.01


# ── Task 4: Selection scenario handler ───────────────────────────────────────

@pytest.mark.asyncio
async def test_selection_scenario_10_percent_on_20_entries_selects_2():
    """10% selection intensity on 20 entries → 2 entries selected."""
    handler = WhatIfQueryHandler()
    # 20 observations for 20 different germplasm entries
    observations = [_obs(float(i), germplasm_id=str(i)) for i in range(1, 21)]
    obs_svc = _make_obs_service(observations)

    result = await handler._handle_selection_scenario(
        params={"selection_intensity": 0.10, "trait": "yield"},
        db=_make_db(),
        organization_id=1,
        observation_search_service=obs_svc,
    )

    assert isinstance(result, WhatIfResult)
    assert result.is_prediction is True
    assert result.prediction["n_selected"] == 2
    assert result.prediction["n_total"] == 20
    assert not result.insufficient_data


@pytest.mark.asyncio
async def test_selection_scenario_includes_expected_gain():
    """Selection scenario includes expected_gain in prediction."""
    handler = WhatIfQueryHandler()
    observations = [_obs(float(i), germplasm_id=str(i)) for i in range(1, 11)]
    obs_svc = _make_obs_service(observations)

    result = await handler._handle_selection_scenario(
        params={"selection_intensity": 0.20, "trait": "yield"},
        db=_make_db(),
        organization_id=1,
        observation_search_service=obs_svc,
    )

    assert "expected_gain" in result.prediction
    assert isinstance(result.prediction["expected_gain"], float)


@pytest.mark.asyncio
async def test_selection_scenario_returns_insufficient_data_when_no_observations():
    """Returns insufficient_data=True when no observations available."""
    handler = WhatIfQueryHandler()
    obs_svc = _make_obs_service([])

    result = await handler._handle_selection_scenario(
        params={"selection_intensity": 0.10, "trait": "yield"},
        db=_make_db(),
        organization_id=1,
        observation_search_service=obs_svc,
    )

    assert result.insufficient_data is True


@pytest.mark.asyncio
async def test_selection_scenario_includes_diversity_impact():
    """Selection scenario includes diversity_impact in prediction."""
    handler = WhatIfQueryHandler()
    observations = [_obs(float(i), germplasm_id=str(i)) for i in range(1, 21)]
    obs_svc = _make_obs_service(observations)

    result = await handler._handle_selection_scenario(
        params={"selection_intensity": 0.25, "trait": "yield"},
        db=_make_db(),
        organization_id=1,
        observation_search_service=obs_svc,
    )

    assert "diversity_impact" in result.prediction
    assert "selection_pressure" in result.prediction["diversity_impact"]


# ── Task 5: Environmental scenario handler ────────────────────────────────────

@pytest.mark.asyncio
async def test_environmental_scenario_returns_result_with_prediction():
    """Environmental scenario returns WhatIfResult with baseline and scenario yield."""
    handler = WhatIfQueryHandler()

    result = await handler._handle_environmental_scenario(
        params={
            "environmental_factor": "rainfall",
            "magnitude": -20.0,
            "crop": "wheat",
            "baseline_yield": 4.5,
        },
        db=_make_db(),
        organization_id=1,
    )

    assert isinstance(result, WhatIfResult)
    assert result.is_prediction is True
    assert "baseline_yield" in result.prediction
    assert "scenario_yield" in result.prediction
    assert "yield_change_percent" in result.prediction
    assert not result.insufficient_data


@pytest.mark.asyncio
async def test_environmental_scenario_rainfall_reduction_lowers_yield():
    """20% rainfall reduction should predict lower yield than baseline."""
    handler = WhatIfQueryHandler()

    result = await handler._handle_environmental_scenario(
        params={
            "environmental_factor": "rainfall",
            "magnitude": -20.0,
            "crop": "wheat",
            "baseline_yield": 4.5,
        },
        db=_make_db(),
        organization_id=1,
    )

    assert result.prediction["scenario_yield"] < result.prediction["baseline_yield"]
    assert result.prediction["yield_change_percent"] < 0


@pytest.mark.asyncio
async def test_environmental_scenario_returns_insufficient_data_without_baseline():
    """Returns insufficient_data=True when no baseline yield is available."""
    handler = WhatIfQueryHandler()

    result = await handler._handle_environmental_scenario(
        params={
            "environmental_factor": "rainfall",
            "magnitude": -20.0,
            "crop": "unknown_crop",
            # no baseline_yield
        },
        db=_make_db(),
        organization_id=1,
    )

    assert result.insufficient_data is True


@pytest.mark.asyncio
async def test_environmental_scenario_includes_assumptions_and_limitations():
    """Environmental scenario always includes assumptions and limitations."""
    handler = WhatIfQueryHandler()

    result = await handler._handle_environmental_scenario(
        params={
            "environmental_factor": "rainfall",
            "magnitude": -15.0,
            "crop": "rice",
            "baseline_yield": 5.0,
        },
        db=_make_db(),
        organization_id=1,
    )

    assert len(result.assumptions) >= 1
    assert len(result.limitations) >= 1


# ── Task 6: handle() dispatch ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_handle_dispatches_to_cross_prediction():
    """handle() with 'cross_prediction' dispatches to _handle_cross_prediction."""
    handler = WhatIfQueryHandler()
    germplasm_svc = _make_germplasm_service([
        {"id": "10", "germplasm_name": "IR64", "gebv": 0.8},
        {"id": "20", "germplasm_name": "Swarna", "gebv": 0.6},
    ])

    result = await handler.handle(
        query_type="cross_prediction",
        params={"parent1": "IR64", "parent2": "Swarna"},
        db=_make_db(),
        organization_id=1,
        germplasm_search_service=germplasm_svc,
        observation_search_service=_make_obs_service(),
    )

    assert result.query_type == "cross_prediction"
    assert result.is_prediction is True


@pytest.mark.asyncio
async def test_handle_dispatches_to_selection_scenario():
    """handle() with 'selection_scenario' dispatches to _handle_selection_scenario."""
    handler = WhatIfQueryHandler()
    observations = [_obs(float(i), germplasm_id=str(i)) for i in range(1, 11)]

    result = await handler.handle(
        query_type="selection_scenario",
        params={"selection_intensity": 0.20, "trait": "yield"},
        db=_make_db(),
        organization_id=1,
        germplasm_search_service=_make_germplasm_service(),
        observation_search_service=_make_obs_service(observations),
    )

    assert result.query_type == "selection_scenario"
    assert result.is_prediction is True


@pytest.mark.asyncio
async def test_handle_returns_insufficient_data_for_unknown_type():
    """handle() with unknown query_type → insufficient_data=True."""
    handler = WhatIfQueryHandler()

    result = await handler.handle(
        query_type="unknown_type",
        params={},
        db=_make_db(),
        organization_id=1,
        germplasm_search_service=_make_germplasm_service(),
        observation_search_service=_make_obs_service(),
    )

    assert result.insufficient_data is True
