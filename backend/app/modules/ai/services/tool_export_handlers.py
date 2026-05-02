from dataclasses import dataclass
from typing import Any

from app.modules.core.services.data_export_service import get_export_service


@dataclass(frozen=True)
class ExportHandlerSharedContext:
    observation_search_service: Any
    seedlot_search_service: Any
    program_search_service: Any
    trait_search_service: Any


async def handle_export(
    executor: Any,
    function_name: str,
    params: dict[str, Any],
    *,
    shared: ExportHandlerSharedContext,
    logger: Any,
) -> dict[str, Any]:
    """Handle export_* functions via a dedicated sibling module."""
    if function_name == "export_data":
        org_id = params.get("organization_id", 1)
        data_type = params.get("data_type", "germplasm").lower()
        format_str = params.get("format", "csv").lower()
        query = params.get("query")
        limit = params.get("limit", 100)

        try:
            export_service = get_export_service()
            data: list[dict[str, Any]] = []

            if data_type == "germplasm":
                data = await executor.germplasm_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=query,
                    limit=limit,
                )
            elif data_type == "trials":
                data = await executor.trial_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=query,
                    limit=limit,
                )
            elif data_type == "observations":
                data = await shared.observation_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=query,
                    limit=limit,
                )
            elif data_type == "crosses":
                data = await executor.cross_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=query,
                    limit=limit,
                )
            elif data_type == "locations":
                data = await executor.location_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=query,
                    limit=limit,
                )
            elif data_type == "seedlots":
                data = await shared.seedlot_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=query,
                    limit=limit,
                )
            elif data_type == "traits":
                data = await shared.trait_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=query,
                    limit=limit,
                )
            elif data_type == "programs":
                data = await shared.program_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    query=query,
                    limit=limit,
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown data type: {data_type}",
                    "message": "Supported types: germplasm, trials, observations, crosses, locations, seedlots, traits, programs",
                }

            if not data:
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "data_exported",
                    "data": {
                        "data_type": data_type,
                        "format": format_str,
                        "record_count": 0,
                        "content": "",
                        "message": f"No {data_type} data found to export",
                    },
                    "demo": False,
                }

            if format_str == "csv":
                content = export_service.export_to_csv(data)
            elif format_str == "tsv":
                content = export_service.export_to_tsv(data)
            elif format_str == "json":
                content = export_service.export_to_json(data)
            else:
                content = export_service.export_to_csv(data)
                format_str = "csv"

            return {
                "success": True,
                "function": function_name,
                "result_type": "data_exported",
                "data": {
                    "data_type": data_type,
                    "format": format_str,
                    "record_count": len(data),
                    "content_preview": content[:500] + "..." if len(content) > 500 else content,
                    "content_length": len(content),
                    "message": f"Exported {len(data)} {data_type} records in {format_str.upper()} format",
                },
                "demo": False,
            }
        except Exception as error:
            logger.error("Export data failed: %s", error)
            return {
                "success": False,
                "error": str(error),
                "message": "Failed to export data",
            }

    return {"success": False, "error": f"Unhandled export function: {function_name}"}