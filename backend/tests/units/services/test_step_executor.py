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
