"""Unit tests for the REEVU StepExecutor."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.ai.services.reevu.step_executor import (
    DOMAIN_ORDER,
    ExecutionOutcome,
    IntermediateResultContext,
    StepExecutor,
    StepResult,
)
from app.modules.ai.services.reevu.planner import ReevuPlanner
from app.modules.ai.services.tool_cross_domain_handlers import (
    _assemble_results_from_outcome,
)
from app.schemas.reevu_envelope import EvidenceRef
from app.schemas.reevu_plan import PlanStep, ReevuExecutionPlan


# ── Helpers ──────────────────────────────────────────────────────────


def _make_plan(steps: list[PlanStep], query: str = "test query") -> ReevuExecutionPlan:
    return ReevuExecutionPlan(
        plan_id="test-plan",
        original_query=query,
        is_compound=len(steps) > 1,
        steps=steps,
        domains_involved=list(dict.fromkeys(s.domain for s in steps)),
    )


def _make_step(
    step_id: str, domain: str, prerequisites: list[str] | None = None
) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        domain=domain,
        description=f"Test {domain} step",
        prerequisites=prerequisites or [],
        expected_outputs=[f"{domain}_data"],
    )


def _observation(
    value: str | float,
    *,
    observation_id: str = "obs-1",
    study_id: str = "101",
    study_name: str = "Study A",
    trait_id: str = "11",
    trait_name: str = "Plant height",
    germplasm_id: str = "201",
) -> dict[str, object]:
    return {
        "id": observation_id,
        "observation_db_id": observation_id,
        "value": value,
        "trait": {"id": trait_id, "name": trait_name, "trait_name": trait_name},
        "study": {"id": study_id, "name": study_name},
        "germplasm": {"id": germplasm_id, "name": f"G{germplasm_id}"},
    }


def _make_executor():
    """Create a mock FunctionExecutor with all services as AsyncMock."""
    executor = MagicMock()
    executor.db = AsyncMock()
    executor.trial_search_service = AsyncMock()
    executor.trial_search_service.search = AsyncMock(return_value=[])
    executor.trial_search_service.get_by_id = AsyncMock(return_value=None)
    executor.germplasm_search_service = AsyncMock()
    executor.germplasm_search_service.search = AsyncMock(return_value=[])
    executor.location_search_service = AsyncMock()
    executor.location_search_service.search = AsyncMock(return_value=[])
    executor.weather_service = AsyncMock()
    executor.weather_service.get_forecast = AsyncMock(
        return_value=MagicMock(alerts=[], impacts=[])
    )
    executor.weather_service.get_veena_summary = MagicMock(
        return_value="Weather summary"
    )
    executor.breeding_value_service = AsyncMock()
    executor.protocol_search_service = AsyncMock()
    executor.protocol_search_service.get_protocols = AsyncMock(return_value=[])
    executor.observation_search_service = AsyncMock()
    executor.observation_search_service.search = AsyncMock(return_value=[])
    executor.trait_search_service = AsyncMock()
    executor.trait_search_service.search = AsyncMock(return_value=[])
    executor.seedlot_search_service = AsyncMock()
    executor.seedlot_search_service.search = AsyncMock(return_value=[])
    executor.crop_calendar_service = AsyncMock()
    executor.crop_calendar_service.search = AsyncMock(return_value=[])
    return executor


# ── Tests ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_single_step_plan():
    """A plan with one trials step should complete with 1 success, 0 failures."""
    executor = _make_executor()
    executor.trial_search_service.search = AsyncMock(
        return_value=[{"id": 1, "name": "Trial A"}, {"id": 2, "name": "Trial B"}]
    )

    step = _make_step("step-1", "trials")
    plan = _make_plan([step])

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )
    outcome = await se.execute_plan(plan)

    assert outcome.steps_completed == 1
    assert outcome.steps_failed == 0
    assert outcome.budget_exhausted is False
    assert len(outcome.step_results) == 1
    assert outcome.step_results[0].status == "success"


@pytest.mark.asyncio
async def test_multi_step_dependency_ordering():
    """Steps with prerequisites execute after their dependencies."""
    executor = _make_executor()
    executor.trial_search_service.search = AsyncMock(
        return_value=[{"id": 1, "name": "Trial A"}]
    )

    step_trials = _make_step("step-1", "trials")
    step_breeding = _make_step("step-2", "breeding", prerequisites=["step-1"])
    step_analytics = _make_step("step-3", "analytics", prerequisites=["step-2"])

    plan = _make_plan([step_analytics, step_breeding, step_trials])

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )
    outcome = await se.execute_plan(plan)

    executed_ids = [r.step_id for r in outcome.step_results]
    assert executed_ids == ["step-1", "step-2", "step-3"]


@pytest.mark.asyncio
async def test_independent_steps_follow_domain_order():
    """Independent steps are ordered by DOMAIN_ORDER (trials=1 < breeding=3)."""
    executor = _make_executor()
    executor.trial_search_service.search = AsyncMock(
        return_value=[{"id": 1, "name": "Trial A"}]
    )

    step_breeding = _make_step("step-b", "breeding")
    step_trials = _make_step("step-t", "trials")

    # Pass breeding first to verify reordering
    plan = _make_plan([step_breeding, step_trials])

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )
    outcome = await se.execute_plan(plan)

    executed_ids = [r.step_id for r in outcome.step_results]
    # trials (DOMAIN_ORDER=1) should execute before breeding (DOMAIN_ORDER=3)
    assert executed_ids.index("step-t") < executed_ids.index("step-b")


@pytest.mark.asyncio
async def test_prerequisite_failure_cascading():
    """When a prerequisite fails, dependent steps are skipped."""
    executor = _make_executor()
    executor.trial_search_service.search = AsyncMock(
        side_effect=RuntimeError("DB connection lost")
    )

    step_trials = _make_step("step-1", "trials")
    step_breeding = _make_step("step-2", "breeding", prerequisites=["step-1"])

    plan = _make_plan([step_trials, step_breeding])

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )
    outcome = await se.execute_plan(plan)

    trials_result = outcome.step_results[0]
    breeding_result = outcome.step_results[1]

    assert trials_result.status == "failed"
    assert breeding_result.status == "skipped"
    assert breeding_result.metadata["skipped_prerequisite"] == "step-1"


@pytest.mark.asyncio
async def test_step_count_limit():
    """Plans exceeding MAX_STEPS are refused with budget_exhausted=True."""
    executor = _make_executor()

    steps = [_make_step(f"step-{i}", "trials") for i in range(11)]
    plan = _make_plan(steps)

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )
    outcome = await se.execute_plan(plan)

    assert outcome.budget_exhausted is True
    assert outcome.steps_completed == 0
    assert len(outcome.step_results) == 0


@pytest.mark.asyncio
async def test_per_step_timeout():
    """A step that exceeds MAX_STEP_SECONDS is marked as timed_out."""
    executor = _make_executor()

    async def slow_search(**kwargs):
        await asyncio.sleep(1)
        return []

    executor.trial_search_service.search = slow_search

    step = _make_step("step-1", "trials")
    plan = _make_plan([step])

    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )

    with patch.object(StepExecutor, "MAX_STEP_SECONDS", 0.01):
        outcome = await se.execute_plan(plan)

    assert len(outcome.step_results) == 1
    assert outcome.step_results[0].status == "timed_out"


def test_context_round_trip():
    """IntermediateResultContext stores and retrieves StepResults correctly."""
    ctx = IntermediateResultContext()

    result = StepResult(
        step_id="step-1",
        domain="trials",
        status="success",
        records={"trials": [{"id": 1}]},
        entity_ids=["1", "2"],
        evidence_refs=[
            EvidenceRef(
                source_type="database",
                entity_id="step:step-1:trial_search",
                query_or_method="trial_search_service.search",
            )
        ],
        duration_ms=42.0,
    )
    ctx.add(result)

    retrieved = ctx.get("step-1")
    assert retrieved is not None
    assert retrieved.step_id == "step-1"
    assert retrieved.domain == "trials"
    assert retrieved.status == "success"
    assert retrieved.records == {"trials": [{"id": 1}]}
    assert retrieved.entity_ids == ["1", "2"]
    assert len(retrieved.evidence_refs) == 1
    assert retrieved.duration_ms == 42.0

    # get_entity_ids returns IDs for successful steps
    assert ctx.get_entity_ids("step-1") == ["1", "2"]

    # get_entity_ids returns empty list for missing step
    assert ctx.get_entity_ids("nonexistent") == []

    # get_entity_ids returns empty list for failed step
    failed = StepResult(
        step_id="step-fail",
        domain="weather",
        status="failed",
        error_category="execution_error",
        error_message="boom",
    )
    ctx.add(failed)
    assert ctx.get_entity_ids("step-fail") == []


def test_narrowing_from_trials():
    """_narrow_from_trials extracts trial_ids and location_query."""
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="step-1",
            domain="trials",
            status="success",
            entity_ids=["1", "2"],
            metadata={"inferred_location_query": "IRRI"},
        )
    )

    narrowing = se._narrow_from_trials(ctx, "step-1")

    assert narrowing["trial_ids"] == ["1", "2"]
    assert narrowing["location_query"] == "IRRI"


def test_narrowing_from_breeding():
    """_narrow_from_breeding extracts germplasm_ids and trait_names."""
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="step-1",
            domain="breeding",
            status="success",
            entity_ids=["10", "20"],
            records={"traits": [{"name": "Yield"}]},
        )
    )

    narrowing = se._narrow_from_breeding(ctx, "step-1")

    assert narrowing["germplasm_ids"] == ["10", "20"]
    assert narrowing["trait_names"] == ["Yield"]


def test_phenotyping_handler_and_domain_order_registered():
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show plant height observations",
        params={},
    )

    assert "phenotyping" in se._domain_handlers
    assert DOMAIN_ORDER["trials"] < DOMAIN_ORDER["phenotyping"] < DOMAIN_ORDER["breeding"]


def test_field_handler_and_domain_order_registered():
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show field locations",
        params={},
    )

    assert "field" in se._domain_handlers
    assert DOMAIN_ORDER["trials"] < DOMAIN_ORDER["field"] < DOMAIN_ORDER["phenotyping"]


def test_planner_registers_field_domain_and_dependencies():
    planner = ReevuPlanner()

    field_plan = planner.build_plan("show field layout and crop calendar for Ludhiana")
    assert "field" in [step.domain for step in field_plan.steps]

    compound_plan = planner.build_plan("show trial locations and weather for those fields")
    steps_by_domain = {step.domain: step for step in compound_plan.steps}
    assert {"trials", "field", "weather"}.issubset(steps_by_domain)
    assert steps_by_domain["trials"].step_id in steps_by_domain["field"].prerequisites
    assert steps_by_domain["field"].step_id in steps_by_domain["weather"].prerequisites


def test_narrowing_from_field():
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )

    location = {"id": "loc-1", "name": "Ludhiana", "latitude": 30.9, "longitude": 75.8}
    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="field-1",
            domain="field",
            status="success",
            records={"locations": [location]},
            entity_ids=["loc-1"],
        )
    )

    narrowing = se._narrow_from_field(ctx, "field-1")

    assert narrowing["location_records"] == [location]


def test_trait_distribution_empty_returns_none():
    assert StepExecutor._compute_trait_distribution([]) is None


def test_trait_distribution_single_value_returns_safe_result():
    distribution = StepExecutor._compute_trait_distribution([5.0])

    assert distribution is not None
    assert distribution["n"] == 1
    assert distribution["quartiles"] == {"q1": 5.0, "median": 5.0, "q3": 5.0}
    assert sum(distribution["bin_counts"]) == 1


def test_trait_distribution_bins_cover_values():
    distribution = StepExecutor._compute_trait_distribution([float(value) for value in range(20)])

    assert distribution is not None
    assert len(distribution["bin_edges"]) == 11
    assert sum(distribution["bin_counts"]) == 20


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([1.0, 2.0, 10.0], "right"),
        ([1.0, 9.0, 10.0], "left"),
        ([1.0, 2.0, 3.0], "symmetric"),
    ],
)
def test_trait_distribution_skewness_indicator(values, expected):
    distribution = StepExecutor._compute_trait_distribution(values)

    assert distribution is not None
    assert distribution["skewness_indicator"] == expected


def test_narrowing_from_phenotyping():
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="test query",
        params={},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="step-1",
            domain="phenotyping",
            status="success",
            entity_ids=["11", "12"],
            records={"observations": [_observation(10.0)]},
            metadata={"resolved_study_ids": ["101"]},
        )
    )

    narrowing = se._narrow_from_phenotyping(ctx, "step-1")

    assert narrowing["trait_ids"] == ["11", "12"]
    assert narrowing["phenotyping_observations"] == [_observation(10.0)]
    assert narrowing["study_ids"] == ["101"]


@pytest.mark.asyncio
async def test_phenotyping_step_missing_observation_service_safe_fails():
    executor = _make_executor()
    executor.observation_search_service = None
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show observations",
        params={"trait": "Yield"},
    )

    result = await se._execute_phenotyping_step(
        _make_step("phenotyping-1", "phenotyping"),
        IntermediateResultContext(),
    )

    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_phenotyping_step_empty_results_is_success():
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show observations for Yield",
        params={"trait": "Yield"},
    )

    result = await se._execute_phenotyping_step(
        _make_step("phenotyping-1", "phenotyping"),
        IntermediateResultContext(),
    )

    assert result.status == "success"
    assert result.records["observation_count"] == 0
    assert result.records["observations"] == []
    assert result.metadata["query_mode"] == "trait_first"


@pytest.mark.asyncio
async def test_phenotyping_step_trait_first_query_returns_observations_and_distribution():
    executor = _make_executor()
    executor.observation_search_service.search = AsyncMock(
        return_value=[
            _observation(10.0, observation_id="obs-1", study_id="101"),
            _observation(20.0, observation_id="obs-2", study_id="102"),
            _observation("bad", observation_id="obs-3", study_id="102"),
        ]
    )
    executor.trait_search_service.search = AsyncMock(
        return_value=[{"id": "11", "name": "Plant height"}]
    )
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="what is the distribution of plant height observations?",
        params={"trait": "Plant height"},
    )

    result = await se._execute_phenotyping_step(
        _make_step("phenotyping-1", "phenotyping"),
        IntermediateResultContext(),
    )

    assert result.status == "success"
    assert result.entity_ids == ["11"]
    assert result.records["observation_count"] == 3
    assert result.records["summary_stats"]["overall"]["mean"] == 15.0
    assert result.records["summary_stats"]["dropped_non_numeric_count"] == 1
    assert result.records["distribution"]["n"] == 2
    assert result.metadata["query_mode"] == "trait_first"
    executor.observation_search_service.search.assert_awaited_once()
    executor.trait_search_service.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_phenotyping_step_uses_trial_study_narrowing():
    executor = _make_executor()

    async def search(**kwargs):
        return [
            _observation(
                kwargs["study_id"],
                observation_id=f"obs-{kwargs['study_id']}",
                study_id=str(kwargs["study_id"]),
            )
        ]

    executor.observation_search_service.search = AsyncMock(side_effect=search)
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show plant height observations from trials",
        params={"trait": "Plant height"},
    )
    context = IntermediateResultContext()
    context.add(
        StepResult(
            step_id="trials-1",
            domain="trials",
            status="success",
            entity_ids=["1"],
            metadata={"resolved_study_ids": ["101", "102"]},
        )
    )

    result = await se._execute_phenotyping_step(
        _make_step("phenotyping-1", "phenotyping", prerequisites=["trials-1"]),
        context,
    )

    assert result.status == "success"
    assert result.metadata["narrowing_applied"] is True
    assert result.metadata["narrowing_source"] == "trials"
    assert result.metadata["resolved_study_ids"] == ["101", "102"]
    assert result.metadata["query_mode"] == "study_scoped"
    assert result.records["observation_count"] == 2


@pytest.mark.asyncio
async def test_field_step_missing_location_service_safe_fails_without_narrowing():
    executor = _make_executor()
    executor.location_search_service = None
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show field details",
        params={},
    )

    result = await se._execute_field_step(
        _make_step("field-1", "field"),
        IntermediateResultContext(),
    )

    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_field_step_uses_trial_location_narrowing_without_requery():
    executor = _make_executor()
    narrowed_location = {
        "id": "loc-1",
        "name": "Ludhiana",
        "latitude": 30.9,
        "longitude": 75.8,
        "field_layouts": [{"plots": 12}],
    }
    executor.crop_calendar_service.search = AsyncMock(
        return_value=[
            {
                "event_type": "planting",
                "crop": "wheat",
                "location_id": "loc-1",
                "planned_date": "2026-11-15",
                "season": "rabi",
            }
        ]
    )
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show field crop calendar for wheat",
        params={"crop": "wheat", "season": "rabi"},
    )
    context = IntermediateResultContext()
    context.add(
        StepResult(
            step_id="trials-1",
            domain="trials",
            status="success",
            records={"locations": [narrowed_location]},
        )
    )

    result = await se._execute_field_step(
        _make_step("field-1", "field", prerequisites=["trials-1"]),
        context,
    )

    assert result.status == "success"
    assert result.metadata["narrowing_applied"] is True
    assert result.metadata["narrowing_source"] == "trials"
    assert result.metadata["query_mode"] == "trials_narrowed"
    assert result.records["locations"] == [narrowed_location]
    assert result.records["field_layouts"] == [{"plots": 12, "location_id": "loc-1"}]
    assert result.records["crop_calendar_events"][0]["event_type"] == "planting"
    executor.location_search_service.search.assert_not_awaited()


@pytest.mark.asyncio
async def test_weather_step_uses_field_coordinates_from_narrowing():
    executor = _make_executor()
    field_location = {
        "id": "loc-1",
        "name": "Ludhiana",
        "latitude": 30.9,
        "longitude": 75.8,
    }
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="weather for field",
        params={},
    )
    context = IntermediateResultContext()
    context.add(
        StepResult(
            step_id="field-1",
            domain="field",
            status="success",
            records={"locations": [field_location]},
        )
    )

    result = await se._execute_weather_step(
        _make_step("weather-1", "weather", prerequisites=["field-1"]),
        context,
    )

    assert result.status == "success"
    executor.weather_service.get_forecast.assert_awaited_once()
    call_kwargs = executor.weather_service.get_forecast.await_args.kwargs
    assert call_kwargs["lat"] == 30.9
    assert call_kwargs["lon"] == 75.8
    executor.location_search_service.search.assert_not_awaited()


def _seedlot(
    seedlot_id: str,
    quantity: float,
    *,
    germplasm_id: str = "10",
    germplasm_name: str = "IR64",
) -> dict[str, object]:
    return {
        "id": seedlot_id,
        "seedlot_db_id": seedlot_id,
        "name": f"Seedlot {seedlot_id}",
        "count": quantity,
        "units": "grams",
        "storage_location": "Vault A",
        "germplasm": {"id": germplasm_id, "name": germplasm_name},
    }


@pytest.mark.asyncio
async def test_seed_ops_step_missing_service_safe_fails():
    executor = _make_executor()
    executor.seedlot_search_service = None
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show seed inventory",
        params={},
    )

    result = await se._execute_seed_ops_step(
        _make_step("seed-1", "seed_ops"),
        IntermediateResultContext(),
    )

    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_seed_ops_step_uses_breeding_narrowing_and_inventory_summary():
    executor = _make_executor()

    async def search(**kwargs):
        assert kwargs["germplasm_id"] in {10, 20}
        return [_seedlot(f"SL-{kwargs['germplasm_id']}", 80 if kwargs["germplasm_id"] == 10 else 250)]

    executor.seedlot_search_service.search = AsyncMock(side_effect=search)
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show seed inventory for selected germplasm",
        params={},
    )
    context = IntermediateResultContext()
    context.add(
        StepResult(
            step_id="breeding-1",
            domain="breeding",
            status="success",
            entity_ids=["10", "20"],
        )
    )

    result = await se._execute_seed_ops_step(
        _make_step("seed-1", "seed_ops", prerequisites=["breeding-1"]),
        context,
    )

    assert result.status == "success"
    assert result.metadata["narrowing_applied"] is True
    assert result.metadata["narrowing_source"] == "breeding"
    assert result.records["inventory_summary"]["total_lots"] == 2
    assert result.records["inventory_summary"]["total_quantity_grams"] == 330
    assert result.records["inventory_summary"]["low_stock_entries"] == ["IR64"]
    assert result.entity_ids == ["SL-10", "SL-20"]


@pytest.mark.asyncio
async def test_seed_ops_step_query_mode_without_narrowing():
    executor = _make_executor()
    executor.seedlot_search_service.search = AsyncMock(return_value=[_seedlot("SL-1", 120)])
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show seed inventory",
        params={"query": "IR64 seed inventory"},
    )

    result = await se._execute_seed_ops_step(
        _make_step("seed-1", "seed_ops"),
        IntermediateResultContext(),
    )

    assert result.status == "success"
    assert result.metadata["query_mode"] == "query"
    assert result.records["inventory_summary"]["low_stock_entries"] == []
    executor.seedlot_search_service.search.assert_awaited_once()


def test_assemble_results_from_outcome():
    """_assemble_results_from_outcome maps step results to the flat dict shape."""
    trials_result = StepResult(
        step_id="step-1",
        domain="trials",
        status="success",
        records={
            "trials": [{"id": 1, "name": "Trial A"}],
            "locations": [{"id": 10, "name": "IRRI"}],
        },
        entity_ids=["1"],
    )
    weather_result = StepResult(
        step_id="step-2",
        domain="weather",
        status="success",
        records={"weather": {"location": "IRRI", "summary": "Sunny"}},
        entity_ids=[],
    )
    breeding_result = StepResult(
        step_id="step-3",
        domain="breeding",
        status="success",
        records={
            "germplasm": [{"id": 100, "name": "IR64"}],
            "observations": [{"id": 200}],
            "traits": [{"name": "Yield"}],
            "seedlots": [],
        },
        entity_ids=["100"],
    )

    outcome = ExecutionOutcome(
        step_results=[trials_result, weather_result, breeding_result],
        evidence_refs=[],
        total_duration_ms=100.0,
        steps_completed=3,
        steps_failed=0,
        steps_skipped=0,
        steps_timed_out=0,
        budget_exhausted=False,
    )

    results = _assemble_results_from_outcome(outcome)

    assert results["trials"] == [{"id": 1, "name": "Trial A"}]
    assert results["locations"] == [{"id": 10, "name": "IRRI"}]
    assert results["weather"] == {"location": "IRRI", "summary": "Sunny"}
    assert results["germplasm"] == [{"id": 100, "name": "IR64"}]
    assert results["observations"] == [{"id": 200}]
    assert results["traits"] == [{"name": "Yield"}]
    assert results["seedlots"] == []


@pytest.mark.asyncio
async def test_analytics_step_computes_statistics_from_context():
    """Analytics step returns real deterministic statistics from prior observations."""
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="Compare and rank Yield performance for Trial A",
        params={"trait": "Yield"},
    )
    context = IntermediateResultContext()
    context.add(
        StepResult(
            step_id="trials-1",
            domain="trials",
            status="success",
            records={
                "trials": [{"id": 1, "name": "Trial A"}],
                "observations": [
                    {
                        "value": value,
                        "germplasm_id": germplasm_id,
                        "germplasm_name": germplasm_id,
                        "trait_name": "Yield",
                        "observation_db_id": f"{germplasm_id}-{value}",
                    }
                    for germplasm_id, values in {
                        "G1": [4.0, 4.2, 4.4],
                        "G2": [5.0, 5.2, 5.4],
                    }.items()
                    for value in values
                ],
            },
        )
    )
    context.add(
        StepResult(
            step_id="breeding-1",
            domain="breeding",
            status="success",
            records={
                "observations": [
                    {
                        "value": value,
                        "germplasm_id": "G3",
                        "germplasm_name": "G3",
                        "trait_name": "Yield",
                        "observation_db_id": f"G3-{value}",
                    }
                    for value in [3.0, 3.2, 3.4]
                ],
            },
        )
    )
    context.add(
        StepResult(
            step_id="failed-1",
            domain="breeding",
            status="failed",
            records={
                "observations": [
                    {
                        "value": value,
                        "germplasm_id": "G9",
                        "germplasm_name": "G9",
                        "trait_name": "Yield",
                        "observation_db_id": f"G9-{value}",
                    }
                    for value in [9.0, 9.2, 9.4]
                ],
            },
        )
    )

    result = await se._execute_analytics_step(_make_step("analytics-1", "analytics"), context)

    assert result.status == "success"
    assert result.metadata["observations_count"] == 9
    assert result.metadata["computation_modes"] == [
        "descriptive_stats",
        "ranking",
        "comparison",
        "trial_summary",
    ]
    assert result.records["descriptive_stats"]["traits"][0]["trait_name"] == "Yield"
    assert result.records["ranking"]["entries"][0]["germplasm_id"] == "G2"
    assert result.records["comparison"]["comparison"]["test_type"] == "anova"
    assert result.records["comparison"]["included_group_ids"] == ["G1", "G2", "G3"]
    assert result.records["trial_summary"]["trial_summary"]["trial_name"] == "Trial A"
    assert result.records["calculation_steps"]
    assert result.evidence_refs


@pytest.mark.asyncio
async def test_analytics_step_empty_context_returns_safe_failure_success():
    """Analytics safe-fails as a successful step when no observations exist."""
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="rank Yield performance",
        params={"trait": "Yield"},
    )

    result = await se._execute_analytics_step(
        _make_step("analytics-1", "analytics"),
        IntermediateResultContext(),
    )

    assert result.status == "success"
    assert result.metadata["observations_count"] == 0
    assert result.metadata["computation_modes"] == []
    assert result.records["safe_failures"]["descriptive_stats"]["reason"] == (
        "insufficient_observations"
    )
    assert result.records["insights"][0]["type"] == "insufficient_data"
    assert result.evidence_refs[0].query_or_method == "analytics_engine.safe_failure"


@pytest.mark.asyncio
async def test_analytics_step_consumes_phenotyping_prerequisite_observations():
    executor = _make_executor()
    se = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="summarize plant height",
        params={"trait": "Plant height"},
    )
    context = IntermediateResultContext()
    context.add(
        StepResult(
            step_id="phenotyping-1",
            domain="phenotyping",
            status="success",
            records={
                "observations": [
                    _observation(10.0, observation_id="obs-1", germplasm_id="201"),
                    _observation(12.0, observation_id="obs-2", germplasm_id="201"),
                    _observation(14.0, observation_id="obs-3", germplasm_id="201"),
                ]
            },
            entity_ids=["11"],
        )
    )

    result = await se._execute_analytics_step(
        _make_step("analytics-1", "analytics", prerequisites=["phenotyping-1"]),
        context,
    )

    assert result.status == "success"
    assert result.metadata["used_phenotyping_observations"] is True
    assert result.metadata["observations_count"] == 3
    assert result.records["descriptive_stats"]["traits"][0]["trait_name"] == "Plant height"


def test_analytics_query_intent_helpers():
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="Which entries are top performers versus the control?",
        params={"group_ids": "G1, G2"},
    )
    context = IntermediateResultContext()
    context.add(StepResult(step_id="trials-1", domain="trials", status="success"))

    assert se._query_suggests_ranking() is True
    assert se._query_suggests_comparison() is True
    assert se._ranking_direction() == "desc"
    assert se._analytics_group_ids() == ["G1", "G2"]
    assert se._has_trial_data(context) is True


# ── Cross-Domain Narrowing: weather and seed_ops extractors ──────────────────

def test_narrowing_from_weather_extracts_weather_data():
    """_narrow_from_weather extracts weather_data, weather_location, and weather_alerts."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="test",
        params={},
    )

    weather_payload = {
        "location": "Ludhiana",
        "source": "live_provider",
        "summary": {"temp_max": 35, "rainfall_mm": 12},
        "alerts": ["heat stress advisory"],
        "impacts_count": 1,
    }
    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="weather-1",
            domain="weather",
            status="success",
            records={"weather": weather_payload},
        )
    )

    narrowing = se._narrow_from_weather(ctx, "weather-1")

    assert narrowing["weather_data"] == weather_payload
    assert narrowing["weather_location"] == "Ludhiana"
    assert narrowing["weather_alerts"] == ["heat stress advisory"]


