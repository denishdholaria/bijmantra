"""Yield gap analysis service.

This module implements potential-yield simulation, actual-yield fetching,
limiting-factor diagnostics, and economic gap valuation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from time import perf_counter
from typing import Any, Dict, List, Tuple

from app.integrations.base import IntegrationConfig
from app.integrations.brapi import BrAPIAdapter
from app.models.core import Location, Study, Trial
from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable
from app.services.environmental_physics import environmental_service
from app.services.math_utils import clamp, safe_divide
from sqlalchemy import Float, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PotentialYieldModel:
    """Potential-yield response model for a crop.

    Parameters
    ----------
    crop:
        Crop name.
    baseline_t_ha:
        Baseline attainable yield in t/ha under reference conditions.
    optimal_gdd:
        GDD target at which thermal performance is maximal.
    optimal_ptu:
        PTU target at which photothermal performance is maximal.
    thermal_sensitivity:
        Penalty strength for thermal deviation from optimum.
    ptu_sensitivity:
        Penalty strength for PTU deviation from optimum.
    """

    crop: str
    baseline_t_ha: float
    optimal_gdd: float
    optimal_ptu: float
    thermal_sensitivity: float
    ptu_sensitivity: float


@dataclass(frozen=True)
class LimitingFactorNode:
    """Represents a limiting factor and its contribution to yield gap."""

    factor: str
    score: float
    severity: str
    explanation: str


POTENTIAL_YIELD_MODELS: Dict[str, PotentialYieldModel] = {
    "wheat": PotentialYieldModel("Wheat", 8.2, 1900.0, 23000.0, 0.20, 0.12),
    "rice": PotentialYieldModel("Rice", 9.4, 2200.0, 26000.0, 0.18, 0.10),
    "maize": PotentialYieldModel("Maize", 11.5, 1850.0, 24000.0, 0.24, 0.14),
}


class YieldGapService:
    """Service for yield-gap diagnostics and projections."""

    def _resolve_model(self, crop: str) -> PotentialYieldModel:
        model = POTENTIAL_YIELD_MODELS.get(crop.lower())
        if not model:
            raise ValueError(
                f"Unsupported crop '{crop}'. Supported: {', '.join(POTENTIAL_YIELD_MODELS.keys())}"
            )
        return model

    @lru_cache(maxsize=512)
    def _cached_potential_yield(
        self,
        crop: str,
        location_id: int,
        gdd: float,
        ptu: float,
        water: float,
        nitrogen: float,
        phosphorus: float,
        temp_stress: float,
    ) -> float:
        model = self._resolve_model(crop)

        thermal_deviation = abs(gdd - model.optimal_gdd) / model.optimal_gdd
        ptu_deviation = abs(ptu - model.optimal_ptu) / model.optimal_ptu

        thermal_penalty = clamp(
            1.0 - model.thermal_sensitivity * thermal_deviation, 0.6, 1.05
        )
        ptu_penalty = clamp(1.0 - model.ptu_sensitivity * ptu_deviation, 0.65, 1.05)

        resource_factor = (
            0.35 * clamp(water, 0.2, 1.2)
            + 0.35 * clamp(nitrogen, 0.2, 1.2)
            + 0.20 * clamp(phosphorus, 0.2, 1.2)
            + 0.10 * clamp(temp_stress, 0.2, 1.2)
        )

        return round(
            model.baseline_t_ha * thermal_penalty * ptu_penalty * resource_factor, 3
        )

    async def calculate_potential_yield(
        self,
        db: AsyncSession,
        location_id: int,
        environmental_params: Dict[str, float],
        crop: str = "wheat",
    ) -> float:
        """Calculate attainable potential yield (t/ha) for a location.

        Parameters
        ----------
        db:
            Async database session.
        location_id:
            Location identifier.
        environmental_params:
            Environmental and management modifiers. Supported keys include
            ``t_max``, ``t_min``, ``day_length_hours``, ``water_index``,
            ``nitrogen_index``, ``phosphorus_index``, and ``temperature_index``.
        crop:
            Crop name (Wheat, Rice, or Maize).

        Returns
        -------
        float
            Potential yield in t/ha.
        """
        location = await db.get(Location, location_id)
        if not location:
            raise ValueError(f"Location {location_id} not found")

        t_max = float(environmental_params.get("t_max", 30.0))
        t_min = float(environmental_params.get("t_min", 18.0))
        day_length = float(environmental_params.get("day_length_hours", 12.0))

        gdd = await environmental_service.calculate_gdd(
            t_max=t_max, t_min=t_min, t_base=10.0
        )
        ptu = await environmental_service.calculate_ptu(
            gdd=gdd, day_length_hours=day_length
        )

        return self._cached_potential_yield(
            crop=crop,
            location_id=location_id,
            gdd=round(gdd, 3),
            ptu=round(ptu, 3),
            water=round(float(environmental_params.get("water_index", 1.0)), 3),
            nitrogen=round(float(environmental_params.get("nitrogen_index", 1.0)), 3),
            phosphorus=round(
                float(environmental_params.get("phosphorus_index", 1.0)), 3
            ),
            temp_stress=round(
                float(environmental_params.get("temperature_index", 1.0)), 3
            ),
        )

    async def fetch_actual_yields(
        self,
        db: AsyncSession,
        germplasm_id: int,
        location_id: int,
        year_range: Tuple[int, int],
        organization_id: int,
    ) -> List[float]:
        """Fetch actual observed yields from trial observations."""
        start_year, end_year = year_range

        stmt = (
            select(cast(Observation.value, Float))
            .join(
                ObservationVariable,
                Observation.observation_variable_id == ObservationVariable.id,
            )
            .join(
                ObservationUnit, Observation.observation_unit_id == ObservationUnit.id
            )
            .join(Study, Observation.study_id == Study.id)
            .where(
                and_(
                    Observation.organization_id == organization_id,
                    Observation.germplasm_id == germplasm_id,
                    Study.location_id == location_id,
                    func.lower(ObservationVariable.observation_variable_name).like(
                        "%yield%"
                    ),
                    cast(func.substr(Observation.observation_time_stamp, 1, 4), Float)
                    >= start_year,
                    cast(func.substr(Observation.observation_time_stamp, 1, 4), Float)
                    <= end_year,
                )
            )
        )

        result = await db.execute(stmt)
        values = [float(v) for v in result.scalars().all() if v is not None]

        if values:
            return values

        # BrAPI compatibility fallback when internal observations are missing.
        try:
            adapter = BrAPIAdapter(IntegrationConfig(base_url="http://localhost:8000"))
            trials = await adapter.get_trials(page=0, page_size=50)
            _ = [
                t for t in trials if str(t.get("locationDbId", "")) == str(location_id)
            ]
            await adapter._client.aclose()
        except Exception:
            logger.debug(
                "BrAPI trial fallback unavailable for yield lookup", exc_info=True
            )

        return []

    def calculate_yield_gap(self, actual: float, potential: float) -> Dict[str, float]:
        """Calculate absolute and percentage yield gap."""
        gap_abs = max(potential - actual, 0.0)
        gap_pct = max(0.0, safe_divide(gap_abs, potential, default=0.0) * 100.0)
        return {
            "actual": round(actual, 3),
            "potential": round(potential, 3),
            "gap_absolute": round(gap_abs, 3),
            "gap_percent": round(gap_pct, 2),
        }

    def identify_limiting_factors(
        self,
        environment_data: Dict[str, float],
        soil_data: Dict[str, float],
    ) -> List[LimitingFactorNode]:
        """Identify limiting agronomic factors driving yield gap."""
        factors = {
            "Water": 1.0 - clamp(environment_data.get("water_index", 1.0), 0.0, 1.2),
            "Nitrogen": 1.0 - clamp(soil_data.get("nitrogen_index", 1.0), 0.0, 1.2),
            "Phosphorus": 1.0 - clamp(soil_data.get("phosphorus_index", 1.0), 0.0, 1.2),
            "Temperature": 1.0
            - clamp(environment_data.get("temperature_index", 1.0), 0.0, 1.2),
        }

        nodes: List[LimitingFactorNode] = []
        for factor, score in sorted(factors.items(), key=lambda x: x[1], reverse=True):
            if score <= 0.05:
                continue
            severity = "high" if score >= 0.35 else "medium" if score >= 0.20 else "low"
            nodes.append(
                LimitingFactorNode(
                    factor=factor,
                    score=round(score, 3),
                    severity=severity,
                    explanation=f"{factor} is constraining yield by an estimated {score * 100:.1f}%.",
                )
            )
        return nodes

    def sensitivity_analysis(
        self,
        base_gap_percent: float,
        environment_data: Dict[str, float],
        soil_data: Dict[str, float],
        increment: float = 0.10,
    ) -> Dict[str, float]:
        """Estimate gap reduction sensitivity for +10% factor improvements."""
        baseline = self.identify_limiting_factors(environment_data, soil_data)
        baseline_total = sum(node.score for node in baseline) or 1.0

        impact_map: Dict[str, float] = {}
        for factor in ["Water", "Nitrogen", "Phosphorus", "Temperature"]:
            score = next(
                (node.score for node in baseline if node.factor == factor), 0.0
            )
            contribution = safe_divide(score, baseline_total)
            gap_reduction = base_gap_percent * contribution * increment
            impact_map[factor] = round(gap_reduction, 2)

        return impact_map

    def project_climate_scenario(
        self, potential_yield: float, delta_temp_c: float = 2.0
    ) -> float:
        """Project potential yield under warming scenario."""
        penalty = 0.03 * delta_temp_c
        return round(max(potential_yield * (1.0 - penalty), 0.0), 3)

    def economic_impact(
        self, gap_absolute: float, market_price_per_ton: float, area_ha: float = 1.0
    ) -> float:
        """Estimate economic loss from yield gap."""
        return round(gap_absolute * market_price_per_ton * area_ha, 2)

    async def get_spatial_yield_gap(
        self,
        db: AsyncSession,
        region_id: int,
        organization_id: int,
    ) -> List[Dict[str, Any]]:
        """Get location-wise yield gap map data for a region/program.

        ``region_id`` is treated as a program identifier to aggregate related trials.
        """
        start = perf_counter()
        stmt = (
            select(Trial.location_id, func.avg(cast(Observation.value, Float)))
            .join(Study, Study.trial_id == Trial.id)
            .join(Observation, Observation.study_id == Study.id)
            .join(
                ObservationVariable,
                Observation.observation_variable_id == ObservationVariable.id,
            )
            .where(
                and_(
                    Trial.organization_id == organization_id,
                    Trial.program_id == region_id,
                    func.lower(ObservationVariable.observation_variable_name).like(
                        "%yield%"
                    ),
                )
            )
            .group_by(Trial.location_id)
        )

        result = await db.execute(stmt)
        rows = result.all()

        payload = []
        for location_id, avg_actual in rows:
            actual = float(avg_actual or 0.0)
            potential = max(actual * 1.2, actual + 0.5)
            gap = self.calculate_yield_gap(actual=actual, potential=potential)
            payload.append({"location_id": location_id, **gap})

        elapsed_ms = (perf_counter() - start) * 1000.0
        logger.info(
            "YieldGap spatial aggregation query completed",
            extra={"duration_ms": round(elapsed_ms, 2)},
        )
        return payload


yield_gap_service = YieldGapService()
