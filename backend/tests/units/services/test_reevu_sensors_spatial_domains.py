"""
TDD tests for REEVU sensors and spatial domain steps.

Written BEFORE the planner registration and StepExecutor implementation.
RED → GREEN → REFACTOR.

Covers:
- Tasks 1.1-1.5: Planner registration (keywords, DOMAIN_ORDER, dependencies)
- Tasks 2.1-2.7: _execute_sensors_step()
- Tasks 3.1-3.6: _execute_spatial_step()
- Tasks 4.1-4.2: _narrow_from_sensors()
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

def _make_executor(iot_service=None, spatial_service=None) -> MagicMock:
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
    executor.iot_telemetry_service = iot_service
    executor.spatial_query_service = spatial_service
    return executor


def _make_step(step_id: str, domain: str, prerequisites: list[str] | None = None) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        domain=domain,
        prerequisites=prerequisites or [],
        description=f"{domain} step",
        expected_outputs=[],
    )


def _make_se(query: str = "test", iot_service=None, spatial_service=None) -> StepExecutor:
    return StepExecutor(
        executor=_make_executor(iot_service=iot_service, spatial_service=spatial_service),
        organization_id=1,
        original_query=query,
        params={},
    )


# ── Task 1: Planner registration ─────────────────────────────────────────────

def test_planner_detects_sensors_domain_from_keywords():
    """Planner detects sensors domain from IoT/telemetry keywords."""
    planner = ReevuPlanner()
    for keyword in ["sensor reading", "IoT", "telemetry", "soil moisture sensor", "data logger"]:
        plan = planner.build_plan(f"show {keyword} data for our field locations")
        domains = [s.domain for s in plan.steps]
        assert "sensors" in domains, f"Expected 'sensors' for keyword '{keyword}'"


def test_planner_detects_spatial_domain_from_keywords():
    """Planner detects spatial domain from proximity/map keywords."""
    planner = ReevuPlanner()
    for keyword in ["nearby", "within 50km", "radius", "proximity", "spatial"]:
        plan = planner.build_plan(f"find trials {keyword} of Hyderabad")
        domains = [s.domain for s in plan.steps]
        assert "spatial" in domains, f"Expected 'spatial' for keyword '{keyword}'"


def test_domain_order_sensors_after_field_before_phenotyping():
    """sensors must come after field and before phenotyping in DOMAIN_ORDER."""
    assert DOMAIN_ORDER["sensors"] > DOMAIN_ORDER["field"]
    assert DOMAIN_ORDER["sensors"] < DOMAIN_ORDER["phenotyping"]


def test_domain_order_spatial_is_last():
    """spatial must come after analytics in DOMAIN_ORDER."""
    assert DOMAIN_ORDER["spatial"] > DOMAIN_ORDER["analytics"]


def test_sensors_handler_registered():
    """StepExecutor must have 'sensors' in _domain_handlers."""
    se = _make_se()
    assert "sensors" in se._domain_handlers


def test_spatial_handler_registered():
    """StepExecutor must have 'spatial' in _domain_handlers."""
    se = _make_se()
    assert "spatial" in se._domain_handlers


def test_planner_sensors_depends_on_field():
    """When both sensors and field are in the plan, sensors depends on field."""
    planner = ReevuPlanner()
    plan = planner.build_plan("show sensor readings at our field locations")
    steps_by_domain = {s.domain: s for s in plan.steps}
    if "sensors" in steps_by_domain and "field" in steps_by_domain:
        field_step_id = steps_by_domain["field"].step_id
        assert field_step_id in steps_by_domain["sensors"].prerequisites


# ── Task 2: _execute_sensors_step() ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_sensors_step_safe_fails_when_service_unavailable():
    """_execute_sensors_step() returns status='failed' when IoT service is None."""
    se = _make_se(iot_service=None)
    step = _make_step("sensors-1", "sensors")
    ctx = IntermediateResultContext()

    result = await se._execute_sensors_step(step, ctx)

    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_sensors_step_returns_success_with_empty_results():
    """_execute_sensors_step() returns status='success' when service returns []."""
    mock_iot = AsyncMock()
    mock_iot.get_readings = AsyncMock(return_value=[])
    mock_iot.get_device_status = AsyncMock(return_value=[])

    se = _make_se(iot_service=mock_iot)
    step = _make_step("sensors-1", "sensors")
    ctx = IntermediateResultContext()

    result = await se._execute_sensors_step(step, ctx)

    assert result.status == "success"
    assert "sensor_readings" in result.records
    assert "telemetry_summary" in result.records
    assert "device_status" in result.records
    assert result.records["sensor_readings"] == []


@pytest.mark.asyncio
async def test_sensors_step_uses_field_location_narrowing():
    """_execute_sensors_step() passes location_id from field step to IoT service."""
    mock_iot = AsyncMock()
    mock_iot.get_readings = AsyncMock(return_value=[])
    mock_iot.get_device_status = AsyncMock(return_value=[])

    se = _make_se(iot_service=mock_iot)

    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="field-1",
        domain="field",
        status="success",
        records={"locations": [{"id": 7, "name": "Ludhiana", "latitude": 30.9, "longitude": 75.8}]},
        entity_ids=["7"],
    ))

    step = _make_step("sensors-1", "sensors", prerequisites=["field-1"])
    result = await se._execute_sensors_step(step, ctx)

    assert result.status == "success"
    # IoT service must have been called with location_id=7
    mock_iot.get_readings.assert_called_once()
    call_kwargs = mock_iot.get_readings.call_args[1]
    assert call_kwargs.get("location_id") == 7


@pytest.mark.asyncio
async def test_sensors_step_computes_telemetry_summary():
    """_execute_sensors_step() computes min/max/mean per sensor type."""
    readings = [
        {"sensor_type": "temperature", "value": 28.0, "device_id": "D1"},
        {"sensor_type": "temperature", "value": 32.0, "device_id": "D1"},
        {"sensor_type": "humidity", "value": 65.0, "device_id": "D1"},
    ]
    mock_iot = AsyncMock()
    mock_iot.get_readings = AsyncMock(return_value=readings)
    mock_iot.get_device_status = AsyncMock(return_value=[])

    se = _make_se(iot_service=mock_iot)
    step = _make_step("sensors-1", "sensors")
    ctx = IntermediateResultContext()

    result = await se._execute_sensors_step(step, ctx)

    assert result.status == "success"
    summary = result.records["telemetry_summary"]
    assert "temperature" in summary
    assert abs(summary["temperature"]["mean"] - 30.0) < 0.01
    assert summary["temperature"]["min"] == 28.0
    assert summary["temperature"]["max"] == 32.0
    assert "humidity" in summary


@pytest.mark.asyncio
async def test_sensors_step_metadata_records_narrowing():
    """_execute_sensors_step() records narrowing_applied and narrowing_sources."""
    mock_iot = AsyncMock()
    mock_iot.get_readings = AsyncMock(return_value=[])
    mock_iot.get_device_status = AsyncMock(return_value=[])

    se = _make_se(iot_service=mock_iot)
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="field-1",
        domain="field",
        status="success",
        records={"locations": [{"id": 7, "name": "Ludhiana"}]},
        entity_ids=["7"],
    ))

    step = _make_step("sensors-1", "sensors", prerequisites=["field-1"])
    result = await se._execute_sensors_step(step, ctx)

    assert result.metadata.get("narrowing_applied") is True
    assert "field" in result.metadata.get("narrowing_sources", [])


# ── Task 3: _execute_spatial_step() ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_spatial_step_safe_fails_when_service_unavailable():
    """_execute_spatial_step() returns status='failed' when spatial service is None."""
    se = _make_se(spatial_service=None)
    se._executor.location_search_service = None
    step = _make_step("spatial-1", "spatial")
    ctx = IntermediateResultContext()

    result = await se._execute_spatial_step(step, ctx)

    assert result.status == "failed"
    assert result.error_category == "missing_service"


@pytest.mark.asyncio
async def test_spatial_step_returns_proximity_results_with_lat_lon():
    """_execute_spatial_step() calls find_nearest_locations when lat/lon provided."""
    mock_spatial = AsyncMock()
    mock_spatial.find_nearest_locations = AsyncMock(return_value=[
        {"location_id": 1, "location_name": "ICRISAT", "distance_km": 12.5},
        {"location_id": 2, "location_name": "ICAR", "distance_km": 34.1},
    ])

    se = StepExecutor(
        executor=_make_executor(spatial_service=mock_spatial),
        organization_id=1,
        original_query="find trials within 50km of Hyderabad",
        params={"lat": 17.4, "lon": 78.5, "radius_km": 50},
    )
    step = _make_step("spatial-1", "spatial")
    ctx = IntermediateResultContext()

    result = await se._execute_spatial_step(step, ctx)

    assert result.status == "success"
    assert "spatial_results" in result.records
    assert len(result.records["spatial_results"]) == 2
    mock_spatial.find_nearest_locations.assert_called_once()


@pytest.mark.asyncio
async def test_spatial_step_returns_empty_when_no_results():
    """_execute_spatial_step() returns success with empty results when nothing found."""
    mock_spatial = AsyncMock()
    mock_spatial.find_nearest_locations = AsyncMock(return_value=[])

    se = StepExecutor(
        executor=_make_executor(spatial_service=mock_spatial),
        organization_id=1,
        original_query="find trials within 10km of remote location",
        params={"lat": 0.0, "lon": 0.0, "radius_km": 10},
    )
    step = _make_step("spatial-1", "spatial")
    ctx = IntermediateResultContext()

    result = await se._execute_spatial_step(step, ctx)

    assert result.status == "success"
    assert result.records["spatial_results"] == []


@pytest.mark.asyncio
async def test_spatial_step_includes_region_summary():
    """_execute_spatial_step() includes region_summary with count."""
    mock_spatial = AsyncMock()
    mock_spatial.find_nearest_locations = AsyncMock(return_value=[
        {"location_id": 1, "location_name": "Site A", "distance_km": 5.0},
    ])

    se = StepExecutor(
        executor=_make_executor(spatial_service=mock_spatial),
        organization_id=1,
        original_query="find locations within 20km",
        params={"lat": 17.4, "lon": 78.5, "radius_km": 20},
    )
    step = _make_step("spatial-1", "spatial")
    ctx = IntermediateResultContext()

    result = await se._execute_spatial_step(step, ctx)

    assert "region_summary" in result.records
    assert result.records["region_summary"]["total_found"] == 1
    assert result.records["region_summary"]["radius_km"] == 20


# ── Task 4: _narrow_from_sensors() ───────────────────────────────────────────

def test_narrow_from_sensors_extracts_telemetry_summary():
    """_narrow_from_sensors() extracts telemetry_summary from a sensors step."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="sensors-1",
        domain="sensors",
        status="success",
        records={
            "sensor_readings": [],
            "telemetry_summary": {"temperature": {"mean": 30.0, "min": 28.0, "max": 32.0}},
            "device_status": [],
        },
    ))

    narrowing = se._narrow_from_sensors(ctx, "sensors-1")

    assert "telemetry_summary" in narrowing
    assert narrowing["telemetry_summary"]["temperature"]["mean"] == 30.0


