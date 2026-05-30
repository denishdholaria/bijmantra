"""
TDD tests for REEVU soil and pest_disease domain steps.

Written BEFORE the planner registration and StepExecutor implementation.
RED → GREEN → REFACTOR.

Covers:
- Tasks 3.1-3.5: Planner registration (keywords, DOMAIN_ORDER, dependencies)
- Tasks 4.1-4.5: _execute_soil_step()
- Tasks 5.1-5.5: _execute_pest_disease_step()
- Tasks 6.1-6.3: _narrow_from_soil(), _narrow_from_pest_disease()
- Tasks 7.1-7.2: Integration narrowing tests
"""

import asyncio
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

def _make_executor(
    soil_service=None,
    disease_service=None,
) -> MagicMock:
    """Build a minimal FunctionExecutor mock."""
    executor = MagicMock()
    executor.db = AsyncMock()
    executor.trial_search_service = None
    executor.germplasm_search_service = None
    executor.observation_search_service = None
    executor.trait_search_service = None
    executor.weather_service = None
    executor.location_search_service = None
    executor.seedlot_search_service = None
    executor.soil_analysis_search_service = soil_service
    executor.disease_resistance_search_service = disease_service
    return executor


def _make_step(
    step_id: str,
    domain: str,
    prerequisites: list[str] | None = None,
) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        domain=domain,
        prerequisites=prerequisites or [],
        description=f"{domain} step",
        expected_outputs=[],
    )


def _make_se(
    query: str = "test",
    soil_service=None,
    disease_service=None,
) -> StepExecutor:
    return StepExecutor(
        executor=_make_executor(
            soil_service=soil_service,
            disease_service=disease_service,
        ),
        organization_id=1,
        original_query=query,
        params={},
    )


# ── Task 3: Planner registration ─────────────────────────────────────────────

def test_planner_detects_soil_domain_from_keywords():
    """Planner registers soil domain and detects it from soil-related keywords."""
    planner = ReevuPlanner()
    for keyword in ["soil", "nutrient", "pH", "organic matter", "nitrogen", "NPK"]:
        plan = planner.build_plan(f"what is the {keyword} level at our trial sites?")
        domains = [s.domain for s in plan.steps]
        assert "soil" in domains, f"Expected 'soil' domain for keyword '{keyword}'"


def test_planner_detects_pest_disease_domain_from_keywords():
    """Planner registers pest_disease domain and detects it from disease-related keywords."""
    planner = ReevuPlanner()
    for keyword in ["disease pressure", "pest scouting", "susceptibility", "blight", "aphid"]:
        plan = planner.build_plan(f"show {keyword} data for our wheat varieties")
        domains = [s.domain for s in plan.steps]
        assert "pest_disease" in domains, f"Expected 'pest_disease' domain for keyword '{keyword}'"


def test_domain_order_soil_after_seed_ops_before_protocols():
    """soil must come after seed_ops and before protocols in DOMAIN_ORDER."""
    assert DOMAIN_ORDER["soil"] > DOMAIN_ORDER["seed_ops"]
    assert DOMAIN_ORDER["soil"] < DOMAIN_ORDER.get("protocols", 999)


def test_domain_order_pest_disease_after_soil():
    """pest_disease must come after soil in DOMAIN_ORDER."""
    assert DOMAIN_ORDER["pest_disease"] > DOMAIN_ORDER["soil"]


def test_soil_handler_registered_in_step_executor():
    """StepExecutor must have 'soil' in _domain_handlers."""
    se = _make_se()
    assert "soil" in se._domain_handlers


def test_pest_disease_handler_registered_in_step_executor():
    """StepExecutor must have 'pest_disease' in _domain_handlers."""
    se = _make_se()
    assert "pest_disease" in se._domain_handlers


def test_planner_soil_depends_on_field():
    """When both soil and field are in the plan, soil must depend on field."""
    planner = ReevuPlanner()
    plan = planner.build_plan(
        "show soil nutrient levels at our field locations"
    )
    steps_by_domain = {s.domain: s for s in plan.steps}
    if "soil" in steps_by_domain and "field" in steps_by_domain:
        field_step_id = steps_by_domain["field"].step_id
        assert field_step_id in steps_by_domain["soil"].prerequisites


