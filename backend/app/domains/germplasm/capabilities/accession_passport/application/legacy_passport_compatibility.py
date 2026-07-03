"""Compatibility helpers for legacy BijMantra passport MCPD surfaces.

The public `/api/v2/passport/*` endpoints predate the capability-pack MCPD
adapter and expose a smaller, legacy response shape. Keep that shape stable
while moving MCPD vocabulary and export mapping ownership into AccessionPassport.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


_LEGACY_BIOLOGICAL_STATUS_CODES = (
    {"code": "100", "name": "Wild", "description": "Wild material"},
    {"code": "200", "name": "Weedy", "description": "Weedy form"},
    {
        "code": "300",
        "name": "Traditional cultivar/Landrace",
        "description": "Traditional cultivar or landrace",
    },
    {
        "code": "400",
        "name": "Breeding/Research material",
        "description": "Breeding line or research material",
    },
    {
        "code": "500",
        "name": "Advanced/Improved cultivar",
        "description": "Advanced or improved cultivar",
    },
    {"code": "600", "name": "GMO", "description": "Genetically modified organism"},
    {"code": "999", "name": "Other", "description": "Other (elaborate in remarks)"},
)

_LEGACY_ACQUISITION_SOURCE_CODES = (
    {"code": "10", "name": "Wild habitat", "description": "Collected from wild habitat"},
    {"code": "20", "name": "Farm/Field", "description": "Collected from farm or cultivated field"},
    {"code": "30", "name": "Market", "description": "Obtained from market"},
    {
        "code": "40",
        "name": "Institute/Genebank",
        "description": "Obtained from research institute or genebank",
    },
    {"code": "50", "name": "Seed company", "description": "Obtained from seed company"},
    {"code": "99", "name": "Other", "description": "Other (elaborate in remarks)"},
)


def legacy_bijmantra_passport_biological_status_codes() -> dict[str, list[dict[str, str]]]:
    """Return the stable legacy biological-status payload."""

    return {"codes": [dict(code) for code in _LEGACY_BIOLOGICAL_STATUS_CODES]}


def legacy_bijmantra_passport_acquisition_source_codes() -> dict[str, list[dict[str, str]]]:
    """Return the stable legacy acquisition-source payload."""

    return {"codes": [dict(code) for code in _LEGACY_ACQUISITION_SOURCE_CODES]}


def legacy_bijmantra_passport_to_mcpd(passport: Any) -> dict[str, Any]:
    """Map a legacy in-memory GermplasmPassport object to its public MCPD shape."""

    collection_site = getattr(passport, "collection_site", None)
    mcpd = {
        "ACCENUMB": getattr(passport, "accession_id", ""),
        "ACCENAME": getattr(passport, "accession_name", ""),
        "GENUS": getattr(passport, "genus", ""),
        "SPECIES": getattr(passport, "species", ""),
        "SPAUTHOR": getattr(passport, "species_authority", ""),
        "SUBTAXA": getattr(passport, "subtaxa", ""),
        "SAMPSTAT": _enum_value(getattr(passport, "biological_status", "")),
        "COLLSRC": _enum_value(getattr(passport, "acquisition_source", "")),
        "ACQDATE": _format_compact_date(getattr(passport, "acquisition_date", None)),
        "DONORCODE": getattr(passport, "donor_institute", ""),
        "DONORNUMB": getattr(passport, "donor_accession", ""),
        "ANCEST": getattr(passport, "pedigree", ""),
        "REMARKS": getattr(passport, "remarks", ""),
        "MLSSTAT": getattr(passport, "mlsstat", ""),
    }

    if collection_site:
        mcpd.update(
            {
                "ORIGCTY": getattr(collection_site, "country", ""),
                "COLLSITE": getattr(collection_site, "locality", ""),
                "LATITUDE": getattr(collection_site, "latitude", None),
                "LONGITUDE": getattr(collection_site, "longitude", None),
                "ELEVATION": getattr(collection_site, "elevation", None),
                "COLLDATE": _format_compact_date(getattr(collection_site, "collection_date", None)),
                "COLLNUMB": "",
                "COLLCODE": getattr(collection_site, "collector_institute", ""),
            }
        )

    return mcpd


def export_legacy_bijmantra_passports_to_mcpd(passports: Iterable[Any]) -> list[dict[str, Any]]:
    """Export legacy passport objects using the stable public MCPD shape."""

    return [legacy_bijmantra_passport_to_mcpd(passport) for passport in passports]


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _format_compact_date(value: Any) -> str:
    if value is None:
        return ""
    return value.strftime("%Y%m%d")
