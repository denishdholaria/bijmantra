"""Shared retrieval-audit builders for REEVU tool handlers."""

from __future__ import annotations

from typing import Any

from app.modules.ai.services.tool_query_helpers import (
    _dedupe_string_values,
    _sample_record_identifiers,
    _sample_scalar_values,
)


def _build_cross_domain_retrieval_tables(results: dict[str, Any]) -> list[str]:
    genomics = results.get("genomics") or {}
    return _dedupe_string_values(
        [
            "Germplasm" if results.get("germplasm") else None,
            "Trial" if results.get("trials") else None,
            "Observation" if results.get("observations") else None,
            "ObservationVariable" if results.get("observations") else None,
            "Location" if results.get("locations") else None,
            "Trait" if results.get("traits") else None,
            "Protocol" if results.get("protocols") else None,
            "Seedlot" if results.get("seedlots") else None,
            "BioQTL" if genomics.get("qtls") else None,
            "GWASResult" if genomics.get("associations") else None,
        ]
    )


def _build_cross_domain_retrieval_entities(
    *,
    original_query: str,
    requested_domains: list[str],
    result_presence: dict[str, bool],
    results: dict[str, Any],
    germplasm_query: str | None,
    trait_query: str | None,
    location_query: str | None,
    inferred_location_query: str | None,
    crop_query: str | None,
    program_query: str | None,
    seedlot_query: str | None,
    resolved_study_ids: list[str] | None = None,
    missing_domains: list[str] | None = None,
    missing_runtime_services: list[str] | None = None,
    resolved_weather_location: dict[str, Any] | None = None,
    weather_resolution_error: str | None = None,
) -> dict[str, Any]:
    def add_entity(target: dict[str, Any], key: str, value: Any, *, allow_empty_list: bool = False) -> None:
        if value is None:
            return
        if isinstance(value, str) and not value.strip():
            return
        if isinstance(value, list) and not value and not allow_empty_list:
            return
        if isinstance(value, dict) and not value:
            return
        target[key] = value

    entities: dict[str, Any] = {
        "query": original_query,
        "requested_domains": requested_domains,
        "resolved_domains": [
            domain for domain in requested_domains if result_presence.get(domain)
        ],
    }

    add_entity(entities, "germplasm", germplasm_query)
    add_entity(entities, "trait", trait_query)
    add_entity(entities, "location", location_query)
    add_entity(entities, "inferred_location_query", inferred_location_query)
    add_entity(entities, "crop", crop_query)
    add_entity(entities, "program", program_query)
    add_entity(entities, "seedlot", seedlot_query)
    add_entity(entities, "missing_domains", missing_domains)
    add_entity(entities, "missing_runtime_services", missing_runtime_services)

    add_entity(entities, "germplasm_count", len(results.get("germplasm") or []))
    add_entity(entities, "trial_count", len(results.get("trials") or []))
    add_entity(entities, "observation_count", len(results.get("observations") or []))
    add_entity(entities, "protocol_count", len(results.get("protocols") or []))
    add_entity(entities, "location_count", len(results.get("locations") or []))
    add_entity(entities, "trait_count", len(results.get("traits") or []))
    add_entity(entities, "seedlot_count", len(results.get("seedlots") or []))

    genomics = results.get("genomics") or {}
    add_entity(entities, "genomics_qtl_count", len(genomics.get("qtls") or []))
    add_entity(entities, "genomics_association_count", len(genomics.get("associations") or []))

    add_entity(
        entities,
        "resolved_germplasm_ids",
        _sample_record_identifiers(results.get("germplasm"), keys=("accession", "id")),
    )
    add_entity(
        entities,
        "resolved_trial_ids",
        _sample_record_identifiers(results.get("trials"), keys=("trial_db_id", "id")),
    )
    add_entity(
        entities,
        "resolved_observation_ids",
        _sample_record_identifiers(results.get("observations"), keys=("observation_db_id", "id")),
    )
    add_entity(
        entities,
        "resolved_location_ids",
        _sample_record_identifiers(results.get("locations"), keys=("location_db_id", "id")),
    )
    add_entity(
        entities,
        "resolved_protocol_ids",
        _sample_record_identifiers(results.get("protocols"), keys=("id",)),
    )
    add_entity(
        entities,
        "resolved_trait_ids",
        _sample_record_identifiers(results.get("traits"), keys=("id",)),
    )
    add_entity(
        entities,
        "resolved_trait_names",
        _sample_record_identifiers(results.get("traits"), keys=("name",)),
    )
    add_entity(
        entities,
        "resolved_seedlot_ids",
        _sample_record_identifiers(results.get("seedlots"), keys=("seedlot_db_id", "id")),
    )
    add_entity(
        entities,
        "resolved_qtl_ids",
        _sample_record_identifiers(genomics.get("qtls"), keys=("qtl_id", "id")),
    )
    add_entity(
        entities,
        "resolved_marker_ids",
        _sample_record_identifiers(genomics.get("associations"), keys=("marker_name", "id")),
    )
    add_entity(entities, "resolved_study_ids", _sample_scalar_values(resolved_study_ids or []))
    add_entity(entities, "resolved_genomics_trait", genomics.get("trait"))
    add_entity(
        entities,
        "matched_genomics_trait_candidates",
        _sample_scalar_values((genomics.get("summary") or {}).get("matched_trait_candidates") or []),
    )

    if "weather" in requested_domains or weather_resolution_error or resolved_weather_location or results.get("weather"):
        add_entity(
            entities,
            "resolved_weather_location_id",
            (resolved_weather_location or {}).get("id")
            or (resolved_weather_location or {}).get("location_db_id"),
        )
        entities["weather_coordinates_used"] = bool(resolved_weather_location)
        add_entity(entities, "weather_failure_reason", weather_resolution_error)
        add_entity(
            entities,
            "weather_data_source",
            (results.get("weather") or {}).get("source"),
        )

    return entities