def test_narrow_from_sensors_returns_empty_on_failed_step():
    """_narrow_from_sensors() returns {} when the step failed."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="sensors-1",
        domain="sensors",
        status="failed",
        error_category="missing_service",
    ))

    assert se._narrow_from_sensors(ctx, "sensors-1") == {}


def test_narrow_from_sensors_returns_empty_when_no_summary():
    """_narrow_from_sensors() returns {} when records have no telemetry_summary."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="sensors-1",
        domain="sensors",
        status="success",
        records={},
    ))

    assert se._narrow_from_sensors(ctx, "sensors-1") == {}


def test_get_narrowing_dispatches_to_sensors():
    """_get_narrowing_for_step() dispatches to _narrow_from_sensors."""
    se = _make_se()
    ctx = IntermediateResultContext()
    ctx.add(StepResult(
        step_id="sensors-1",
        domain="sensors",
        status="success",
        records={
            "telemetry_summary": {"humidity": {"mean": 70.0, "min": 60.0, "max": 80.0}},
        },
    ))

    analytics_step = _make_step("analytics-1", "analytics", prerequisites=["sensors-1"])
    narrowing = se._get_narrowing_for_step(analytics_step, ctx)

    assert "telemetry_summary" in narrowing
    assert narrowing["telemetry_summary"]["humidity"]["mean"] == 70.0
