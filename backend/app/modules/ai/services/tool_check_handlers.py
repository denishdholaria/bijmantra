from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CheckHandlerSharedContext:
    seedlot_search_service: Any


async def handle_check(
    executor: Any,
    function_name: str,
    params: dict[str, Any],
    *,
    shared: CheckHandlerSharedContext,
    logger: Any,
) -> dict[str, Any]:
    """Handle check_* functions via a dedicated sibling module."""
    if function_name == "check_seed_viability":
        org_id = params.get("organization_id", 1)
        seedlot_id = params.get("seedlot_id") or params.get("accession_id")
        germplasm_id = params.get("germplasm_id")

        try:
            if germplasm_id and not seedlot_id:
                seedlots = await shared.seedlot_search_service.get_by_germplasm(
                    db=executor.db,
                    organization_id=org_id,
                    germplasm_id=int(germplasm_id),
                    limit=5,
                )

                if not seedlots:
                    return {
                        "success": False,
                        "error": "No seedlots found",
                        "message": f"No seedlots found for germplasm ID {germplasm_id}",
                    }

                viability_results = []
                for seedlot in seedlots:
                    result = await shared.seedlot_search_service.check_viability(
                        db=executor.db,
                        organization_id=org_id,
                        seedlot_id=seedlot["id"],
                    )
                    viability_results.append(result)

                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "viability_results",
                    "data": {
                        "seedlot_count": len(viability_results),
                        "results": viability_results,
                        "message": f"Checked viability for {len(viability_results)} seedlots",
                    },
                    "demo": False,
                }

            if not seedlot_id:
                return {
                    "success": False,
                    "error": "seedlot_id or germplasm_id required",
                    "message": "Please specify a seedlot ID or germplasm ID",
                }

            result = await shared.seedlot_search_service.check_viability(
                db=executor.db,
                organization_id=org_id,
                seedlot_id=str(seedlot_id),
            )
            result_with_message = {
                **result,
                "message": f"Checked viability for seedlot {seedlot_id}",
            }

            return {
                "success": True,
                "function": function_name,
                "result_type": "viability_result",
                "data": result_with_message,
                "demo": False,
            }
        except Exception as error:
            logger.error("Check seed viability failed: %s", error)
            return {
                "success": False,
                "error": str(error),
                "message": "Failed to check seed viability",
            }

    return {"success": False, "error": f"Unhandled check function: {function_name}"}