def test_planner_pest_disease_depends_on_trials_or_breeding():
    """When pest_disease and trials/breeding are in the plan, pest_disease depends on them."""
    planner = ReevuPlanner()
    plan = planner.build_plan(
        "show disease resistance for our top germplasm from trials"
    )
    steps_by_domain = {s.domain: s for s in plan.steps}
    if "pest_disease" in steps_by_domain:
        pest_step = steps_by_domain["pest_disease"]
        upstream_ids = {
            steps_by_domain[d].step_id
            for d in ("trials", "breeding")
            if d in steps_by_domain
        }
        assert pest_step.prerequisites or not upstream_ids, (
            "pest_disease step should depend on trials/breeding when they are present"
        )


# ── Task 4: _execute_soil_step() ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_soil_step_safe_fails_when_service_unavailable():
    """_execute_soil_step() returns status='failed' when soil service is None."""
    se = _make_se(soil_service=None)
    step = _make_step("soil-1", "soil")
    ctx = IntermediateResultContext()

    result = await se._execute_soil_step(step, ctx)

    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_soil_step_returns_success_with_empty_results():
    """_execute_soil_step() returns status='success' even when service returns []."""
    mock_service = AsyncMock()
    mock_service.search = AsyncMock(return_value=[])
    mock_service.get_nutrient_summary = AsyncMock(return_value={
        "location_id": None,
        "sample_count": 0,
        "mean_ph": None,
        "mean_n_ppm": None,
        "mean_p_ppm": None,
        "mean_k_ppm": None,
        "mean_organic_matter_percent": None,
        "soil_health_indicators": {},
    })

    se = _make_se(soil_service=mock_service)
    step = _make_step("soil-1", "soil")
    ctx = IntermediateResultContext()

    result = await se._execute_soil_step(step, ctx)

    assert result.status == "success"
    assert "soil_analyses" in result.records
    assert result.records["soil_analyses"] == []


@pytest.mark.asyncio
async def test_soil_step_uses_field_narrowing_location():
    """_execute_soil_step() passes location_id from field step narrowing to service."""
    mock_service = AsyncMock()
    mock_service.search = AsyncMock(return_value=[])
    mock_service.get_nutrient_summary = AsyncMock(return_value={
        "location_id": 10,
        "sample_count": 0,
        "mean_ph": None,
        "mean_n_ppm": None,
        "mean_p_ppm": None,
        "mean_k_ppm": None,
        "mean_organic_matter_percent": None,
        "soil_health_indicators": {},
    })

    se = _make_se(soil_service=mock_service)

    # Provide a field step result with location records
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="field-1",
        domain="field",
        status="success",
        records={"locations": [{"id": 10, "name": "Ludhiana", "latitude": 30.9, "longitude": 75.8}]},
        entity_ids=["10"],
    ))

    step = _make_step("soil-1", "soil", prerequisites=["field-1"])
    result = await se._execute_soil_step(step, ctx)

    assert result.status == "success"
    # Service must have been called with location_id=10
    mock_service.search.assert_called_once()
    call_kwargs = mock_service.search.call_args[1]
    assert call_kwargs.get("location_id") == 10


@pytest.mark.asyncio
async def test_soil_step_records_contain_nutrient_summary():
    """_execute_soil_step() includes nutrient_summary in records."""
    nutrient_summary = {
        "location_id": 10,
        "sample_count": 3,
        "mean_ph": 6.5,
        "mean_n_ppm": 45.0,
        "mean_p_ppm": 22.0,
        "mean_k_ppm": 130.0,
        "mean_organic_matter_percent": 2.8,
        "soil_health_indicators": {"ph_status": "optimal"},
    }
    mock_service = AsyncMock()
    mock_service.search = AsyncMock(return_value=[{"id": "1", "ph": 6.5}])
    mock_service.get_nutrient_summary = AsyncMock(return_value=nutrient_summary)

    se = _make_se(soil_service=mock_service)
    step = _make_step("soil-1", "soil")
    ctx = IntermediateResultContext()

    result = await se._execute_soil_step(step, ctx)

    assert result.status == "success"
    assert result.records["nutrient_summary"] == nutrient_summary
    assert result.records["soil_health_indicators"] == {"ph_status": "optimal"}


