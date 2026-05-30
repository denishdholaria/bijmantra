from dataclasses import dataclass
from typing import Any


SEARCH_RESULT_LIMIT = 20
MAX_SEARCH_RESULT_LIMIT = 50
CHAT_PREVIEW_LIMIT = 20
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
    total: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
    evidence_refs: list[str] | None = None,
    calculation_method_refs: list[str] | None = None,
) -> dict[str, Any]:
    total_count = len(items) if total is None else total
    data = {
        "total": total_count,
        "items": items,
        "message": message,
    }
    if total is not None:
        data["returned"] = len(items)
        data["has_more"] = total_count > len(items)
    if limit is not None:
        data["limit"] = limit
    if offset is not None:
        data["offset"] = offset
        if limit:
            data["page"] = (offset // limit) + 1
            data["next_page"] = ((offset // limit) + 2) if total_count > offset + len(items) else None

    response: dict[str, Any] = {
        "success": True,
        "function": function_name,
        "result_type": result_type,
        "data": data,
        "demo": False,
    }
    if evidence_refs:
        response["evidence_refs"] = evidence_refs
    if calculation_method_refs:
        response["calculation_method_refs"] = calculation_method_refs
    return response


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


def _trial_result_label(status: str | None) -> str:
    normalized = (status or "").strip().lower()
    if normalized in {"active", "true", "1"}:
        return "active trials"
    if normalized in {"inactive", "false", "0"}:
        return "inactive trials"
    return "trials"


def _trial_evidence_refs(items: list[Any]) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        trial_id = item.get("id") or item.get("trial_id") or item.get("trialDbId")
        if trial_id is None:
            continue
        ref = f"db:trial:{trial_id}"
        if ref in seen:
            continue
        refs.append(ref)
        seen.add(ref)
    return refs


def _coerce_positive_int(value: Any, *, default: int, maximum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default

    parsed = max(1, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed


def _coerce_offset(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def _trial_item_line(index: int, item: Any) -> str | None:
    if not isinstance(item, dict):
        return None

    name = str(item.get("name") or item.get("trial_name") or item.get("trial_db_id") or "Unnamed trial").strip()
    crop = str(item.get("crop") or "crop unknown").strip()
    location = str(item.get("location") or "location not recorded").strip()
    start_date = item.get("start_date") or "start date not recorded"
    end_date = item.get("end_date") or "end date not recorded"
    return f"{index}. {name} - {crop}; {location}; {start_date} to {end_date}"


def _trial_followup_phrase(*, next_page: int, status: str | None, crop: str | None, location: str | None, program: str | None) -> str:
    parts: list[str] = []
    if crop:
        parts.append(str(crop))
    if status:
        parts.append(str(status))
    parts.append("trials")
    if location:
        parts.append(f"in {location}")
    if program:
        parts.append(f"for {program}")
    parts.append(f"page {next_page}")
    return " ".join(parts)


def _build_trial_search_message(
    *,
    total: int,
    returned: int,
    offset: int,
    limit: int,
    status: str | None,
    query: str | None,
    crop: str | None,
    location: str | None,
    program: str | None,
    items: list[Any],
    summary_only: bool,
) -> str:
    trial_label = _trial_result_label(status)
    filters = []
    if query:
        filters.append(f"query '{query}'")
    if crop:
        filters.append(f"crop '{crop}'")
    if location:
        filters.append(f"location '{location}'")
    if program:
        filters.append(f"program '{program}'")

    scope = f" matching {', '.join(filters)}" if filters else ""
    if total == 0:
        return f"No {trial_label}{scope} were found in the accessible database."

    message_parts = [f"There are {total} {trial_label}{scope} in the accessible database."]
    if summary_only:
        return " ".join(message_parts)

    if returned == 0:
        message_parts.append(
            "The requested result window starts after the available records; ask for page 1 or narrow the filters."
        )
        return " ".join(message_parts)

    first_record_number = offset + 1
    last_record_number = offset + returned
    message_parts.append(
        f"Here are records {first_record_number}-{last_record_number} from a deterministic name-sorted query."
    )

    preview_lines = [
        line
        for line in (
            _trial_item_line(first_record_number + index, item)
            for index, item in enumerate(items[:CHAT_PREVIEW_LIMIT])
        )
        if line
    ]
    if preview_lines:
        message_parts.append("\n".join(preview_lines))

    remaining_after_window = max(total - last_record_number, 0)
    if returned > len(preview_lines):
        message_parts.append(
            f"{returned - len(preview_lines)} more records were returned; ask for a smaller filtered view if you want a compact list."
        )
    if remaining_after_window:
        next_page = (offset // limit) + 2
        followup_phrase = _trial_followup_phrase(
            next_page=next_page,
            status=status,
            crop=crop,
            location=location,
            program=program,
        )
        message_parts.append(
            f"{remaining_after_window} additional matching trials remain. Ask for '{followup_phrase}' or narrow by crop, location, or program."
        )

    return "\n\n".join(message_parts)


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
        limit = _coerce_positive_int(params.get("limit"), default=SEARCH_RESULT_LIMIT, maximum=MAX_SEARCH_RESULT_LIMIT)
        page = _coerce_positive_int(params.get("page"), default=1)
        offset = _coerce_offset(params.get("offset")) if "offset" in params else (page - 1) * limit
        summary_only = bool(params.get("summary_only"))

        try:
            results = await executor.trial_search_service.search(
                db=executor.db,
                organization_id=org_id,
                query=query,
                crop=crop,
                location=location,
                program=program,
                status=status,
                limit=limit,
                offset=offset,
            )
            total = await executor.trial_search_service.count(
                db=executor.db,
                organization_id=org_id,
                query=query,
                crop=crop,
                location=location,
                program=program,
                status=status,
            )
            message = _build_trial_search_message(
                total=total,
                returned=len(results),
                offset=offset,
                limit=limit,
                status=status,
                query=query,
                crop=crop,
                location=location,
                program=program,
                items=results,
                summary_only=summary_only,
            )

            return _build_success_response(
                function_name=function_name,
                result_type="trial_list",
                items=results,
                message=message,
                total=total,
                limit=limit,
                offset=offset,
                evidence_refs=_trial_evidence_refs(results),
                calculation_method_refs=["fn:search_trials.count"],
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
