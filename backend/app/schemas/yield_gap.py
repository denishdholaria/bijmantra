"""Pydantic schemas for yield-gap API responses."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class LimitingFactorSchema(BaseModel):
    factor: str
    score: float
    severity: str
    explanation: str


class YieldGapChartPoint(BaseModel):
    label: str
    value: float


class YieldGapResponse(BaseModel):
    location_id: int
    germplasm_id: int | None = None
    actual_yield: float
    potential_yield: float
    gap_absolute: float
    gap_percent: float
    economic_loss: float = Field(description="Estimated loss in local currency")
    climate_scenario_potential_yield: float
    limiting_factors: List[LimitingFactorSchema]
    sensitivity_analysis: Dict[str, float]
    chart_data: List[YieldGapChartPoint]
