from dataclasses import dataclass
from typing import Any


SEARCH_RESULT_LIMIT = 20
ACCESSION_LOCATION_LOOKUP_LIMIT = 100


@dataclass(frozen=True)
class SearchHandlerSharedContext:
    seedlot_search_service: Any
    program_search_service: Any
    trait_search_service: Any


def _build_success_response(
    *,
    function_name: str,
    result_type: str,
    items: list[Any],
    message: str,
) -> dict[str, Any]:
    return {
        "success": True,
        "function": function_name,
        "result_type": result_type,
        "data": {
            "total": len(items),
            "items": items,
            "message": message,
        },
        "demo": False,
    }


def _build_failure_response(
    *,
    logger: Any,
    log_message: str,
    error: Exception,
    message: str,
) -> dict[str, Any]:
    logger.error("%s: %s", log_message, error)
    return {
        "success": False,
        "error": str(error),
        "message": message,
    }


async def handle_search(
    executor: Any,
    function_name: str,
    params: dict[str, Any],
    *,
    shared: SearchHandlerSharedContext,
    logger: Any,
) -> dict[str, Any]:
    """Handle search_* functions via a dedicated sibling module."""
    if function_name == "search_germplasm":
        org_id = params.get("organization_id", 1)
        query = params.get("query") or params.get("q")
        crop = params.get("crop")
        trait = params.get("trait")

        full_query = query
        if crop and (not query or crop not in query):
            full_query = f"{crop} {query or ''}".strip()

        try:
            if not executor.germplasm_search_service:
                raise RuntimeError("Germplasm search service not available")

            results = await executor.germplasm_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=full_query,
                trait=trait,
                limit=SEARCH_RESULT_LIMIT,
            )

            return _build_success_response(
                function_name=function_name,
                result_type="germplasm_list",
                items=results,
                message=f"Found {len(results)} germplasm records matching '{full_query}'",
            )
        except Exception as error:
            return _build_failure_response(
                logger=logger,
                log_message="Search failed",
                error=error,
                message="Failed to search germplasm database",
            )

    if function_name == "search_trials":
        org_id = params.get("organization_id", 1)
        query = params.get("query") or params.get("q")
        crop = params.get("crop")
        location = params.get("location")
        program = params.get("program")
        status = params.get("status")

        try:
            results = await executor.trial_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                crop=crop,
                location=location,
                program=program,
                status=status,
                limit=SEARCH_RESULT_LIMIT,
            )

            return _build_success_response(
                function_name=function_name,
                result_type="trial_list",
                items=results,
                message=f"Found {len(results)} trials" + (f" matching '{query}'" if query else ""),
            )
        except Exception as error:
            return _build_failure_response(
                logger=logger,
                log_message="Trial search failed",
                error=error,
                message="Failed to search trials database",
            )

    if function_name == "search_crosses":
        org_id = params.get("organization_id", 1)
        query = params.get("query") or params.get("q")
        parent_id = params.get("parent_id")
        status = params.get("status")
        cross_type = params.get("cross_type")
        year = params.get("year")

        try:
            results = await executor.cross_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                parent_id=parent_id,
                status=status,
                cross_type=cross_type,
                year=year,
                limit=SEARCH_RESULT_LIMIT,
            )

            return _build_success_response(
                function_name=function_name,
                result_type="cross_list",
                items=results,
                message=f"Found {len(results)} crosses" + (f" matching '{query}'" if query else ""),
            )
        except Exception as error:
            return _build_failure_response(
                logger=logger,
                log_message="Cross search failed",
                error=error,
                message="Failed to search crosses database",
            )

    if function_name == "search_accessions":
        org_id = params.get("organization_id", 1)
        query = params.get("query") or params.get("q")
        country = params.get("country")

        try:
            results = await executor.germplasm_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                limit=SEARCH_RESULT_LIMIT,
            )

            if country:
                locations = await executor.location_search_service.search(
                    db=executor.db,
                    organization_id=org_id,
                    country=country,
                    limit=ACCESSION_LOCATION_LOOKUP_LIMIT,
                )
                _ = {loc["id"] for loc in locations}

            return _build_success_response(
                function_name=function_name,
                result_type="accession_list",
                items=results,
                message=f"Found {len(results)} accessions" + (f" matching '{query}'" if query else ""),
            )
        except Exception as error:
            return _build_failure_response(
                logger=logger,
                log_message="Accession search failed",
                error=error,
                message="Failed to search accessions database",
            )

    if function_name == "search_locations":
        org_id = params.get("organization_id", 1)
        query = params.get("query") or params.get("q")
        country = params.get("country")
        location_type = params.get("type") or params.get("location_type")

        try:
            results = await executor.location_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                country=country,
                location_type=location_type,
                limit=SEARCH_RESULT_LIMIT,
            )

            return _build_success_response(
                function_name=function_name,
                result_type="location_list",
                items=results,
                message=f"Found {len(results)} locations" + (f" matching '{query}'" if query else ""),
            )
        except Exception as error:
            return _build_failure_response(
                logger=logger,
                log_message="Location search failed",
                error=error,
                message="Failed to search locations database",
            )

    if function_name == "search_seedlots":
        org_id = params.get("organization_id", 1)
        query = params.get("query") or params.get("q")
        germplasm_id = params.get("germplasm_id")
        location_id = params.get("location_id")

        try:
            results = await shared.seedlot_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                germplasm_id=int(germplasm_id) if germplasm_id else None,
                location_id=int(location_id) if location_id else None,
                limit=SEARCH_RESULT_LIMIT,
            )

            return _build_success_response(
                function_name=function_name,
                result_type="seedlot_list",
                items=results,
                message=f"Found {len(results)} seedlots" + (f" matching '{query}'" if query else ""),
            )
        except Exception as error:
            return _build_failure_response(
                logger=logger,
                log_message="Seedlot search failed",
                error=error,
                message="Failed to search seedlots database",
            )

    if function_name == "search_programs":
        org_id = params.get("organization_id", 1)
        query = params.get("query") or params.get("q")
        crop = params.get("crop")
        is_research = params.get("is_research")

        try:
            results = await shared.program_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                crop=crop,
                is_research=is_research,
                limit=SEARCH_RESULT_LIMIT,
            )

            return _build_success_response(
                function_name=function_name,
                result_type="program_list",
                items=results,
                message=f"Found {len(results)} programs" + (f" matching '{query}'" if query else ""),
            )
        except Exception as error:
            return _build_failure_response(
                logger=logger,
                log_message="Program search failed",
                error=error,
                message="Failed to search programs database",
            )

    if function_name == "search_traits":
        org_id = params.get("organization_id", 1)
        query = params.get("query") or params.get("q")
        trait_class = params.get("trait_class") or params.get("class")
        data_type = params.get("data_type")
        crop = params.get("crop")
        ontology = params.get("ontology")

        try:
            results = await shared.trait_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                trait_class=trait_class,
                data_type=data_type,
                crop=crop,
                ontology=ontology,
                limit=SEARCH_RESULT_LIMIT,
            )

            return _build_success_response(
                function_name=function_name,
                result_type="trait_list",
                items=results,
                message=f"Found {len(results)} traits" + (f" matching '{query}'" if query else ""),
            )
        except Exception as error:
            return _build_failure_response(
                logger=logger,
                log_message="Trait search failed",
                error=error,
                message="Failed to search traits database",
            )

    return {"success": False, "error": f"Unhandled search function: {function_name}"}