@pytest.mark.asyncio
async def test_soil_step_metadata_records_narrowing_applied():
    """_execute_soil_step() sets narrowing_applied=True when field narrowing was used."""
    mock_service = AsyncMock()
    mock_service.search = AsyncMock(return_value=[])
    mock_service.get_nutrient_summary = AsyncMock(return_value={
        "location_id": 10, "sample_count": 0, "mean_ph": None,
        "mean_n_ppm": None, "mean_p_ppm": None, "mean_k_ppm": None,
        "mean_organic_matter_percent": None, "soil_health_indicators": {},
    })

    se = _make_se(soil_service=mock_service)
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="field-1",
        domain="field",
        status="success",
        records={"locations": [{"id": 10, "name": "Ludhiana"}]},
        entity_ids=["10"],
    ))

    step = _make_step("soil-1", "soil", prerequisites=["field-1"])
    result = await se._execute_soil_step(step, ctx)

    assert result.metadata.get("narrowing_applied") is True
    assert "field" in result.metadata.get("narrowing_sources", [])


# ── Task 5: _execute_pest_disease_step() ─────────────────────────────────────

@pytest.mark.asyncio
async def test_pest_disease_step_safe_fails_when_service_unavailable():
    """_execute_pest_disease_step() returns status='failed' when service is None."""
    se = _make_se(disease_service=None)
    step = _make_step("pd-1", "pest_disease")
    ctx = IntermediateResultContext()

    result = await se._execute_pest_disease_step(step, ctx)

    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_pest_disease_step_returns_success_with_empty_results():
    """_execute_pest_disease_step() returns status='success' when service returns []."""
    mock_service = AsyncMock()
    mock_service.get_resistance_profiles = AsyncMock(return_value=[])
    mock_service.search_scouting_records = AsyncMock(return_value=[])

    se = _make_se(disease_service=mock_service)
    step = _make_step("pd-1", "pest_disease")
    ctx = IntermediateResultContext()

    result = await se._execute_pest_disease_step(step, ctx)

    assert result.status == "success"
    assert "resistance_profiles" in result.records
    assert "scouting_records" in result.records


@pytest.mark.asyncio
async def test_pest_disease_step_uses_breeding_germplasm_narrowing():
    """_execute_pest_disease_step() passes germplasm_ids from breeding step to service."""
    mock_service = AsyncMock()
    mock_service.get_resistance_profiles = AsyncMock(return_value=[])
    mock_service.search_scouting_records = AsyncMock(return_value=[])

    se = _make_se(disease_service=mock_service)

    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="breeding-1",
        domain="breeding",
        status="success",
        entity_ids=["10", "20", "30"],
        records={"traits": []},
    ))

    step = _make_step("pd-1", "pest_disease", prerequisites=["breeding-1"])
    result = await se._execute_pest_disease_step(step, ctx)

    assert result.status == "success"
    # Resistance profiles must have been queried with germplasm_ids
    mock_service.get_resistance_profiles.assert_called_once()
    call_kwargs = mock_service.get_resistance_profiles.call_args[1]
    assert call_kwargs.get("germplasm_ids") == ["10", "20", "30"]


@pytest.mark.asyncio
async def test_pest_disease_step_uses_trials_location_narrowing():
    """_execute_pest_disease_step() passes location from trials step to scouting query."""
    mock_service = AsyncMock()
    mock_service.get_resistance_profiles = AsyncMock(return_value=[])
    mock_service.search_scouting_records = AsyncMock(return_value=[])

    se = _make_se(disease_service=mock_service)

    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="trials-1",
        domain="trials",
        status="success",
        entity_ids=["T1"],
        records={"locations": [{"id": 5, "name": "IRRI"}]},
        metadata={"resolved_study_ids": ["S1"]},
    ))

    step = _make_step("pd-1", "pest_disease", prerequisites=["trials-1"])
    result = await se._execute_pest_disease_step(step, ctx)

    assert result.status == "success"
    mock_service.search_scouting_records.assert_called_once()