def test_narrowing_from_weather_returns_empty_on_failed_step():
    """_narrow_from_weather returns {} when the prerequisite step failed."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="test",
        params={},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="weather-1",
            domain="weather",
            status="failed",
            error_category="weather_resolution_error",
        )
    )

    assert se._narrow_from_weather(ctx, "weather-1") == {}


def test_narrowing_from_weather_returns_empty_when_no_weather_record():
    """_narrow_from_weather returns {} when the step has no weather record."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="test",
        params={},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="weather-1",
            domain="weather",
            status="success",
            records={},  # no "weather" key
        )
    )

    assert se._narrow_from_weather(ctx, "weather-1") == {}


def test_narrowing_from_seed_ops_extracts_available_germplasm_ids():
    """_narrow_from_seed_ops returns germplasm IDs for seedlots with quantity > 0."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="test",
        params={},
    )

    seedlots = [
        {"id": "SL-1", "germplasm_id": 10, "quantity_grams": 500},
        {"id": "SL-2", "germplasm_id": 20, "quantity_grams": 0},    # out of stock
        {"id": "SL-3", "germplasm_id": 30, "quantity_grams": 200},
        {"id": "SL-4", "germplasm_id": 10, "quantity_grams": 100},  # duplicate germplasm
    ]
    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="seed-1",
            domain="seed_ops",
            status="success",
            records={"seedlots": seedlots},
        )
    )

    narrowing = se._narrow_from_seed_ops(ctx, "seed-1")

    # germplasm 20 is out of stock; germplasm 10 appears twice but deduped
    assert set(narrowing["available_germplasm_ids"]) == {10, 30}
    assert narrowing["available_germplasm_ids"].count(10) == 1  # deduped


def test_narrowing_from_seed_ops_returns_empty_when_all_out_of_stock():
    """_narrow_from_seed_ops returns {} when no seedlots have quantity > 0."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="test",
        params={},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="seed-1",
            domain="seed_ops",
            status="success",
            records={"seedlots": [{"id": "SL-1", "germplasm_id": 5, "quantity_grams": 0}]},
        )
    )

    assert se._narrow_from_seed_ops(ctx, "seed-1") == {}


