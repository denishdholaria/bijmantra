"""Shared evidence-envelope, freshness, and confidence helpers for REEVU tools."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.modules.ai.services.reevu_provenance_validator import validate_all as validate_provenance
from app.modules.ai.services.tool_query_helpers import _get_germplasm_identifier
from app.schemas.reevu_envelope import EvidenceRef, ReevuEnvelope, UncertaintyInfo


GERMPLASM_CONFIDENCE_BASE = 0.35
GERMPLASM_CONFIDENCE_IDENTIFIER_BONUS = 0.2
GERMPLASM_CONFIDENCE_SPECIES_BONUS = 0.1
GERMPLASM_CONFIDENCE_TRAIT_BONUS = 0.15
GERMPLASM_CONFIDENCE_OBSERVATION_BONUS = 0.15
GERMPLASM_CONFIDENCE_ORIGIN_BONUS = 0.05
GERMPLASM_CONFIDENCE_CAP = 0.95
GERMPLASM_EVIDENCE_OBSERVATION_LIMIT = 10
GERMPLASM_METADATA_UNKNOWN_VALUE = "Unknown"


def _parse_iso_timestamp(value: Any) -> datetime | None:
    """Normalize supported timestamp inputs to timezone-aware UTC datetimes."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        try:
            parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _derive_germplasm_data_age_seconds(observations: list[dict[str, Any]]) -> int | None:
    timestamps = [
        parsed
        for observation in observations
        for parsed in (
            _parse_iso_timestamp(observation.get("observation_time_stamp"))
            or _parse_iso_timestamp(observation.get("observed_at"))
            or _parse_iso_timestamp(observation.get("updated_at"))
            or _parse_iso_timestamp(observation.get("created_at")),
        )
        if parsed is not None
    ]
    if not timestamps:
        return None

    newest = max(timestamps)
    return max(int((datetime.now(UTC) - newest).total_seconds()), 0)


def _derive_germplasm_confidence(
    germplasm: dict[str, Any],
    observations: list[dict[str, Any]],
) -> float:
    confidence = GERMPLASM_CONFIDENCE_BASE
    if germplasm.get("accession"):
        confidence += GERMPLASM_CONFIDENCE_IDENTIFIER_BONUS
    if germplasm.get("species") and germplasm.get("species") != GERMPLASM_METADATA_UNKNOWN_VALUE:
        confidence += GERMPLASM_CONFIDENCE_SPECIES_BONUS
    if germplasm.get("traits"):
        confidence += GERMPLASM_CONFIDENCE_TRAIT_BONUS
    if observations:
        confidence += GERMPLASM_CONFIDENCE_OBSERVATION_BONUS
    if germplasm.get("origin") and germplasm.get("origin") != GERMPLASM_METADATA_UNKNOWN_VALUE:
        confidence += GERMPLASM_CONFIDENCE_ORIGIN_BONUS
    return round(min(confidence, GERMPLASM_CONFIDENCE_CAP), 2)


def _build_germplasm_evidence_envelope(
    *,
    germplasm: dict[str, Any],
    observations: list[dict[str, Any]],
    confidence_score: float,
    data_age_seconds: int | None,
) -> dict[str, Any]:
    accession = _get_germplasm_identifier(germplasm)
    evidence_refs = [
        EvidenceRef(
            source_type="database",
            entity_id=f"db:germplasm:{accession}",
            query_or_method="germplasm_search_service.get_by_id",
        )
    ]

    for observation in observations[:GERMPLASM_EVIDENCE_OBSERVATION_LIMIT]:
        observation_ref = observation.get("observation_db_id") or observation.get("id")
        if observation_ref is None:
            continue
        evidence_refs.append(
            EvidenceRef(
                source_type="database",
                entity_id=f"db:observation:{observation_ref}",
                query_or_method="observation_search_service.get_by_germplasm",
                freshness_seconds=float(data_age_seconds) if data_age_seconds is not None else None,
            )
        )

    missing_data: list[str] = []
    if not germplasm.get("traits"):
        missing_data.append("trait_annotations")
    if not observations:
        missing_data.append("linked_observations")

    envelope = ReevuEnvelope(
        claims=[
            f"Germplasm '{germplasm.get('name') or accession}' was retrieved from database-backed search.",
            f"Linked observation count: {len(observations)}",
        ],
        evidence_refs=evidence_refs,
        uncertainty=UncertaintyInfo(confidence=confidence_score, missing_data=missing_data),
        policy_flags=[],
    )
    provenance_flags = validate_provenance(envelope)
    if provenance_flags:
        envelope = envelope.model_copy(update={"policy_flags": envelope.policy_flags + provenance_flags})

    payload = envelope.model_dump()
    payload["calculations"] = payload.get("calculation_steps", [])
    return payload


