"""
TDD tests for REEVU outer ring domain steps:
climate, commercial, harvest, nursery, vision.

Written BEFORE the planner registration and StepExecutor implementation.
RED → GREEN → REFACTOR.

Covers:
- Task 1: Planner registration (keywords, DOMAIN_ORDER, dependencies)
- Tasks 2-6: Each domain step (safe failure, success, narrowing)
- Task 8: Integration narrowing tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.ai.services.reevu.step_executor import StepExecutor, DOMAIN_ORDER
from app.modules.ai.services.reevu.planner import ReevuPlanner
from app.modules.ai.services.reevu.step_executor import (
    IntermediateResultContext,
    StepResult,
)
from app.schemas.reevu_plan import PlanStep


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_executor(**kwargs) -> MagicMock:
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
    executor.climate_service = kwargs.get("climate_service")
    executor.commercial_service = kwargs.get("commercial_service")
    executor.harvest_service = kwargs.get("harvest_service")
    executor.nursery_service = kwargs.get("nursery_service")
    executor.vision_service = kwargs.get("vision_service")
    return executor


def _make_step(step_id: str, domain: str, prerequisites: list[str] | None = None) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        domain=domain,
        prerequisites=prerequisites or [],
        description=f"{domain} step",
        expected_outputs=[],
    )


def _make_se(query: str = "test", **kwargs) -> StepExecutor:
    return StepExecutor(
        executor=_make_executor(**kwargs),
        organization_id=1,
        original_query=query,
        params={},
    )


# ── Task 1: Planner registration ─────────────────────────────────────────────

def test_planner_detects_climate_domain():
    planner = ReevuPlanner()
    for kw in ["climate change", "SSP", "2050", "future climate", "climate risk"]:
        plan = planner.build_plan(f"what is the {kw} projection for our trial sites?")
        domains = [s.domain for s in plan.steps]
        assert "climate" in domains, f"Expected 'climate' for keyword '{kw}'"


def test_planner_detects_commercial_domain():
    planner = ReevuPlanner()
    for kw in ["variety release", "market demand", "licensing", "royalty"]:
        plan = planner.build_plan(f"show {kw} data for our wheat varieties")
        domains = [s.domain for s in plan.steps]
        assert "commercial" in domains, f"Expected 'commercial' for keyword '{kw}'"


def test_planner_detects_harvest_domain():
    planner = ReevuPlanner()
    for kw in ["harvest", "yield data", "quality grade", "post-harvest"]:
        plan = planner.build_plan(f"show {kw} results from last season")
        domains = [s.domain for s in plan.steps]
        assert "harvest" in domains, f"Expected 'harvest' for keyword '{kw}'"


def test_planner_detects_nursery_domain():
    planner = ReevuPlanner()
    for kw in ["nursery", "seedling", "transplant", "irrigation schedule"]:
        plan = planner.build_plan(f"show {kw} status for our rice crop")
        domains = [s.domain for s in plan.steps]
        assert "nursery" in domains, f"Expected 'nursery' for keyword '{kw}'"


def test_planner_detects_vision_domain():
    planner = ReevuPlanner()
    for kw in ["identify disease", "plant image", "leaf photo", "visual scan"]:
        plan = planner.build_plan(f"{kw} of my wheat crop")
        domains = [s.domain for s in plan.steps]
        assert "vision" in domains, f"Expected 'vision' for keyword '{kw}'"


def test_domain_order_outer_ring_after_protocols():
    """All outer ring domains must come after protocols and before or at analytics."""
    protocols_pos = DOMAIN_ORDER["protocols"]
    analytics_pos = DOMAIN_ORDER["analytics"]
    for domain in ("climate", "commercial", "harvest", "nursery", "vision"):
        assert DOMAIN_ORDER[domain] > protocols_pos, f"{domain} must be after protocols"
        assert DOMAIN_ORDER[domain] < analytics_pos, f"{domain} must be before analytics"


def test_all_outer_ring_handlers_registered():
    """StepExecutor must have all five outer ring domains in _domain_handlers."""
    se = _make_se()
    for domain in ("climate", "commercial", "harvest", "nursery", "vision"):
        assert domain in se._domain_handlers, f"Missing handler for '{domain}'"


def test_planner_climate_depends_on_field():
    """When climate and field are both in the plan, climate depends on field."""
    planner = ReevuPlanner()
    plan = planner.build_plan("show climate change projections for our field locations in 2050")
    steps_by_domain = {s.domain: s for s in plan.steps}
    if "climate" in steps_by_domain and "field" in steps_by_domain:
        assert steps_by_domain["field"].step_id in steps_by_domain["climate"].prerequisites


def test_planner_harvest_depends_on_trials():
    """When harvest and trials are both in the plan, harvest depends on trials."""
    planner = ReevuPlanner()
    plan = planner.build_plan("show harvest yield data from our wheat trials")
    steps_by_domain = {s.domain: s for s in plan.steps}
    if "harvest" in steps_by_domain and "trials" in steps_by_domain:
        assert steps_by_domain["trials"].step_id in steps_by_domain["harvest"].prerequisites


def test_planner_commercial_depends_on_breeding():
    """When commercial and breeding are both in the plan, commercial depends on breeding."""
    planner = ReevuPlanner()
    plan = planner.build_plan("show variety release and market demand for our top germplasm")
    steps_by_domain = {s.domain: s for s in plan.steps}
    if "commercial" in steps_by_domain and "breeding" in steps_by_domain:
        assert steps_by_domain["breeding"].step_id in steps_by_domain["commercial"].prerequisites


# ── Task 2: _execute_climate_step() ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_climate_step_safe_fails_when_service_unavailable():
    se = _make_se(climate_service=None)
    result = await se._execute_climate_step(_make_step("c-1", "climate"), IntermediateResultContext())
    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_climate_step_returns_success_with_projections():
    mock_svc = MagicMock()
    mock_svc.get_projections = MagicMock(return_value={
        "scenario": "SSP2-4.5",
        "year": 2050,
        "temp_change_c": 1.8,
        "rainfall_change_pct": -12.0,
    })
    se = StepExecutor(
        executor=_make_executor(climate_service=mock_svc),
        organization_id=1,
        original_query="climate projection for 2050",
        params={"scenario": "SSP2-4.5", "year": 2050, "crop": "wheat"},
    )
    result = await se._execute_climate_step(_make_step("c-1", "climate"), IntermediateResultContext())
    assert result.status == "success"
    assert "climate_projections" in result.records
    assert "crop_suitability" in result.records


@pytest.mark.asyncio
async def test_climate_step_safe_fails_for_invalid_scenario():
    mock_svc = MagicMock()
    se = StepExecutor(
        executor=_make_executor(climate_service=mock_svc),
        organization_id=1,
        original_query="climate projection",
        params={"scenario": "INVALID_SCENARIO"},
    )
    result = await se._execute_climate_step(_make_step("c-1", "climate"), IntermediateResultContext())
    assert result.status == "failed"
    assert result.error_category == "invalid_parameter"


@pytest.mark.asyncio
async def test_climate_step_uses_field_location_narrowing():
    mock_svc = MagicMock()
    mock_svc.get_projections = MagicMock(return_value={"scenario": "SSP2-4.5", "year": 2050})
    se = StepExecutor(
        executor=_make_executor(climate_service=mock_svc),
        organization_id=1,
        original_query="climate projection",
        params={"scenario": "SSP2-4.5", "year": 2050},
    )
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="field-1", domain="field", status="success",
        records={"locations": [{"id": 5, "name": "Ludhiana", "latitude": 30.9, "longitude": 75.8}]},
        entity_ids=["5"],
    ))
    step = _make_step("c-1", "climate", prerequisites=["field-1"])
    result = await se._execute_climate_step(step, ctx)
    assert result.status == "success"
    assert result.metadata.get("narrowing_applied") is True


# ── Task 3: _execute_commercial_step() ───────────────────────────────────────

@pytest.mark.asyncio
async def test_commercial_step_safe_fails_when_service_unavailable():
    se = _make_se(commercial_service=None)
    result = await se._execute_commercial_step(_make_step("com-1", "commercial"), IntermediateResultContext())
    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_commercial_step_returns_variety_releases():
    mock_svc = MagicMock()
    mock_svc.list_varieties = MagicMock(return_value=[
        {"variety_id": "V-001", "name": "IR64", "status": "released", "crop": "Rice"},
    ])
    se = StepExecutor(
        executor=_make_executor(commercial_service=mock_svc),
        organization_id=1,
        original_query="show variety release status",
        params={"crop": "rice"},
    )
    result = await se._execute_commercial_step(_make_step("com-1", "commercial"), IntermediateResultContext())
    assert result.status == "success"
    assert "variety_releases" in result.records
    assert "market_demand" in result.records


@pytest.mark.asyncio
async def test_commercial_step_uses_breeding_germplasm_narrowing():
    mock_svc = MagicMock()
    mock_svc.list_varieties = MagicMock(return_value=[])
    se = StepExecutor(
        executor=_make_executor(commercial_service=mock_svc),
        organization_id=1,
        original_query="commercial data for our germplasm",
        params={},
    )
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="breeding-1", domain="breeding", status="success",
        entity_ids=["10", "20"], records={"traits": []},
    ))
    step = _make_step("com-1", "commercial", prerequisites=["breeding-1"])
    result = await se._execute_commercial_step(step, ctx)
    assert result.status == "success"
    assert result.metadata.get("narrowing_applied") is True
    assert "breeding" in result.metadata.get("narrowing_sources", [])


# ── Task 4: _execute_harvest_step() ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_harvest_step_safe_fails_when_service_unavailable():
    se = _make_se(harvest_service=None)
    result = await se._execute_harvest_step(_make_step("h-1", "harvest"), IntermediateResultContext())
    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_harvest_step_returns_harvest_records_and_yield_summary():
    mock_svc = MagicMock()
    mock_svc.list_harvests = MagicMock(return_value=[
        {"harvest_id": "H-001", "trial_id": "T1", "yield_kg_ha": 4500.0, "quality_grade": "A"},
        {"harvest_id": "H-002", "trial_id": "T1", "yield_kg_ha": 4200.0, "quality_grade": "B"},
    ])
    se = StepExecutor(
        executor=_make_executor(harvest_service=mock_svc),
        organization_id=1,
        original_query="show harvest yield data",
        params={},
    )
    result = await se._execute_harvest_step(_make_step("h-1", "harvest"), IntermediateResultContext())
    assert result.status == "success"
    assert "harvest_records" in result.records
    assert "yield_summary" in result.records
    summary = result.records["yield_summary"]
    assert abs(summary["mean_yield_kg_ha"] - 4350.0) < 0.01
    assert summary["min_yield_kg_ha"] == 4200.0
    assert summary["max_yield_kg_ha"] == 4500.0


@pytest.mark.asyncio
async def test_harvest_step_uses_trials_narrowing():
    mock_svc = MagicMock()
    mock_svc.list_harvests = MagicMock(return_value=[])
    se = StepExecutor(
        executor=_make_executor(harvest_service=mock_svc),
        organization_id=1,
        original_query="harvest data from trials",
        params={},
    )
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="trials-1", domain="trials", status="success",
        entity_ids=["T1", "T2"],
        metadata={"resolved_study_ids": ["S1"]},
        records={},
    ))
    step = _make_step("h-1", "harvest", prerequisites=["trials-1"])
    result = await se._execute_harvest_step(step, ctx)
    assert result.status == "success"
    assert result.metadata.get("narrowing_applied") is True
    assert "trials" in result.metadata.get("narrowing_sources", [])


# ── Task 5: _execute_nursery_step() ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_nursery_step_safe_fails_when_service_unavailable():
    se = _make_se(nursery_service=None)
    result = await se._execute_nursery_step(_make_step("n-1", "nursery"), IntermediateResultContext())
    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_nursery_step_returns_nursery_operations():
    mock_svc = MagicMock()
    mock_svc.list_nurseries = MagicMock(return_value=[
        {"nursery_id": "N-001", "name": "Rice Nursery Block A", "status": "active"},
    ])
    se = StepExecutor(
        executor=_make_executor(nursery_service=mock_svc),
        organization_id=1,
        original_query="show nursery status",
        params={"crop": "rice"},
    )
    result = await se._execute_nursery_step(_make_step("n-1", "nursery"), IntermediateResultContext())
    assert result.status == "success"
    assert "nursery_operations" in result.records
    assert "transplanting_schedules" in result.records
    assert "crop_management_events" in result.records


@pytest.mark.asyncio
async def test_nursery_step_uses_field_location_narrowing():
    mock_svc = MagicMock()
    mock_svc.list_nurseries = MagicMock(return_value=[])
    se = StepExecutor(
        executor=_make_executor(nursery_service=mock_svc),
        organization_id=1,
        original_query="nursery at our field locations",
        params={},
    )
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="field-1", domain="field", status="success",
        records={"locations": [{"id": 3, "name": "Pantnagar"}]},
        entity_ids=["3"],
    ))
    step = _make_step("n-1", "nursery", prerequisites=["field-1"])
    result = await se._execute_nursery_step(step, ctx)
    assert result.status == "success"
    assert result.metadata.get("narrowing_applied") is True


# ── Task 6: _execute_vision_step() ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_vision_step_safe_fails_when_service_unavailable():
    se = _make_se(vision_service=None)
    se._executor.vision_service = None
    result = await se._execute_vision_step(_make_step("v-1", "vision"), IntermediateResultContext())
    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_vision_step_safe_fails_when_no_image_provided():
    mock_svc = MagicMock()
    se = StepExecutor(
        executor=_make_executor(vision_service=mock_svc),
        organization_id=1,
        original_query="identify disease on my wheat",
        params={},  # no image_url or image_base64
    )
    result = await se._execute_vision_step(_make_step("v-1", "vision"), IntermediateResultContext())
    assert result.status == "failed"
    assert result.error_category == "missing_input"
    assert "image" in result.error_message.lower()


@pytest.mark.asyncio
async def test_vision_step_returns_classification_with_image_url():
    mock_svc = MagicMock()
    mock_svc.analyze = MagicMock(return_value={
        "classification": "Rice Blast",
        "confidence": 0.87,
        "recommendation": "Apply fungicide within 48 hours",
    })
    se = StepExecutor(
        executor=_make_executor(vision_service=mock_svc),
        organization_id=1,
        original_query="identify disease in this image",
        params={"image_url": "https://example.com/leaf.jpg", "crop": "rice"},
    )
    result = await se._execute_vision_step(_make_step("v-1", "vision"), IntermediateResultContext())
    assert result.status == "success"
    assert "classification_result" in result.records
    assert "confidence_score" in result.records
    assert "management_recommendation" in result.records
