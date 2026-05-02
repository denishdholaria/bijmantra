from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.ai.services.reevu.step_executor import (
    IntermediateResultContext,
    StepExecutor,
    StepResult,
)
from app.schemas.reevu_plan import PlanStep


def _step(step_id: str, domain: str, prerequisites: list[str] | None = None) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        domain=domain,
        description=f"{domain} step",
        prerequisites=prerequisites or [],
        expected_outputs=[f"{domain}_records"],
    )


def _executor() -> MagicMock:
    executor = MagicMock()
    executor.db = AsyncMock()
    executor.observation_search_service = AsyncMock()
    executor.observation_search_service.search = AsyncMock(return_value=[])
    executor.trait_search_service = AsyncMock()
    executor.trait_search_service.search = AsyncMock(return_value=[])
    executor.trial_search_service = AsyncMock()
    executor.trial_search_service.get_by_id = AsyncMock(return_value=None)
    return executor


def _observation(value: float, study_id: str = "101") -> dict[str, object]:
    return {
        "id": f"obs-{study_id}-{value}",
        "observation_db_id": f"OBS-{study_id}-{value}",
        "value": value,
        "trait": {"id": "trait-1", "name": "Plant height", "trait_name": "Plant height"},
        "study": {"id": study_id, "name": f"Study {study_id}"},
        "germplasm": {"id": "germ-1", "name": "Line 1"},
    }


@pytest.mark.asyncio
async def test_phenotyping_step_scopes_observations_from_trial_study_ids():
    executor = _executor()

    async def search(**kwargs):
        return [_observation(float(kwargs["study_id"]), study_id=str(kwargs["study_id"]))]

    executor.observation_search_service.search = AsyncMock(side_effect=search)
    step_executor = StepExecutor(
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
            entity_ids=["trial-1"],
            metadata={"resolved_study_ids": ["101", "102"]},
        )
    )

    result = await step_executor._execute_phenotyping_step(
        _step("phenotyping-1", "phenotyping", prerequisites=["trials-1"]),
        context,
    )

    assert result.status == "success"
    assert result.metadata["narrowing_applied"] is True
    assert result.metadata["narrowing_source"] == "trials"
    assert result.metadata["query_mode"] == "study_scoped"
    assert result.metadata["resolved_study_ids"] == ["101", "102"]
    assert result.records["observation_count"] == 2


@pytest.mark.asyncio
async def test_phenotyping_step_supports_trait_first_queries_without_prerequisites():
    executor = _executor()
    executor.observation_search_service.search = AsyncMock(
        return_value=[_observation(10.0, "101"), _observation(12.0, "102")]
    )
    step_executor = StepExecutor(
        executor=executor,
        organization_id=1,
        original_query="show plant height observations",
        params={"trait": "Plant height"},
    )

    result = await step_executor._execute_phenotyping_step(
        _step("phenotyping-1", "phenotyping"),
        IntermediateResultContext(),
    )

    assert result.status == "success"
    assert result.metadata["query_mode"] == "trait_first"
    assert result.records["observation_count"] == 2
    executor.observation_search_service.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_phenotyping_observations_feed_downstream_analytics():
    step_executor = StepExecutor(
        executor=_executor(),
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
                    _observation(10.0),
                    _observation(12.0),
                    _observation(14.0),
                ]
            },
            entity_ids=["trait-1"],
        )
    )

    result = await step_executor._execute_analytics_step(
        _step("analytics-1", "analytics", prerequisites=["phenotyping-1"]),
        context,
    )

    assert result.status == "success"
    assert result.metadata["used_phenotyping_observations"] is True
    assert result.metadata["observations_count"] == 3
