"""
REEVU What-If & Predictive Query Handler

Handles three types of hypothetical queries:
- cross_prediction: "what if I crossed IR64 with Swarna?"
- selection_scenario: "what if I select the top 10%?"
- environmental_scenario: "what if rainfall drops 20%?"

All results carry is_prediction=True, explicit assumptions, and limitations
so the LLM can clearly label them as predictions, not observations.
"""

from __future__ import annotations

import logging
import math
import re
import statistics as _stats
from dataclasses import dataclass, field
from typing import Any

from app.schemas.reevu_envelope import EvidenceRef

logger = logging.getLogger(__name__)

# ── What-if phrase sets ───────────────────────────────────────────────────────

WHAT_IF_PHRASES: tuple[str, ...] = (
    "what if", "what would happen", "what happens when",
    "simulate", "predict", "scenario", "hypothetical",
    "if i cross", "if i select", "if drought", "if rainfall",
    "if temperature", "if i advance",
)

_CROSS_TERMS: tuple[str, ...] = (
    "cross", "crossed", "crossing", "parent", "hybrid", "mate",
)
_SELECTION_TERMS: tuple[str, ...] = (
    "select", "selection", "advance", "top", "best", "truncat",
    "percent", "%", "entries",
)
_ENVIRONMENTAL_TERMS: tuple[str, ...] = (
    "rainfall", "rain", "drought", "temperature", "heat", "flood",
    "climate", "weather", "water", "irrigation",
)

# Rainfall sensitivity: approximate % yield loss per % rainfall reduction
# (simplified linear model — real models are crop/region specific)
_RAINFALL_SENSITIVITY: dict[str, float] = {
    "wheat": 0.5,
    "rice": 0.6,
    "maize": 0.55,
    "corn": 0.55,
    "sorghum": 0.35,
    "default": 0.5,
}
_TEMPERATURE_SENSITIVITY: dict[str, float] = {
    "wheat": -0.06,   # % yield change per +1°C
    "rice": -0.05,
    "maize": -0.07,
    "default": -0.06,
}


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class WhatIfResult:
    """Result of a what-if predictive query."""

    query_type: str
    prediction: dict[str, Any]
    confidence: float
    assumptions: list[str]
    limitations: list[str]
    insufficient_data: bool
    reason: str | None
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    is_prediction: bool = True          # always True — label for LLM prompt


# ── Handler ───────────────────────────────────────────────────────────────────

