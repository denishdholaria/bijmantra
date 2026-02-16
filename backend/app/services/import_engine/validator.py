from __future__ import annotations

from collections.abc import Iterable
from difflib import get_close_matches
import re


class SchemaValidator:
    """Validates and maps import headers to model columns with fuzzy matching."""

    _default_aliases = {
        "g_id": "germplasm_id",
        "germplasmname": "germplasm_name",
        "trialname": "trial_name",
        "observationunitname": "observation_unit_name",
    }

    def __init__(self, expected_fields: set[str], aliases: dict[str, str] | None = None):
        self.expected_fields = expected_fields
        raw_aliases = {**self._default_aliases, **(aliases or {})}
        self.aliases = {self._normalize(k): v for k, v in raw_aliases.items()}

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.strip().lower())

    def map_headers(self, headers: Iterable[str]) -> dict[str, str]:
        mapped: dict[str, str] = {}
        normalized_expected = {self._normalize(x): x for x in self.expected_fields}

        for header in headers:
            direct = self._normalize(header)
            if direct in normalized_expected:
                mapped[header] = normalized_expected[direct]
                continue

            if direct in self.aliases and self.aliases[direct] in self.expected_fields:
                mapped[header] = self.aliases[direct]
                continue

            suggestions = get_close_matches(direct, normalized_expected.keys(), n=1, cutoff=0.75)
            if suggestions:
                mapped[header] = normalized_expected[suggestions[0]]

        return mapped

    def validate_headers(self, headers: Iterable[str]) -> tuple[bool, list[str], dict[str, str]]:
        header_list = list(headers)
        mapped = self.map_headers(header_list)
        present = set(mapped.values())
        missing = sorted(self.expected_fields - present)
        return len(missing) == 0, missing, mapped
