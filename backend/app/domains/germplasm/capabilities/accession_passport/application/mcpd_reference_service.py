"""Use cases for MCPD v2.1 accession passport reference data."""

from __future__ import annotations

from typing import Any

from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    acquisition_source_codes_payload,
    biological_status_codes_payload,
    build_mcpd_template_csv,
    country_codes_payload,
    storage_type_codes_payload,
)


class MCPDReferenceService:
    """Application facade for MCPD reference and template payloads."""

    def template_csv(self) -> str:
        return build_mcpd_template_csv()

    def biological_status_codes(self) -> dict[str, Any]:
        return biological_status_codes_payload()

    def acquisition_source_codes(self) -> dict[str, Any]:
        return acquisition_source_codes_payload()

    def storage_type_codes(self) -> dict[str, Any]:
        return storage_type_codes_payload()

    def country_codes(self) -> dict[str, Any]:
        return country_codes_payload()


def get_mcpd_reference_service() -> MCPDReferenceService:
    """Return the stateless MCPD reference use-case facade."""

    return MCPDReferenceService()