def test_narrowing_from_seed_ops_returns_empty_on_failed_step():
    """_narrow_from_seed_ops returns {} when the prerequisite step failed."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="test",
        params={},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="seed-1",
            domain="seed_ops",
            status="failed",
            error_category="missing_service",
        )
    )

    assert se._narrow_from_seed_ops(ctx, "seed-1") == {}


def test_get_narrowing_for_step_includes_weather_and_seed_ops():
    """_get_narrowing_for_step dispatches to weather and seed_ops extractors."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="test",
        params={},
    )

    weather_payload = {
        "location": "Delhi",
        "summary": {"temp_max": 38},
        "alerts": [],
        "impacts_count": 0,
    }
    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="weather-1",
            domain="weather",
            status="success",
            records={"weather": weather_payload},
        )
    )
    ctx.add(
        StepResult(
            step_id="seed-1",
            domain="seed_ops",
            status="success",
            records={"seedlots": [{"germplasm_id": 42, "quantity_grams": 300}]},
        )
    )

    analytics_step = _make_step(
        "analytics-1", "analytics", prerequisites=["weather-1", "seed-1"]
    )
    narrowing = se._get_narrowing_for_step(analytics_step, ctx)

    assert "weather_data" in narrowing
    assert narrowing["weather_data"]["location"] == "Delhi"
    assert 42 in narrowing["available_germplasm_ids"]


