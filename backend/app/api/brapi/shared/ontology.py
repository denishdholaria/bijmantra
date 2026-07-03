"""Shared BrAPI ontology-reference helpers."""

from typing import Any


def _as_nonempty_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _first_nonempty(*values: Any) -> str | None:
    for value in values:
        normalized = _as_nonempty_string(value)
        if normalized is not None:
            return normalized
    return None


def _normalize_documentation_link(link: Any) -> dict[str, Any] | None:
    if isinstance(link, str):
        url = _as_nonempty_string(link)
        return {"URL": url} if url else None

    if not isinstance(link, dict):
        return None

    url = _first_nonempty(link.get("URL"), link.get("url"))
    if url is None:
        return None

    normalized = dict(link)
    normalized["URL"] = url
    normalized.pop("url", None)
    return normalized


def normalize_documentation_links(value: Any) -> list[dict[str, Any]] | None:
    if value is None:
        return None

    raw_links = value if isinstance(value, list) else [value]
    links = [
        normalized
        for raw_link in raw_links
        if (normalized := _normalize_documentation_link(raw_link)) is not None
    ]
    return links or None


def extract_ontology_fields(
    ontology_reference: dict[str, Any] | None = None,
    *,
    ontology_db_id: Any = None,
    ontology_name: Any = None,
    ontology_term_id: Any = None,
    ontology_version: Any = None,
    ontology_documentation_links: Any = None,
) -> dict[str, Any]:
    reference = ontology_reference or {}

    return {
        "ontology_db_id": _first_nonempty(
            ontology_db_id,
            reference.get("ontologyDbId"),
            reference.get("ontology_db_id"),
        ),
        "ontology_name": _first_nonempty(
            ontology_name,
            reference.get("ontologyName"),
            reference.get("ontology_name"),
        ),
        "ontology_term_id": _first_nonempty(
            ontology_term_id,
            reference.get("ontologyTermId"),
            reference.get("termId"),
            reference.get("ontology_term_id"),
            reference.get("term_id"),
        ),
        "ontology_version": _first_nonempty(
            ontology_version,
            reference.get("version"),
            reference.get("ontologyVersion"),
            reference.get("ontology_version"),
        ),
        "ontology_documentation_links": normalize_documentation_links(
            ontology_documentation_links
            if ontology_documentation_links is not None
            else reference.get("documentationLinks") or reference.get("documentation_links")
        ),
    }


def build_ontology_reference(
    *,
    ontology_db_id: Any = None,
    ontology_name: Any = None,
    ontology_term_id: Any = None,
    ontology_version: Any = None,
    ontology_documentation_links: Any = None,
) -> dict[str, Any] | None:
    fields = extract_ontology_fields(
        ontology_db_id=ontology_db_id,
        ontology_name=ontology_name,
        ontology_term_id=ontology_term_id,
        ontology_version=ontology_version,
        ontology_documentation_links=ontology_documentation_links,
    )

    reference: dict[str, Any] = {}
    if fields["ontology_db_id"]:
        reference["ontologyDbId"] = fields["ontology_db_id"]
    if fields["ontology_name"]:
        reference["ontologyName"] = fields["ontology_name"]
    if fields["ontology_term_id"]:
        reference["ontologyTermId"] = fields["ontology_term_id"]
    if fields["ontology_version"]:
        reference["version"] = fields["ontology_version"]
    if fields["ontology_documentation_links"]:
        reference["documentationLinks"] = fields["ontology_documentation_links"]

    return reference or None