class WhatIfQueryHandler:
    """Dispatch what-if queries to the appropriate prediction handler.

    Usage:
        handler = WhatIfQueryHandler()
        result = await handler.handle(query_type, params, db, organization_id, ...)
    """

    # ── Public API ────────────────────────────────────────────────────────────

    async def handle(
        self,
        query_type: str,
        params: dict[str, Any],
        db: Any,
        organization_id: int,
        germplasm_search_service: Any = None,
        observation_search_service: Any = None,
    ) -> WhatIfResult:
        """Dispatch to the appropriate what-if handler."""
        if query_type == "cross_prediction":
            return await self._handle_cross_prediction(
                params, db, organization_id,
                germplasm_search_service=germplasm_search_service,
            )
        if query_type == "selection_scenario":
            return await self._handle_selection_scenario(
                params, db, organization_id,
                observation_search_service=observation_search_service,
            )
        if query_type == "environmental_scenario":
            return await self._handle_environmental_scenario(
                params, db, organization_id,
            )
        return WhatIfResult(
            query_type=query_type,
            prediction={},
            confidence=0.0,
            assumptions=[],
            limitations=[],
            insufficient_data=True,
            reason=f"Unknown what-if query type: '{query_type}'",
        )

    # ── Detection helpers ─────────────────────────────────────────────────────

    def _classify_what_if(self, message: str) -> str:
        """Classify a what-if message into cross_prediction, selection_scenario,
        environmental_scenario, or unknown.

        Environmental terms are checked first to avoid "drops" (in "rainfall drops")
        matching the selection term "top" via substring collision.
        """
        msg = message.lower()
        # Environmental first — avoids "drops" matching "top" in selection terms
        if any(t in msg for t in _ENVIRONMENTAL_TERMS):
            return "environmental_scenario"
        if any(t in msg for t in _CROSS_TERMS):
            return "cross_prediction"
        if any(t in msg for t in _SELECTION_TERMS):
            return "selection_scenario"
        return "unknown"

    def _extract_what_if_params(
        self, message: str, what_if_type: str
    ) -> dict[str, Any]:
        """Extract structured parameters from a what-if message."""
        if what_if_type == "cross_prediction":
            return self._extract_cross_params(message)
        if what_if_type == "selection_scenario":
            return self._extract_selection_params(message)
        if what_if_type == "environmental_scenario":
            return self._extract_environmental_params(message)
        return {}

    # ── Cross prediction ──────────────────────────────────────────────────────

    async def _handle_cross_prediction(
        self,
        params: dict[str, Any],
        db: Any,
        organization_id: int,
        germplasm_search_service: Any = None,
    ) -> WhatIfResult:
        """Predict progeny performance for a cross between two parents.

        Uses mid-parent value (additive model) when full genotype data is
        unavailable. Returns insufficient_data when parents cannot be resolved.
        """
        parent1_name = params.get("parent1") or params.get("parents", [None, None])[0]
        parent2_name = params.get("parent2") or (params.get("parents", [None, None]) + [None])[1]

        if not parent1_name or not parent2_name:
            return WhatIfResult(
                query_type="cross_prediction",
                prediction={},
                confidence=0.0,
                assumptions=[],
                limitations=[],
                insufficient_data=True,
                reason="Two parent names are required for cross prediction",
            )

        # Resolve parents via germplasm search
        parent1 = parent2 = None
        if germplasm_search_service:
            try:
                p1_results = await germplasm_search_service.search(
                    db=db, organization_id=organization_id,
                    query=str(parent1_name), limit=1,
                )
                p2_results = await germplasm_search_service.search(
                    db=db, organization_id=organization_id,
                    query=str(parent2_name), limit=1,
                )
                parent1 = p1_results[0] if p1_results else None
                parent2 = p2_results[0] if p2_results else None
            except Exception as exc:
                logger.warning("Cross prediction germplasm lookup failed: %s", exc)

        if parent1 is None or parent2 is None:
            return WhatIfResult(
                query_type="cross_prediction",
                prediction={},
                confidence=0.0,
                assumptions=[],
                limitations=[],
                insufficient_data=True,
                reason=f"Could not resolve parent germplasm: "
                       f"'{parent1_name}' and/or '{parent2_name}'",
            )

        # Mid-parent value prediction (additive model)
        gebv1 = float(parent1.get("gebv") or parent1.get("mean_value") or 0.5)
        gebv2 = float(parent2.get("gebv") or parent2.get("mean_value") or 0.5)
        predicted_mean = (gebv1 + gebv2) / 2.0
        predicted_variance = abs(gebv1 - gebv2) * 0.25  # simplified estimate

        # Inbreeding estimate: 0 for unrelated parents (simplified)
        inbreeding_coefficient = 0.0

        return WhatIfResult(
            query_type="cross_prediction",
            prediction={
                "parent1": parent1.get("germplasm_name") or str(parent1_name),
                "parent2": parent2.get("germplasm_name") or str(parent2_name),
                "predicted_mean": predicted_mean,
                "predicted_variance": predicted_variance,
                "inbreeding_coefficient": inbreeding_coefficient,
                "model": "mid_parent_value",
            },
            confidence=0.65,
            assumptions=[
                "Additive genetic model assumed (no epistasis)",
                "Mid-parent value used as progeny mean estimate",
                "Parental GEBVs used as performance proxies",
            ],
            limitations=[
                "Prediction accuracy depends on training data size",
                "Dominance and epistatic effects not modeled",
                "Inbreeding coefficient estimated as 0 (pedigree data unavailable)",
            ],
            insufficient_data=False,
            reason=None,
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id=f"cross_prediction:{parent1.get('id')}x{parent2.get('id')}",
                    query_or_method="what_if_handler.cross_prediction.mid_parent_value",
                )
            ],
        )

    # ── Selection scenario ────────────────────────────────────────────────────

    async def _handle_selection_scenario(
        self,
        params: dict[str, Any],
        db: Any,
        organization_id: int,
        observation_search_service: Any = None,
    ) -> WhatIfResult:
        """Simulate truncation selection at a given intensity.

        Computes: selected set, expected genetic gain, diversity impact.
        """
        intensity = float(params.get("selection_intensity") or 0.20)
        top_n = params.get("top_n")
        trait = params.get("trait") or "yield"

        # Fetch observations
        observations: list[dict[str, Any]] = []
        if observation_search_service:
            try:
                observations = await observation_search_service.search(
                    db=db, organization_id=organization_id,
                    query=trait, trait=trait, limit=200,
                )
            except Exception as exc:
                logger.warning("Selection scenario observation fetch failed: %s", exc)

        if not observations:
            return WhatIfResult(
                query_type="selection_scenario",
                prediction={},
                confidence=0.0,
                assumptions=[],
                limitations=[],
                insufficient_data=True,
                reason=f"No observations available for trait '{trait}'",
            )

        # Parse numeric values per germplasm
        germplasm_values: dict[str, list[float]] = {}
        for obs in observations:
            gid = str(obs.get("germplasm_id") or obs.get("germplasm_name") or "unknown")
            try:
                val = float(obs.get("value", ""))
                germplasm_values.setdefault(gid, []).append(val)
            except (TypeError, ValueError):
                continue

        if not germplasm_values:
            return WhatIfResult(
                query_type="selection_scenario",
                prediction={},
                confidence=0.0,
                assumptions=[],
                limitations=[],
                insufficient_data=True,
                reason="No numeric observations available for selection simulation",
            )

        # Compute per-germplasm means
        germplasm_means = {
            gid: _stats.mean(vals)
            for gid, vals in germplasm_values.items()
        }
        n_total = len(germplasm_means)
        all_means = list(germplasm_means.values())
        population_mean = _stats.mean(all_means)

        # Determine number to select
        if top_n is not None:
            n_select = max(1, int(top_n))
        else:
            n_select = max(1, round(n_total * intensity))

        # Truncation selection: take top n_select by mean
        sorted_entries = sorted(germplasm_means.items(), key=lambda x: x[1], reverse=True)
        selected = sorted_entries[:n_select]
        selected_mean = _stats.mean(v for _, v in selected)

        # Expected genetic gain (simplified: selected mean - population mean)
        expected_gain = selected_mean - population_mean

        # Diversity impact: selection pressure and allelic richness reduction estimate
        selection_pressure = n_select / n_total
        allelic_richness_reduction = max(0.0, 1.0 - math.sqrt(selection_pressure))

        return WhatIfResult(
            query_type="selection_scenario",
            prediction={
                "n_total": n_total,
                "n_selected": n_select,
                "selection_intensity": intensity,
                "population_mean": population_mean,
                "selected_mean": selected_mean,
                "expected_gain": expected_gain,
                "selected_entries": [gid for gid, _ in selected],
                "diversity_impact": {
                    "selection_pressure": selection_pressure,
                    "allelic_richness_reduction_estimate": allelic_richness_reduction,
                },
            },
            confidence=0.70,
            assumptions=[
                "Truncation selection model applied",
                "Additive genetic effects assumed",
                "Heritability assumed to be 1.0 (upper bound for gain estimate)",
            ],
            limitations=[
                "Actual genetic gain depends on heritability and genetic variance",
                "Correlated responses in other traits not modeled",
                "Diversity impact is an approximation based on selection pressure",
            ],
            insufficient_data=False,
            reason=None,
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id=f"selection_scenario:trait={trait}:intensity={intensity}",
                    query_or_method="what_if_handler.selection_scenario.truncation",
                )
            ],
        )

    # ── Environmental scenario ────────────────────────────────────────────────

    async def _handle_environmental_scenario(
        self,
        params: dict[str, Any],
        db: Any,
        organization_id: int,
    ) -> WhatIfResult:
        """Predict yield under a modified environmental scenario.

        Uses a simplified linear sensitivity model when no calibrated
        simulation model is available for the crop/location.
        """
        factor = params.get("environmental_factor") or "rainfall"
        magnitude = params.get("magnitude")
        crop = (params.get("crop") or "default").lower()
        baseline_yield = params.get("baseline_yield")

        if baseline_yield is None:
            return WhatIfResult(
                query_type="environmental_scenario",
                prediction={},
                confidence=0.0,
                assumptions=[],
                limitations=[],
                insufficient_data=True,
                reason=(
                    f"No baseline yield available for crop '{crop}'. "
                    "Provide baseline_yield in params or ensure trial data is available."
                ),
            )

        try:
            baseline = float(baseline_yield)
            mag = float(magnitude) if magnitude is not None else 0.0
        except (TypeError, ValueError):
            return WhatIfResult(
                query_type="environmental_scenario",
                prediction={},
                confidence=0.0,
                assumptions=[],
                limitations=[],
                insufficient_data=True,
                reason="Invalid baseline_yield or magnitude parameter",
            )

        # Apply sensitivity model
        factor_lower = str(factor).lower()
        if "rain" in factor_lower or "water" in factor_lower or "irrigation" in factor_lower:
            sensitivity = _RAINFALL_SENSITIVITY.get(crop, _RAINFALL_SENSITIVITY["default"])
            # yield_change% = sensitivity * magnitude%
            yield_change_pct = sensitivity * mag
        elif "temp" in factor_lower or "heat" in factor_lower:
            sensitivity = _TEMPERATURE_SENSITIVITY.get(crop, _TEMPERATURE_SENSITIVITY["default"])
            # yield_change% = sensitivity * magnitude (°C)
            yield_change_pct = sensitivity * mag * 100.0
        else:
            # Generic: assume 0.5 sensitivity
            yield_change_pct = 0.5 * mag

        scenario_yield = baseline * (1.0 + yield_change_pct / 100.0)
        # Confidence interval: ±15% of scenario yield (simplified)
        ci_margin = abs(scenario_yield) * 0.15

        return WhatIfResult(
            query_type="environmental_scenario",
            prediction={
                "environmental_factor": factor,
                "magnitude": mag,
                "crop": crop,
                "baseline_yield": baseline,
                "scenario_yield": scenario_yield,
                "yield_change_percent": yield_change_pct,
                "ci_lower": scenario_yield - ci_margin,
                "ci_upper": scenario_yield + ci_margin,
                "model": "linear_sensitivity",
            },
            confidence=0.55,
            assumptions=[
                f"Linear response to {factor} assumed",
                f"Sensitivity coefficient: {sensitivity if 'sensitivity' in dir() else 0.5:.2f} "
                f"(% yield change per % {factor} change)",
                "Baseline yield used as reference point",
            ],
            limitations=[
                f"Model calibrated for generic {crop} — region-specific calibration recommended",
                "Non-linear stress responses not modeled",
                "Interaction effects between environmental factors not included",
                "Confidence interval is approximate (±15%)",
            ],
            insufficient_data=False,
            reason=None,
            evidence_refs=[
                EvidenceRef(
                    source_type="function",
                    entity_id=f"environmental_scenario:{factor}:{mag}:{crop}",
                    query_or_method="what_if_handler.environmental_scenario.linear_sensitivity",
                )
            ],
        )

    # ── Private extraction helpers ────────────────────────────────────────────

    @staticmethod
    def _extract_cross_params(message: str) -> dict[str, Any]:
        """Extract parent names from a cross prediction message."""
        # Try "crossed X with Y" or "cross X and Y" patterns
        patterns = [
            r"cross(?:ed)?\s+([A-Za-z0-9_\-]+)\s+(?:with|and|x)\s+([A-Za-z0-9_\-]+)",
            r"([A-Za-z0-9_\-]+)\s+(?:x|×)\s+([A-Za-z0-9_\-]+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, message, re.IGNORECASE)
            if m:
                return {"parent1": m.group(1), "parent2": m.group(2)}
        # Fallback: return empty parents
        return {"parent1": None, "parent2": None}

    @staticmethod
    def _extract_selection_params(message: str) -> dict[str, Any]:
        """Extract selection intensity or top N from a selection scenario message."""
        # "top 10%" or "top 10 percent"
        pct_match = re.search(r"top\s+(\d+(?:\.\d+)?)\s*%", message, re.IGNORECASE)
        if pct_match:
            return {"selection_intensity": float(pct_match.group(1)) / 100.0}

        pct_word = re.search(r"top\s+(\d+(?:\.\d+)?)\s+percent", message, re.IGNORECASE)
        if pct_word:
            return {"selection_intensity": float(pct_word.group(1)) / 100.0}

        # "top N entries" or "top N"
        n_match = re.search(r"top\s+(\d+)\s+(?:entries|lines|varieties|germplasm)?", message, re.IGNORECASE)
        if n_match:
            n = int(n_match.group(1))
            # If small number, treat as count; if large, treat as percentage
            if n <= 100:
                return {"top_n": n}

        return {"selection_intensity": 0.20}  # default 20%

    @staticmethod
    def _extract_environmental_params(message: str) -> dict[str, Any]:
        """Extract environmental factor and magnitude from message."""
        params: dict[str, Any] = {}

        # Detect factor
        if any(t in message.lower() for t in ("rain", "rainfall", "precipitation")):
            params["environmental_factor"] = "rainfall"
        elif any(t in message.lower() for t in ("temperature", "heat", "temp")):
            params["environmental_factor"] = "temperature"
        elif "drought" in message.lower():
            params["environmental_factor"] = "rainfall"
        else:
            params["environmental_factor"] = "rainfall"

        # Extract magnitude (e.g., "20%", "2 degrees", "30 percent")
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", message)
        if pct_match:
            val = float(pct_match.group(1))
            # Negative if "drop", "reduce", "less", "decrease", "drought"
            if any(t in message.lower() for t in ("drop", "reduc", "less", "decreas", "drought", "deficit")):
                val = -val
            params["magnitude"] = val
        else:
            deg_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:degree|°|celsius|fahrenheit)", message, re.IGNORECASE)
            if deg_match:
                val = float(deg_match.group(1))
                if any(t in message.lower() for t in ("drop", "cool", "decreas")):
                    val = -val
                params["magnitude"] = val
            else:
                params["magnitude"] = -20.0  # default: 20% reduction

        return params
