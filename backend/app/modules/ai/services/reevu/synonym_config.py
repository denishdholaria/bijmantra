"""Configurable agricultural synonym normalization for REEVU routing."""

from __future__ import annotations

import re


SYNONYM_GROUPS: dict[str, list[str]] = {
    "germplasm": [
        "cultivar",
        "cultivars",
        "variety",
        "varieties",
        "entry",
        "entries",
        "line",
        "lines",
        "accession",
        "accessions",
    ],
    "trial": [
        "experiment",
        "experiments",
        "field trial",
        "field trials",
        "field experiment",
        "field experiments",
    ],
    "observation": [
        "plot",
        "plots",
        "observation unit",
        "observation units",
    ],
    "trait": [
        "character",
        "characters",
        "variable",
        "variables",
        "phenotype",
        "phenotypes",
    ],
    "cross": [
        "hybridization",
        "hybridizations",
        "mating",
        "matings",
    ],
    "genomics": [
        "marker",
        "markers",
        "snp",
        "snps",
        "locus",
        "loci",
    ],
}

CROP_NAMES: dict[str, list[str]] = {
    "wheat": ["triticum", "triticum aestivum", "bread wheat"],
    "rice": ["oryza", "oryza sativa", "paddy"],
    "maize": ["corn", "zea mays"],
    "sorghum": ["jowar", "sorghum bicolor"],
    "pearl millet": ["bajra", "pennisetum glaucum", "cenchrus americanus"],
    "chickpea": ["chana", "gram", "cicer arietinum"],
    "soybean": ["soya", "glycine max"],
    "cotton": ["kapas", "gossypium"],
    "barley": ["jau", "hordeum vulgare"],
    "oat": ["jai", "avena sativa"],
    "sunflower": ["surajmukhi", "helianthus annuus"],
    "groundnut": ["peanut", "moongphali", "arachis hypogaea"],
}

TEMPORAL_PATTERNS: list[tuple[str, str]] = [
    (r"\bthis season\b", "current_season"),
    (r"\bcurrent season\b", "current_season"),
    (r"\blast season\b", "previous_season"),
    (r"\bprevious season\b", "previous_season"),
    (r"\blast year\b", "previous_year"),
    (r"\bthis year\b", "current_year"),
    # Extended temporal qualifiers (Task 6 — temporal reasoning spec)
    (r"\bover the last\s+(\d+)\s+years?\b", r"last_\1_years"),
    (r"\bover the last\s+(\d+)\s+seasons?\b", r"last_\1_seasons"),
    (r"\bover the last\s+(\d+)\s+cycles?\b", r"last_\1_cycles"),
    (r"\bsince\s+(20\d{2})\b", r"since_\1"),
    (r"\bbetween\s+(20\d{2})\s+and\s+(20\d{2})\b", r"between_\1_\2"),
    (r"\b(20\d{2})\b", r"\1"),
    (r"\b(kharif|rabi|zaid)\b", r"\1"),
]

QUALIFIER_TERMS: dict[str, str] = {
    "best": "descending",
    "highest": "descending",
    "top": "descending",
    "most": "descending",
    "worst": "ascending",
    "lowest": "ascending",
    "least": "ascending",
    "bottom": "ascending",
}

NEGATION_PATTERNS: list[str] = [
    r"\bnot\s+",
    r"\bnon[-\s]",
    r"\bwithout\s+",
    r"\blacking\s+",
    r"\bexcluding\s+",
]


class SynonymExpander:
    """Normalize agricultural terminology in user messages."""

    def __init__(self, synonym_groups: dict[str, list[str]] | None = None) -> None:
        self._groups = synonym_groups or SYNONYM_GROUPS
        self._lookup: dict[str, str] = {}
        for canonical, synonyms in self._groups.items():
            for synonym in synonyms:
                self._lookup[synonym.lower()] = canonical

    def expand(self, message: str) -> str:
        """Replace synonyms with canonical terms using longest-match-first matching."""
        result = message
        for synonym in sorted(self._lookup, key=len, reverse=True):
            pattern = re.compile(rf"(?<!\w){re.escape(synonym)}(?!\w)", re.IGNORECASE)
            result = pattern.sub(self._lookup[synonym], result)
        return result
