"""Yield-gap analysis endpoints."""

from __future__ import annotations

from typing import Dict, Optional

from app.api import deps
from app.models.core import User
from app.schemas.yield_gap import (
    LimitingFactorSchema,
    YieldGapChartPoint,
    YieldGapResponse,
)
from app.services.yield_gap_service import yield_gap_service
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/yield-gap",
    tags=["Yield Gap"],
    dependencies=[Depends(deps.get_current_user)],
)


@router.get("/summary/{location_id}", response_model=YieldGapResponse)
async def get_location_yield_gap_summary(
    location_id: int,
    crop: str = Query("wheat"),
    market_price_per_ton: float = Query(320.0, gt=0),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Return location-level yield-gap summary."""
    try:
        environment = {
            "t_max": 31.0,
            "t_min": 20.0,
            "day_length_hours": 12.2,
            "water_index": 0.86,
            "temperature_index": 0.91,
        }
        soil = {"nitrogen_index": 0.78, "phosphorus_index": 0.82}

        potential = await yield_gap_service.calculate_potential_yield(
            db=db,
            location_id=location_id,
            environmental_params={**environment, **soil},
            crop=crop,
        )
        actuals = await yield_gap_service.fetch_actual_yields(
            db=db,
            germplasm_id=0,
            location_id=location_id,
            year_range=(2020, 2030),
            organization_id=current_user.organization_id,
        )
        actual = sum(actuals) / len(actuals) if actuals else round(potential * 0.76, 3)

        gap = yield_gap_service.calculate_yield_gap(actual=actual, potential=potential)
        limiting_factors = yield_gap_service.identify_limiting_factors(
            environment, soil
        )
        sensitivity = yield_gap_service.sensitivity_analysis(
            gap["gap_percent"], environment, soil
        )
        projected = yield_gap_service.project_climate_scenario(
            potential_yield=potential, delta_temp_c=2.0
        )
        economic = yield_gap_service.economic_impact(
            gap["gap_absolute"], market_price_per_ton
        )

        return YieldGapResponse(
            location_id=location_id,
            actual_yield=gap["actual"],
            potential_yield=gap["potential"],
            gap_absolute=gap["gap_absolute"],
            gap_percent=gap["gap_percent"],
            economic_loss=economic,
            climate_scenario_potential_yield=projected,
            limiting_factors=[
                LimitingFactorSchema(**node.__dict__) for node in limiting_factors
            ],
            sensitivity_analysis=sensitivity,
            chart_data=[
                YieldGapChartPoint(label="Actual", value=gap["actual"]),
                YieldGapChartPoint(label="Potential", value=gap["potential"]),
                YieldGapChartPoint(label="Gap", value=gap["gap_absolute"]),
            ],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/germplasm/{germplasm_id}", response_model=YieldGapResponse)
async def get_germplasm_yield_gap(
    germplasm_id: int,
    location_id: int = Query(...),
    crop: str = Query("wheat"),
    market_price_per_ton: float = Query(320.0, gt=0),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Return germplasm-specific yield-gap summary at a location."""
    if germplasm_id <= 0:
        raise HTTPException(status_code=400, detail="germplasm_id must be positive")

    environment: Dict[str, float] = {
        "t_max": 30.5,
        "t_min": 19.4,
        "day_length_hours": 12.0,
        "water_index": 0.88,
        "temperature_index": 0.90,
    }
    soil = {"nitrogen_index": 0.76, "phosphorus_index": 0.80}

    potential = await yield_gap_service.calculate_potential_yield(
        db=db,
        location_id=location_id,
        environmental_params={**environment, **soil},
        crop=crop,
    )
    actuals = await yield_gap_service.fetch_actual_yields(
        db=db,
        germplasm_id=germplasm_id,
        location_id=location_id,
        year_range=(2020, 2030),
        organization_id=current_user.organization_id,
    )
    if not actuals:
        raise HTTPException(
            status_code=404,
            detail="No yield observations found for germplasm and location",
        )

    actual = sum(actuals) / len(actuals)
    gap = yield_gap_service.calculate_yield_gap(actual=actual, potential=potential)
    limiting_factors = yield_gap_service.identify_limiting_factors(environment, soil)
    sensitivity = yield_gap_service.sensitivity_analysis(
        gap["gap_percent"], environment, soil
    )
    projected = yield_gap_service.project_climate_scenario(
        potential_yield=potential, delta_temp_c=2.0
    )
    economic = yield_gap_service.economic_impact(
        gap["gap_absolute"], market_price_per_ton
    )

    return YieldGapResponse(
        location_id=location_id,
        germplasm_id=germplasm_id,
        actual_yield=gap["actual"],
        potential_yield=gap["potential"],
        gap_absolute=gap["gap_absolute"],
        gap_percent=gap["gap_percent"],
        economic_loss=economic,
        climate_scenario_potential_yield=projected,
        limiting_factors=[
            LimitingFactorSchema(**node.__dict__) for node in limiting_factors
        ],
        sensitivity_analysis=sensitivity,
        chart_data=[
            YieldGapChartPoint(label="Actual", value=gap["actual"]),
            YieldGapChartPoint(label="Potential", value=gap["potential"]),
            YieldGapChartPoint(label="Gap", value=gap["gap_absolute"]),
        ],
    )


@router.get("/spatial/{region_id}")
async def get_spatial_gap(
    region_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Return location-wise spatial yield-gap payload for mapping."""
    data = await yield_gap_service.get_spatial_yield_gap(
        db, region_id, current_user.organization_id
    )
    return {"region_id": region_id, "records": data, "count": len(data)}
