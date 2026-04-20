"""Shared query, identifier, and normalization helpers for REEVU tool handlers."""

from __future__ import annotations

from typing import Any


def _get_germplasm_identifier(germplasm: dict[str, Any]) -> str | None:
    """Return the preferred external identifier for a germplasm payload."""
    return str(germplasm.get("accession") or germplasm.get("id") or "").strip() or None


def _normalize_text_token(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def _dedupe_string_values(values: list[Any]) -> list[str]:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_values.append(normalized)
    return unique_values


def _sample_scalar_values(values: list[Any], *, limit: int = 3) -> list[str]:
    return _dedupe_string_values(values)[:limit]


def _sample_record_identifiers(
    records: list[dict[str, Any]] | None,
    *,
    keys: tuple[str, ...],
    limit: int = 3,
) -> list[str]:
    if not records:
        return []

    samples: list[str] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue

        identifier: str | None = None
        for key in keys:
            candidate = record.get(key)
            if candidate is None or isinstance(candidate, (dict, list)):
                continue
            normalized = str(candidate).strip()
            if normalized:
                identifier = normalized
                break

        if identifier is None or identifier in seen:
            continue

        seen.add(identifier)
        samples.append(identifier)
        if len(samples) >= limit:
            break

    return samples


def _resolve_trait_query(
    *,
    available_traits: list[str],
    requested_trait: str | None,
) -> tuple[str | None, list[str]]:
    """Resolve a free-form trait request against authoritative genomics traits."""
    normalized_requested = _normalize_text_token(requested_trait)
    if not normalized_requested:
        return None, []

    exact_matches = [
        trait
        for trait in available_traits
        if _normalize_text_token(trait) == normalized_requested
    ]
    if exact_matches:
        return exact_matches[0], exact_matches

    partial_matches = [
        trait
        for trait in available_traits
        if normalized_requested in _normalize_text_token(trait)
        or _normalize_text_token(trait) in normalized_requested
    ]
    if len(partial_matches) == 1:
        return partial_matches[0], partial_matches
    return None, partial_matches