"""
TDD tests for REEVU Temporal Reasoning.

Written BEFORE the implementation. RED → GREEN → REFACTOR.

Covers:
- Task 1: TimePoint, TemporalTrendResult, GeneticGainResult dataclasses
- Task 2: _group_observations_by_period() — season/year/cycle grouping
- Task 3: _compute_trend() — linear regression, trend direction
- Task 4: _estimate_genetic_gain() — gain per cycle
- Task 5: compute_temporal_trend() orchestration
- Task 6: TEMPORAL_PATTERNS extension (over last N, since YYYY, between)
- Task 7: _query_suggests_temporal() helper + analytics step wiring
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.modules.ai.services.reevu.analytics_engine import (
    AnalyticsEngine,
    TimePoint,
    TemporalTrendResult,
    GeneticGainResult,
)
from app.modules.ai.services.reevu.step_executor import StepExecutor, DOMAIN_ORDER
from app.modules.ai.services.reevu.step_executor import (
    IntermediateResultContext,
    StepResult,
)
from app.schemas.reevu_plan import PlanStep


# ── Helpers ──────────────────────────────────────────────────────────────────

def _obs(value: float, season: str = "2023", trait: str = "yield", germplasm: str = "G1") -> dict:
    return {
        "observation_variable_name": trait,
        "value": str(value),
        "season": season,
        "germplasm_name": germplasm,
        "germplasm_id": "1",
    }


def _obs_year(value: float, year: int, trait: str = "yield") -> dict:
    return {
        "observation_variable_name": trait,
        "value": str(value),
        "observation_time_stamp": f"{year}-06-15T00:00:00",
        "germplasm_name": "G1",
        "germplasm_id": "1",
    }


def _obs_cycle(value: float, cycle: int, trait: str = "yield") -> dict:
    return {
        "observation_variable_name": trait,
        "value": str(value),
        "cycle": str(cycle),
        "germplasm_name": "G1",
        "germplasm_id": "1",
    }


def _make_executor() -> object:
    from unittest.mock import MagicMock, AsyncMock
    executor = MagicMock()
    executor.db = AsyncMock()
    executor.trial_search_service = None
    executor.germplasm_search_service = None
    executor.observation_search_service = None
    executor.trait_search_service = None
    executor.weather_service = None
    executor.location_search_service = None
    executor.seedlot_search_service = None
    executor.soil_analysis_search_service = None
    executor.disease_resistance_search_service = None
    executor.iot_telemetry_service = None
    executor.spatial_query_service = None
    executor.climate_service = None
    executor.commercial_service = None
    executor.harvest_service = None
    executor.nursery_service = None
    executor.vision_service = None
    return executor


def _make_se(query: str = "test") -> StepExecutor:
    return StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query=query,
        params={},
    )


def _make_step(step_id: str, domain: str, prerequisites: list[str] | None = None) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        domain=domain,
        prerequisites=prerequisites or [],
        description=f"{domain} step",
        expected_outputs=[],
    )


# ── Task 1: Data models ───────────────────────────────────────────────────────

def test_time_point_has_required_fields():
    tp = TimePoint(period="2023", mean=4.5, n=10, ci_lower=4.1, ci_upper=4.9)
    assert tp.period == "2023"
    assert tp.mean == 4.5
    assert tp.n == 10
    assert tp.ci_lower < tp.mean < tp.ci_upper


def test_temporal_trend_result_has_required_fields():
    result = TemporalTrendResult(
        trait_name="yield",
        time_series=[],
        trend_direction="increasing",
        rate_of_change=0.2,
        r_squared=0.85,
        genetic_gain=None,
        evidence_refs=[],
        calculation_steps=[],
    )
    assert result.trait_name == "yield"
    assert result.trend_direction == "increasing"
    assert result.r_squared == 0.85


def test_genetic_gain_result_has_required_fields():
    gg = GeneticGainResult(
        gain_per_cycle=0.15,
        gain_percent_per_cycle=3.5,
        n_cycles=4,
        base_mean=4.0,
        current_mean=4.6,
    )
    assert gg.gain_per_cycle == 0.15
    assert gg.n_cycles == 4


# ── Task 2: Temporal grouping ─────────────────────────────────────────────────

def test_group_by_season_produces_correct_time_points():
    """3 seasons → 3 TimePoints sorted chronologically with correct means."""
    engine = AnalyticsEngine()
    observations = [
        _obs(4.0, "2021"), _obs(4.2, "2021"),
        _obs(4.5, "2022"), _obs(4.7, "2022"),
        _obs(5.0, "2023"), _obs(5.2, "2023"),
    ]

    time_points = engine._group_observations_by_period(observations, "season")

    assert len(time_points) == 3
    assert time_points[0].period == "2021"
    assert time_points[1].period == "2022"
    assert time_points[2].period == "2023"
    assert abs(time_points[0].mean - 4.1) < 0.01
    assert abs(time_points[1].mean - 4.6) < 0.01
    assert abs(time_points[2].mean - 5.1) < 0.01


def test_group_by_year_extracts_year_from_timestamp():
    """Observations with timestamps are grouped by year."""
    engine = AnalyticsEngine()
    observations = [
        _obs_year(4.0, 2021), _obs_year(4.2, 2021),
        _obs_year(4.8, 2022), _obs_year(5.0, 2022),
    ]

    time_points = engine._group_observations_by_period(observations, "year")

    assert len(time_points) == 2
    assert time_points[0].period == "2021"
    assert time_points[1].period == "2022"


def test_group_by_cycle_extracts_cycle_field():
    """Observations with cycle field are grouped by cycle."""
    engine = AnalyticsEngine()
    observations = [
        _obs_cycle(3.8, 1), _obs_cycle(3.9, 1),
        _obs_cycle(4.1, 2), _obs_cycle(4.3, 2),
        _obs_cycle(4.6, 3),
    ]

    time_points = engine._group_observations_by_period(observations, "cycle")

    assert len(time_points) == 3
    assert time_points[0].period == "1"
    assert time_points[2].period == "3"


def test_group_computes_confidence_intervals():
    """TimePoints include 95% CI: mean ± 1.96 * std / sqrt(n)."""
    engine = AnalyticsEngine()
    import math, statistics
    values = [4.0, 4.2, 4.4, 4.6, 4.8]
    observations = [_obs(v, "2023") for v in values]

    time_points = engine._group_observations_by_period(observations, "season")

    assert len(time_points) == 1
    tp = time_points[0]
    mean = statistics.mean(values)
    std = statistics.stdev(values)
    expected_ci = 1.96 * std / math.sqrt(len(values))
    assert abs(tp.ci_lower - (mean - expected_ci)) < 0.01
    assert abs(tp.ci_upper - (mean + expected_ci)) < 0.01


def test_group_returns_empty_when_no_numeric_values():
    """Returns empty list when observations have no parseable numeric values."""
    engine = AnalyticsEngine()
    observations = [{"observation_variable_name": "yield", "value": "N/A", "season": "2023"}]

    time_points = engine._group_observations_by_period(observations, "season")

    assert time_points == []


# ── Task 3: Trend computation ─────────────────────────────────────────────────

def test_compute_trend_returns_slope_intercept_r_squared():
    """_compute_trend returns (slope, intercept, r_squared) for a clear trend."""
    engine = AnalyticsEngine()
    time_points = [
        TimePoint("2021", 4.0, 5, 3.8, 4.2),
        TimePoint("2022", 4.5, 5, 4.3, 4.7),
        TimePoint("2023", 5.0, 5, 4.8, 5.2),
    ]

    slope, intercept, r_squared = engine._compute_trend(time_points)

    assert slope > 0          # increasing trend
    assert 0.0 <= r_squared <= 1.0
    assert abs(r_squared - 1.0) < 0.01  # perfect linear trend


def test_compute_trend_direction_increasing():
    """slope > 5% of base_mean → 'increasing'."""
    engine = AnalyticsEngine()
    # base_mean = 4.0, slope = 0.5 → 0.5 > 0.05 * 4.0 = 0.2 → increasing
    time_points = [
        TimePoint("2021", 4.0, 5, 3.8, 4.2),
        TimePoint("2022", 4.5, 5, 4.3, 4.7),
        TimePoint("2023", 5.0, 5, 4.8, 5.2),
    ]

    direction = engine._trend_direction(time_points)

    assert direction == "increasing"


def test_compute_trend_direction_decreasing():
    """slope < -5% of base_mean → 'decreasing'."""
    engine = AnalyticsEngine()
    time_points = [
        TimePoint("2021", 5.0, 5, 4.8, 5.2),
        TimePoint("2022", 4.5, 5, 4.3, 4.7),
        TimePoint("2023", 4.0, 5, 3.8, 4.2),
    ]

    direction = engine._trend_direction(time_points)

    assert direction == "decreasing"


def test_compute_trend_direction_stable():
    """Small slope relative to base_mean → 'stable'."""
    engine = AnalyticsEngine()
    # base_mean = 4.0, slope ≈ 0.01 → 0.01 < 0.05 * 4.0 = 0.2 → stable
    time_points = [
        TimePoint("2021", 4.00, 5, 3.9, 4.1),
        TimePoint("2022", 4.01, 5, 3.9, 4.1),
        TimePoint("2023", 4.02, 5, 3.9, 4.1),
    ]

    direction = engine._trend_direction(time_points)

    assert direction == "stable"


def test_compute_trend_insufficient_data_when_fewer_than_3_points():
    """Fewer than 3 time points → 'insufficient_data'."""
    engine = AnalyticsEngine()
    time_points = [
        TimePoint("2021", 4.0, 5, 3.8, 4.2),
        TimePoint("2022", 4.5, 5, 4.3, 4.7),
    ]

    direction = engine._trend_direction(time_points)

    assert direction == "insufficient_data"


@given(
    means=st.lists(st.floats(min_value=0.1, max_value=100.0, allow_nan=False), min_size=3, max_size=10),
)
@settings(max_examples=100)
def test_property_trend_direction_matches_slope(means):
    """trend_direction matches slope sign relative to 5% of base_mean threshold."""
    import statistics as _stats
    engine = AnalyticsEngine()
    time_points = [TimePoint(str(i), m, 5, m - 0.1, m + 0.1) for i, m in enumerate(means)]

    direction = engine._trend_direction(time_points)
    slope, _, _ = engine._compute_trend(time_points)
    base_mean = time_points[0].mean
    threshold = 0.05 * base_mean

    if slope > threshold:
        assert direction == "increasing"
    elif slope < -threshold:
        assert direction == "decreasing"
    else:
        assert direction == "stable"


# ── Task 4: Genetic gain estimation ──────────────────────────────────────────

def test_estimate_genetic_gain_correct_formula():
    """5 cycles with known means → correct gain_per_cycle and gain_percent."""
    engine = AnalyticsEngine()
    # base=4.0, current=4.8, n_cycles=4 → gain=0.2/cycle, 5%/cycle
    time_points = [
        TimePoint("1", 4.0, 10, 3.8, 4.2),
        TimePoint("2", 4.2, 10, 4.0, 4.4),
        TimePoint("3", 4.4, 10, 4.2, 4.6),
        TimePoint("4", 4.6, 10, 4.4, 4.8),
        TimePoint("5", 4.8, 10, 4.6, 5.0),
    ]

    gg = engine._estimate_genetic_gain(time_points)

    assert gg is not None
    assert abs(gg.gain_per_cycle - 0.2) < 0.001
    assert abs(gg.gain_percent_per_cycle - 5.0) < 0.01
    assert gg.n_cycles == 4
    assert gg.base_mean == 4.0
    assert gg.current_mean == 4.8


def test_estimate_genetic_gain_returns_none_for_single_point():
    """Returns None when fewer than 2 time points."""
    engine = AnalyticsEngine()
    time_points = [TimePoint("1", 4.0, 10, 3.8, 4.2)]

    assert engine._estimate_genetic_gain(time_points) is None


def test_estimate_genetic_gain_returns_none_for_empty():
    engine = AnalyticsEngine()
    assert engine._estimate_genetic_gain([]) is None


# ── Task 5: compute_temporal_trend() orchestration ───────────────────────────

def test_compute_temporal_trend_returns_temporal_trend_result():
    """compute_temporal_trend returns a TemporalTrendResult."""
    engine = AnalyticsEngine()
    observations = [
        _obs(4.0, "2021"), _obs(4.2, "2021"),
        _obs(4.5, "2022"), _obs(4.7, "2022"),
        _obs(5.0, "2023"), _obs(5.2, "2023"),
    ]

    result = engine.compute_temporal_trend(observations, trait_name="yield", time_field="season")

    assert isinstance(result, TemporalTrendResult)
    assert result.trait_name == "yield"
    assert len(result.time_series) == 3
    assert result.trend_direction in ("increasing", "decreasing", "stable", "insufficient_data")


def test_compute_temporal_trend_filters_by_trait():
    """Only observations matching trait_name are included."""
    engine = AnalyticsEngine()
    observations = [
        _obs(4.0, "2021", trait="yield"),
        _obs(4.5, "2022", trait="yield"),
        _obs(5.0, "2023", trait="yield"),
        {"observation_variable_name": "height", "value": "90", "season": "2021"},
        {"observation_variable_name": "height", "value": "95", "season": "2022"},
    ]

    result = engine.compute_temporal_trend(observations, trait_name="yield", time_field="season")

    assert len(result.time_series) == 3  # only yield observations


def test_compute_temporal_trend_includes_genetic_gain_when_requested():
    """When query mentions 'genetic gain', GeneticGainResult is included."""
    engine = AnalyticsEngine()
    observations = [
        _obs_cycle(4.0, 1), _obs_cycle(4.2, 1),
        _obs_cycle(4.4, 2), _obs_cycle(4.6, 2),
        _obs_cycle(4.8, 3), _obs_cycle(5.0, 3),
    ]

    result = engine.compute_temporal_trend(
        observations, trait_name="yield", time_field="cycle",
        compute_genetic_gain=True,
    )

    assert result.genetic_gain is not None
    assert result.genetic_gain.n_cycles == 2


def test_compute_temporal_trend_safe_failure_when_no_temporal_data():
    """Returns TemporalTrendResult with insufficient_data when no grouping possible."""
    engine = AnalyticsEngine()
    # Observations with no season/year/cycle field
    observations = [
        {"observation_variable_name": "yield", "value": "4.0"},
        {"observation_variable_name": "yield", "value": "4.5"},
    ]

    result = engine.compute_temporal_trend(observations, trait_name="yield", time_field="season")

    assert result.trend_direction == "insufficient_data"
    assert result.time_series == []


def test_compute_temporal_trend_includes_evidence_refs():
    """TemporalTrendResult includes at least one evidence_ref."""
    engine = AnalyticsEngine()
    observations = [
        _obs(4.0, "2021"), _obs(4.5, "2022"), _obs(5.0, "2023"),
    ]

    result = engine.compute_temporal_trend(observations, trait_name="yield", time_field="season")

    assert len(result.evidence_refs) >= 1


# ── Task 6: TEMPORAL_PATTERNS extension ──────────────────────────────────────

def test_temporal_patterns_detect_over_last_n_years():
    """'over the last N years' is detected and returns temporal_range."""
    import re
    from app.modules.ai.services.reevu.synonym_config import TEMPORAL_PATTERNS

    pattern_map = dict(TEMPORAL_PATTERNS)
    test_cases = [
        "how has yield changed over the last 3 years?",
        "show me data over the last 5 seasons",
        "trend over the last 2 cycles",
    ]
    for msg in test_cases:
        matched = False
        for pattern, _ in TEMPORAL_PATTERNS:
            if re.search(pattern, msg, re.IGNORECASE):
                matched = True
                break
        assert matched, f"No pattern matched: '{msg}'"


def test_temporal_patterns_detect_since_year():
    """'since YYYY' is detected."""
    import re
    from app.modules.ai.services.reevu.synonym_config import TEMPORAL_PATTERNS

    msg = "show yield trend since 2020"
    matched = any(re.search(p, msg, re.IGNORECASE) for p, _ in TEMPORAL_PATTERNS)
    assert matched, "Expected 'since YYYY' to be detected"


def test_temporal_patterns_detect_between_years():
    """'between YYYY and YYYY' is detected."""
    import re
    from app.modules.ai.services.reevu.synonym_config import TEMPORAL_PATTERNS

    msg = "show yield data between 2022 and 2025"
    matched = any(re.search(p, msg, re.IGNORECASE) for p, _ in TEMPORAL_PATTERNS)
    assert matched, "Expected 'between YYYY and YYYY' to be detected"


# ── Task 7: _query_suggests_temporal() + analytics step wiring ───────────────

def test_query_suggests_temporal_returns_true_for_trend_queries():
    """_query_suggests_temporal() returns True for temporal queries."""
    temporal_queries = [
        "how has yield changed over time?",
        "show the trend in plant height over the last 3 seasons",
        "what is the genetic gain in our wheat program?",
        "has yield improved over the last 5 years?",
        "breeding progress for rice",
        "changed over the last 2 cycles",
    ]
    for query in temporal_queries:
        se = _make_se(query)
        assert se._query_suggests_temporal(), f"Expected True for: '{query}'"


def test_query_suggests_temporal_returns_false_for_non_temporal():
    """_query_suggests_temporal() returns False for non-temporal queries."""
    non_temporal = [
        "show me trial results for wheat",
        "which variety has the highest yield?",
        "list all germplasm in program P1",
    ]
    for query in non_temporal:
        se = _make_se(query)
        assert not se._query_suggests_temporal(), f"Expected False for: '{query}'"


@pytest.mark.asyncio
async def test_analytics_step_includes_temporal_trend_for_temporal_query():
    """When query suggests temporal, analytics step includes temporal_trend in records."""
    from unittest.mock import AsyncMock, MagicMock

    mock_obs_service = AsyncMock()
    mock_obs_service.search = AsyncMock(return_value=[
        _obs(4.0, "2021"), _obs(4.2, "2021"),
        _obs(4.5, "2022"), _obs(4.7, "2022"),
        _obs(5.0, "2023"), _obs(5.2, "2023"),
    ])

    executor = _make_executor()
    executor.observation_search_service = mock_obs_service

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="how has yield changed over the last 3 seasons?",
        params={"trait": "yield"},
    )

    # Build a context with a phenotyping step that has observations
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="pheno-1",
        domain="phenotyping",
        status="success",
        records={"observations": [
            _obs(4.0, "2021"), _obs(4.2, "2021"),
            _obs(4.5, "2022"), _obs(4.7, "2022"),
            _obs(5.0, "2023"), _obs(5.2, "2023"),
        ]},
        entity_ids=["trait-1"],
    ))

    step = _make_step("analytics-1", "analytics", prerequisites=["pheno-1"])
    result = await se._execute_analytics_step(step, ctx)

    assert result.status == "success"
    assert "temporal_trend" in result.records
    temporal = result.records["temporal_trend"]
    assert isinstance(temporal, dict) or hasattr(temporal, "trend_direction")