def _derive_genomics_lookup_confidence(*, qtl_count: int, association_count: int) -> float:
    confidence = 0.45
    if qtl_count:
        confidence += 0.2
    if association_count:
        confidence += 0.2
    if qtl_count and association_count:
        confidence += 0.05
    return round(min(confidence, 0.9), 2)


def _build_genomics_evidence_envelope(
    *,
    trait: str,
    qtls: list[dict[str, Any]],
    associations: list[dict[str, Any]],
    confidence_score: float,
) -> dict[str, Any]:
    evidence_refs: list[EvidenceRef] = []
    seen_refs: set[str] = set()

    def add_ref(entity_id: str, query_or_method: str) -> None:
        if entity_id in seen_refs:
            return
        seen_refs.add(entity_id)
        evidence_refs.append(
            EvidenceRef(
                source_type="database",
                entity_id=entity_id,
                query_or_method=query_or_method,
            )
        )

    for qtl in qtls[:10]:
        qtl_id = qtl.get("qtl_id")
        if qtl_id:
            add_ref(f"db:qtl:{qtl_id}", "QTLMappingService.list_qtls")
        marker_name = qtl.get("marker_name")
        if marker_name:
            add_ref(f"db:marker:{marker_name}", "QTLMappingService.list_qtls")

    for association in associations[:10]:
        marker_name = association.get("marker_name")
        if marker_name:
            add_ref(f"db:marker:{marker_name}", "QTLMappingService.get_gwas_results")

    missing_data: list[str] = []
    if not qtls:
        missing_data.append("qtl_records")
    if not associations:
        missing_data.append("gwas_associations")

    envelope = ReevuEnvelope(
        claims=[
            f"Genomics marker associations for trait '{trait}' were retrieved from database-backed QTL/GWAS records.",
            f"Matched {len(qtls)} QTLs and {len(associations)} marker associations.",
        ],
        evidence_refs=evidence_refs,
        calculation_steps=[
            {
                "step_id": "calc:genomics:marker_lookup",
                "formula": "trait-filtered retrieval across QTL and GWAS records",
                "inputs": {
                    "trait": trait,
                    "qtl_count": len(qtls),
                    "association_count": len(associations),
                },
            }
        ],
        uncertainty=UncertaintyInfo(confidence=confidence_score, missing_data=missing_data),
        policy_flags=[],
    )
    provenance_flags = validate_provenance(envelope)
    if provenance_flags:
        envelope = envelope.model_copy(update={"policy_flags": envelope.policy_flags + provenance_flags})
    return envelope.model_dump()


