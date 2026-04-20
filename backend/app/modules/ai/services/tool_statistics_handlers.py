from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StatisticsHandlerSharedContext:
    observation_search_service: Any
    seedlot_search_service: Any
    program_search_service: Any
    trait_search_service: Any


async def handle_statistics(
    executor: Any,
    params: dict[str, Any],
    *,
    shared: StatisticsHandlerSharedContext,
    logger: Any,
) -> dict[str, Any]:
    """Get cross-domain statistics from database-backed services."""
    org_id = params.get("organization_id", 1)

    try:
        germplasm_stats = await executor.germplasm_search_service.get_statistics(
            db=executor.db,
            organization_id=org_id,
        )

        trial_stats = await executor.trial_search_service.get_statistics(
            db=executor.db,
            organization_id=org_id,
        )

        observation_stats = await shared.observation_search_service.get_statistics(
            db=executor.db,
            organization_id=org_id,
        )

        cross_stats = await executor.cross_search_service.get_statistics(
            db=executor.db,
            organization_id=org_id,
        )

        location_stats = await executor.location_search_service.get_statistics(
            db=executor.db,
            organization_id=org_id,
        )

        seedlot_stats = await shared.seedlot_search_service.get_statistics(
            db=executor.db,
            organization_id=org_id,
        )

        program_stats = await shared.program_search_service.get_statistics(
            db=executor.db,
            organization_id=org_id,
        )

        trait_stats = await shared.trait_search_service.get_statistics(
            db=executor.db,
            organization_id=org_id,
        )

        return {
            "success": True,
            "function": "get_statistics",
            "result_type": "statistics",
            "calculation_ids": ["fn:get_statistics"],
            "data": {
                "programs": program_stats,
                "germplasm": germplasm_stats,
                "trials": trial_stats,
                "observations": observation_stats,
                "crosses": cross_stats,
                "locations": location_stats,
                "seedlots": seedlot_stats,
                "traits": trait_stats,
                "message": (
                    f"Database contains {program_stats.get('total_programs', 0)} programs, "
                    f"{germplasm_stats.get('total_germplasm', 0)} germplasm, "
                    f"{trial_stats.get('total_trials', 0)} trials, "
                    f"{observation_stats.get('total_observations', 0)} observations, "
                    f"{seedlot_stats.get('total_seedlots', 0)} seedlots, "
                    f"{trait_stats.get('total_traits', 0)} traits"
                ),
            },
            "demo": False,
        }
    except Exception as error:
        logger.error("Get statistics failed: %s", error)
        return {
            "success": False,
            "error": str(error),
            "message": "Failed to get database statistics",
        }