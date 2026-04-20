"""Extracted analyze-handler family for the REEVU function executor.

This module keeps analyze-specific branching out of tools.py while preserving
the existing runtime seams used by the executor and focused tests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.modules.breeding.services.gxe_analysis_service import get_gxe_service


@dataclass(slots=True)
class AnalyzeHandlerSharedContext:
    observation_search_service: Any
    cross_domain_gdd_service_cls: Any


def _build_variety_recommendation_message(recommendations: dict[str, Any], field_id: Any) -> str:
    recommendation_items = recommendations.get("recommendations")
    recommendation_count = len(recommendation_items) if isinstance(recommendation_items, list) else 0
    return f"Recommended {recommendation_count} varieties for field {field_id} based on GDD suitability."


def _build_planting_window_message(crop_name: Any, field_id: Any) -> str:
    normalized_crop = str(crop_name or "the requested crop").strip() or "the requested crop"
    return f"Analyzed planting windows for {normalized_crop} in field {field_id}."


async def handle_analyze(
    executor: Any,
    function_name: str,
    params: dict[str, Any],
    *,
    shared: AnalyzeHandlerSharedContext,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Handle analyze_* functions for FunctionExecutor."""

    observation_search_service = shared.observation_search_service
    CrossDomainGDDService = shared.cross_domain_gdd_service_cls

    if function_name == "recommend_varieties_by_gdd":
        field_id = params.get("field_id")
        try:
            gdd_service = CrossDomainGDDService(executor.db)
            recommendations = gdd_service.recommend_varieties(field_id)
            recommendations_with_message = {
                **recommendations,
                "message": _build_variety_recommendation_message(recommendations, field_id),
            }
            return {
                "success": True,
                "function": function_name,
                "result_type": "variety_recommendations",
                "data": recommendations_with_message,
            }
        except Exception as exc:
            logger.error("Recommend varieties by GDD failed: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "message": "Failed to recommend varieties by GDD",
            }

    if function_name == "analyze_planting_windows":
        field_id = params.get("field_id")
        crop_name = params.get("crop_name")
        try:
            gdd_service = CrossDomainGDDService(executor.db)
            planting_windows = gdd_service.analyze_planting_windows(field_id, crop_name)
            planting_windows_with_message = {
                **planting_windows,
                "message": _build_planting_window_message(crop_name, field_id),
            }
            return {
                "success": True,
                "function": function_name,
                "result_type": "planting_windows",
                "data": planting_windows_with_message,
            }
        except Exception as exc:
            logger.error("Analyze planting windows failed: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "message": "Failed to analyze planting windows",
            }

    if function_name == "analyze_gxe":
        org_id = params.get("organization_id", 1)
        trait = params.get("trait")
        method = params.get("method", "AMMI").upper()

        if not trait:
            return {
                "success": False,
                "error": "trait is required",
                "message": "Please specify a trait for G×E analysis",
            }

        try:
            observations = await observation_search_service.search(
                db=executor.db,
                organization_id=org_id,
                trait=trait,
                limit=1000,
            )

            if len(observations) < 6:
                return {
                    "success": False,
                    "error": "Insufficient data",
                    "message": f"Need at least 6 observations for G×E analysis. Found {len(observations)} for trait '{trait}'",
                }

            geno_env_data: dict[tuple[Any, Any], list[float]] = {}
            genotypes: set[Any] = set()
            environments: set[Any] = set()
            geno_names: dict[Any, str] = {}
            env_names: dict[Any, str] = {}

            for observation in observations:
                try:
                    value = float(observation.get("value", 0))
                    germplasm = observation.get("germplasm", {})
                    genotype_id = germplasm.get("id")
                    genotype_name = germplasm.get("name", f"G{genotype_id}")

                    study = observation.get("study", {})
                    environment_id = study.get("id") if study else observation.get("location_id", "unknown")
                    environment_name = study.get("name") if study else f"Env{environment_id}"

                    if genotype_id and environment_id:
                        key = (genotype_id, environment_id)
                        if key not in geno_env_data:
                            geno_env_data[key] = []
                        geno_env_data[key].append(value)
                        genotypes.add(genotype_id)
                        environments.add(environment_id)
                        geno_names[genotype_id] = genotype_name
                        env_names[environment_id] = environment_name
                except (ValueError, TypeError):
                    continue

            if len(genotypes) < 2 or len(environments) < 2:
                return {
                    "success": False,
                    "error": "Insufficient variation",
                    "message": f"Need at least 2 genotypes and 2 environments. Found {len(genotypes)} genotypes, {len(environments)} environments.",
                }

            genotype_list = sorted(genotypes)
            environment_list = sorted(environments)
            yield_matrix = np.zeros((len(genotype_list), len(environment_list)))

            for row_index, genotype_id in enumerate(genotype_list):
                for column_index, environment_id in enumerate(environment_list):
                    key = (genotype_id, environment_id)
                    if key in geno_env_data and geno_env_data[key]:
                        yield_matrix[row_index, column_index] = np.mean(geno_env_data[key])
                    else:
                        genotype_values = [
                            value
                            for key_tuple, values in geno_env_data.items()
                            if key_tuple[0] == genotype_id
                            for value in values
                        ]
                        yield_matrix[row_index, column_index] = np.mean(genotype_values) if genotype_values else 0

            genotype_name_list = [geno_names.get(genotype_id, f"G{genotype_id}") for genotype_id in genotype_list]
            environment_name_list = [
                env_names.get(environment_id, f"E{environment_id}")
                for environment_id in environment_list
            ]

            gxe_service = get_gxe_service()

            if method == "GGE":
                result = gxe_service.gge_biplot(
                    yield_matrix=yield_matrix,
                    genotype_names=genotype_name_list,
                    environment_names=environment_name_list,
                )
                result_dict = result.to_dict()
                result_dict["winning_genotypes"] = gxe_service.identify_winning_genotypes(result)
            elif method in {"FINLAY_WILKINSON", "FW"}:
                result = gxe_service.finlay_wilkinson(
                    yield_matrix=yield_matrix,
                    genotype_names=genotype_name_list,
                    environment_names=environment_name_list,
                )
                result_dict = result.to_dict()
            else:
                result = gxe_service.ammi_analysis(
                    yield_matrix=yield_matrix,
                    genotype_names=genotype_name_list,
                    environment_names=environment_name_list,
                )
                result_dict = result.to_dict()

            return {
                "success": True,
                "function": function_name,
                "result_type": "gxe_analysis",
                "data": {
                    "method": method,
                    "trait": trait,
                    "n_genotypes": len(genotype_list),
                    "n_environments": len(environment_list),
                    "n_observations": len(observations),
                    "analysis": result_dict,
                    "message": f"{method} analysis: {len(genotype_list)} genotypes × {len(environment_list)} environments for trait '{trait}'",
                },
                "demo": False,
            }
        except Exception as exc:
            logger.error(f"Analyze G×E failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
                "message": "Failed to perform G×E analysis",
            }

    return {"success": False, "error": f"Unhandled analyze function: {function_name}"}