def _build_cross_domain_evidence_envelope(
    *,
    query: str,
    germplasm: list[dict[str, Any]],
    trials: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    protocols: list[dict[str, Any]],
    locations: list[dict[str, Any]],
    weather_present: bool,
    genomics: dict[str, Any] | None,
    domains_involved: list[str],
    confidence_score: float,
) -> dict[str, Any]:
    evidence_refs: list[EvidenceRef] = []
    seen_refs: set[str] = set()

    def add_database_ref(entity_id: str, method: str) -> None:
        if not entity_id or entity_id in seen_refs:
            return
        seen_refs.add(entity_id)
        evidence_refs.append(
            EvidenceRef(
                source_type="database",
                entity_id=entity_id,
                query_or_method=method,
            )
        )

    for item in germplasm[:5]:
        accession = item.get("accession") or item.get("id")
        if accession:
            add_database_ref(f"db:germplasm:{accession}", "germplasm_search_service.search")

    for item in trials[:5]:
        trial_id = item.get("trial_db_id") or item.get("id")
        if trial_id:
            add_database_ref(f"db:trial:{trial_id}", "trial_search_service.search")

    for observation in observations[:10]:
        observation_ref = observation.get("observation_db_id") or observation.get("id")
        if observation_ref:
            add_database_ref(
                f"db:observation:{observation_ref}",
                "observation_search_service.search",
            )

    for item in protocols[:5]:
        protocol_id = item.get("protocolDbId") or item.get("id")
        if protocol_id:
            add_database_ref(f"db:protocol:{protocol_id}", "speed_breeding_service.get_protocols")

    for item in locations[:5]:
        location_id = item.get("locationDbId") or item.get("id") or item.get("name")
        if location_id:
            add_database_ref(f"db:location:{location_id}", "location_search_service.search")

    if weather_present:
        evidence_refs.append(
            EvidenceRef(
                source_type="function",
                entity_id="fn:weather.forecast",
                query_or_method="weather_service.get_forecast",
            )
        )

    if genomics:
        for qtl in genomics.get("qtls", [])[:10]:
            qtl_id = qtl.get("qtl_id")
            if qtl_id:
                add_database_ref(f"db:qtl:{qtl_id}", "QTLMappingService.list_qtls")
            marker_name = qtl.get("marker_name")
            if marker_name:
                add_database_ref(f"db:marker:{marker_name}", "QTLMappingService.list_qtls")

        for association in genomics.get("associations", [])[:10]:
            marker_name = association.get("marker_name")
            if marker_name:
                add_database_ref(f"db:marker:{marker_name}", "QTLMappingService.get_gwas_results")

    missing_data: list[str] = []
    if "breeding" in domains_involved and not germplasm and not observations:
        missing_data.append("breeding_records")
    if "trials" in domains_involved and not trials:
        missing_data.append("trial_records")
    if "weather" in domains_involved and not locations and not weather_present:
        missing_data.append("environment_records")
    if "genomics" in domains_involved and not genomics:
        missing_data.append("genomics_records")
    if "protocols" in domains_involved and not protocols:
        missing_data.append("protocol_records")

    domain_phrase = ", ".join(domains_involved) if domains_involved else "cross-domain"
    genomics_qtl_count = len((genomics or {}).get("qtls", []))
    genomics_association_count = len((genomics or {}).get("associations", []))

    envelope = ReevuEnvelope(
        claims=[
            f"Cross-domain query '{query}' was executed across {domain_phrase} evidence.",
            (
                f"Retrieved {len(germplasm)} germplasm entries, {len(trials)} trials, "
                f"{len(observations)} observations, {len(protocols)} protocols, {len(locations)} locations, "
                f"{genomics_qtl_count} QTLs, and "
                f"{genomics_association_count} marker associations."
            ),
        ],
        evidence_refs=evidence_refs,
        calculation_steps=[
            {
                "step_id": "calc:cross_domain:join",
                "formula": f"compound retrieval join across {domain_phrase} services",
                "inputs": {
                    "query": query,
                    "domains_involved": domains_involved,
                    "germplasm_count": len(germplasm),
                    "trial_count": len(trials),
                    "observation_count": len(observations),
                    "protocol_count": len(protocols),
                    "location_count": len(locations),
                    "weather_present": weather_present,
                    "genomics_qtl_count": genomics_qtl_count,
                    "genomics_association_count": genomics_association_count,
                },
            }
        ],
        uncertainty=UncertaintyInfo(confidence=confidence_score, missing_data=missing_data),
        policy_flags=[],
    )
    provenance_flags = validate_provenance(envelope)
    if provenance_flags:
        envelope = envelope.model_copy(update={"policy_flags": envelope.policy_flags + provenance_flags})
    return envelope.model_dump()


def _build_compute_evidence_envelope(
    *,
    routine: str,
    claim: str,
    success_response: dict[str, Any],
    confidence_score: float,
    missing_data: list[str] | None = None,
) -> dict[str, Any]:
    provenance = success_response.get("provenance", {})
    envelope = ReevuEnvelope(
        claims=[claim],
        evidence_refs=[
            EvidenceRef.model_validate(item)
            for item in provenance.get("evidence_refs", [])
        ],
        calculation_steps=provenance.get("calculation_steps", []),
        uncertainty=UncertaintyInfo(
            confidence=confidence_score,
            missing_data=missing_data or [],
        ),
        policy_flags=provenance.get("policy_flags", []),
    )
    provenance_flags = validate_provenance(envelope)
    if provenance_flags:
        envelope = envelope.model_copy(update={"policy_flags": envelope.policy_flags + provenance_flags})
    payload = envelope.model_dump()
    payload["calculations"] = payload.get("calculation_steps", [])
    payload["routine"] = routine
    return payload