def test_phenotyping_step_metadata_includes_narrowing_audit_trail():
    """Phenotyping step metadata includes narrowing_sources and narrowing_counts."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="show plant height observations",
        params={"trait": "plant height"},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="trials-1",
            domain="trials",
            status="success",
            entity_ids=["T1"],
            metadata={"resolved_study_ids": ["S1", "S2"]},
        )
    )

    # The phenotyping step metadata should carry narrowing_sources and narrowing_counts
    # even when the observation service is absent (safe failure path still records metadata)
    step = _make_step("pheno-1", "phenotyping", prerequisites=["trials-1"])
    # We test the metadata keys exist on a successful result by checking the
    # narrowing_sources list is populated when trials narrowing is applied.
    # Use a mock observation service that returns empty results.
    import unittest.mock as mock
    mock_obs_service = mock.AsyncMock()
    mock_obs_service.search = mock.AsyncMock(return_value=[])
    se._executor.observation_search_service = mock_obs_service

    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        se._execute_phenotyping_step(step, ctx)
    )

    assert result.status == "success"
    assert "narrowing_sources" in result.metadata
    assert "narrowing_counts" in result.metadata
    assert isinstance(result.metadata["narrowing_counts"], dict)


def test_seed_ops_step_metadata_includes_narrowing_audit_trail():
    """Seed ops step metadata includes narrowing_sources and narrowing_counts."""
    se = StepExecutor(
        executor=_make_executor(),
        organization_id=1,
        original_query="check seed availability",
        params={},
    )

    ctx = IntermediateResultContext()
    ctx.add(
        StepResult(
            step_id="breeding-1",
            domain="breeding",
            status="success",
            entity_ids=["10", "20"],
            records={"traits": []},
        )
    )

    import unittest.mock as mock
    mock_seedlot_service = mock.AsyncMock()
    mock_seedlot_service.search = mock.AsyncMock(return_value=[])
    se._executor.seedlot_search_service = mock_seedlot_service

    step = _make_step("seed-1", "seed_ops", prerequisites=["breeding-1"])

    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        se._execute_seed_ops_step(step, ctx)
    )

    assert result.status == "success"
    assert "narrowing_sources" in result.metadata
    assert "narrowing_counts" in result.metadata
    assert result.metadata["narrowing_sources"] == ["breeding"]
    assert result.metadata["narrowing_counts"]["germplasm_ids"] == 2