@pytest.mark.asyncio
async def test_pest_disease_step_metadata_records_narrowing():
    """_execute_pest_disease_step() records narrowing_applied and narrowing_sources."""
    mock_service = AsyncMock()
    mock_service.get_resistance_profiles = AsyncMock(return_value=[])
    mock_service.search_scouting_records = AsyncMock(return_value=[])

    se = _make_se(disease_service=mock_service)

    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="breeding-1",
        domain="breeding",
        status="success",
        entity_ids=["10"],
        records={"traits": []},
    ))

    step = _make_step("pd-1", "pest_disease", prerequisites=["breeding-1"])
    result = await se._execute_pest_disease_step(step, ctx)

    assert result.metadata.get("narrowing_applied") is True
    assert "breeding" in result.metadata.get("narrowing_sources", [])


# ── Task 6: Narrowing extractors ─────────────────────────────────────────────

def test_narrow_from_soil_extracts_nutrient_summary():
    """_narrow_from_soil() extracts nutrient_summary and soil_health_indicators."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="soil-1",
        domain="soil",
        status="success",
        records={
            "soil_analyses": [],
            "nutrient_summary": {"mean_ph": 6.5, "mean_n_ppm": 45.0},
            "soil_health_indicators": {"ph_status": "optimal"},
        },
    ))

    narrowing = se._narrow_from_soil(ctx, "soil-1")

    assert narrowing["nutrient_summary"] == {"mean_ph": 6.5, "mean_n_ppm": 45.0}
    assert narrowing["soil_health_indicators"] == {"ph_status": "optimal"}


def test_narrow_from_soil_returns_empty_on_failed_step():
    """_narrow_from_soil() returns {} when the prerequisite step failed."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="soil-1",
        domain="soil",
        status="failed",
        error_category="missing_service",
    ))

    assert se._narrow_from_soil(ctx, "soil-1") == {}


def test_narrow_from_soil_returns_empty_when_no_nutrient_summary():
    """_narrow_from_soil() returns {} when records have no nutrient_summary."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="soil-1",
        domain="soil",
        status="success",
        records={},
    ))

    assert se._narrow_from_soil(ctx, "soil-1") == {}


def test_narrow_from_pest_disease_extracts_resistance_profiles():
    """_narrow_from_pest_disease() extracts resistance_profiles."""
    se = _make_se()
    profiles = [{"gene_code": "Xa21", "resistance_type": "complete"}]
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="pd-1",
        domain="pest_disease",
        status="success",
        records={
            "resistance_profiles": profiles,
            "scouting_records": [],
        },
    ))

    narrowing = se._narrow_from_pest_disease(ctx, "pd-1")

    assert narrowing["resistance_profiles"] == profiles


def test_narrow_from_pest_disease_returns_empty_on_failed_step():
    """_narrow_from_pest_disease() returns {} when the prerequisite step failed."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="pd-1",
        domain="pest_disease",
        status="failed",
        error_category="missing_service",
    ))

    assert se._narrow_from_pest_disease(ctx, "pd-1") == {}


def test_get_narrowing_for_step_dispatches_to_soil_and_pest_disease():
    """_get_narrowing_for_step() dispatches to soil and pest_disease extractors."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="soil-1",
        domain="soil",
        status="success",
        records={
            "nutrient_summary": {"mean_ph": 6.5},
            "soil_health_indicators": {"ph_status": "optimal"},
        },
    ))
    ctx.add(StepResult(
        step_id="pd-1",
        domain="pest_disease",
        status="success",
        records={
            "resistance_profiles": [{"gene_code": "Xa21"}],
            "scouting_records": [],
        },
    ))

    analytics_step = _make_step(
        "analytics-1", "analytics", prerequisites=["soil-1", "pd-1"]
    )
    narrowing = se._get_narrowing_for_step(analytics_step, ctx)

    assert "nutrient_summary" in narrowing
    assert "resistance_profiles" in narrowing
