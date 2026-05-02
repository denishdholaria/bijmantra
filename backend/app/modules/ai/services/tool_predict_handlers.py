"""Extracted predict-handler family for the REEVU function executor.

This module keeps predict-specific branching out of tools.py while preserving
the existing module-root seams used by the executor runtime and tests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class PredictHandlerSharedContext:
    observation_search_service: Any
    cross_domain_gdd_service_cls: Any


async def handle_predict(
    executor: Any,
    function_name: str,
    params: dict[str, Any],
    *,
    shared: PredictHandlerSharedContext,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Handle predict_* functions for FunctionExecutor."""

    observation_search_service = shared.observation_search_service
    CrossDomainGDDService = shared.cross_domain_gdd_service_cls

    if function_name == "predict_cross":
        org_id = params.get("organization_id", 1)
        parent1_id = params.get("parent1_id")
        parent2_id = params.get("parent2_id")
        trait = params.get("trait")
        heritability = params.get("heritability", 0.3)

        if not parent1_id or not parent2_id:
            return {
                "success": False,
                "error": "parent1_id and parent2_id are required",
                "message": "Please specify both parent IDs for cross prediction",
            }

        try:
            parent1 = await executor.germplasm_search_service.get_by_id(
                db=executor.db,
                organization_id=org_id,
                germplasm_id=str(parent1_id),
            )
            parent2 = await executor.germplasm_search_service.get_by_id(
                db=executor.db,
                organization_id=org_id,
                germplasm_id=str(parent2_id),
            )

            if not parent1 or not parent2:
                missing = []
                if not parent1:
                    missing.append(f"parent1 ({parent1_id})")
                if not parent2:
                    missing.append(f"parent2 ({parent2_id})")
                return {
                    "success": False,
                    "error": "Parent(s) not found",
                    "message": f"Could not find: {', '.join(missing)}",
                }

            parent1_obs = await observation_search_service.get_by_germplasm(
                db=executor.db,
                organization_id=org_id,
                germplasm_id=int(parent1_id),
                limit=50,
            )
            parent2_obs = await observation_search_service.get_by_germplasm(
                db=executor.db,
                organization_id=org_id,
                germplasm_id=int(parent2_id),
                limit=50,
            )

            def calc_mean(observations: list[dict[str, Any]], trait_filter: str | None = None) -> float:
                values: list[float] = []
                for observation in observations:
                    if trait_filter and observation.get("trait", {}).get("name", "").lower() != trait_filter.lower():
                        continue
                    try:
                        values.append(float(observation.get("value", 0)))
                    except (ValueError, TypeError):
                        continue
                return sum(values) / len(values) if values else 0

            parent1_mean = calc_mean(parent1_obs, trait)
            parent2_mean = calc_mean(parent2_obs, trait)

            all_obs = await observation_search_service.search(
                db=executor.db,
                organization_id=org_id,
                trait=trait,
                limit=200,
            )
            trait_mean = calc_mean(all_obs)

            parent1_ebv = (parent1_mean - trait_mean) * heritability if trait_mean else 0
            parent2_ebv = (parent2_mean - trait_mean) * heritability if trait_mean else 0

            prediction = executor.breeding_value_service.predict_cross(
                parent1_ebv=parent1_ebv,
                parent2_ebv=parent2_ebv,
                trait_mean=trait_mean,
                heritability=heritability,
            )

            return {
                "success": True,
                "function": function_name,
                "result_type": "cross_prediction",
                "data": {
                    "parent1": {
                        "id": parent1_id,
                        "name": parent1.get("name"),
                        "mean_phenotype": round(parent1_mean, 4) if parent1_mean else None,
                        "estimated_ebv": round(parent1_ebv, 4),
                        "observation_count": len(parent1_obs),
                    },
                    "parent2": {
                        "id": parent2_id,
                        "name": parent2.get("name"),
                        "mean_phenotype": round(parent2_mean, 4) if parent2_mean else None,
                        "estimated_ebv": round(parent2_ebv, 4),
                        "observation_count": len(parent2_obs),
                    },
                    "trait": trait or "all traits",
                    "trait_mean": round(trait_mean, 4) if trait_mean else None,
                    "heritability": heritability,
                    "prediction": prediction,
                    "message": f"Cross prediction: {parent1.get('name')} × {parent2.get('name')}",
                },
                "demo": False,
            }
        except Exception as exc:
            logger.error(f"Predict cross failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "message": "Failed to predict cross outcome",
            }

    if function_name == "predict_harvest_timing":
        field_id = params.get("field_id")
        planting_date = params.get("planting_date")
        crop_name = params.get("crop_name")
        try:
            gdd_service = CrossDomainGDDService(executor.db)
            planting_date_obj = datetime.strptime(planting_date, "%Y-%m-%d").date()
            harvest_timing = gdd_service.predict_harvest_timing(field_id, planting_date_obj, crop_name)
            harvest_timing_with_message = {
                **harvest_timing,
                "message": f"Predicted harvest timing for {crop_name} planted on {planting_date}.",
            }
            return {
                "success": True,
                "function": function_name,
                "result_type": "harvest_timing_prediction",
                "data": harvest_timing_with_message,
            }
        except Exception as exc:
            logger.error("Predict harvest timing failed: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "message": "Failed to predict harvest timing",
            }

    return {"success": False, "error": f"Unhandled predict function: {function_name}"}