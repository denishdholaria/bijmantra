"""
MCPD (Multi-Crop Passport Descriptors) v2.1 Service

Compatibility facade for genebank MCPD data exchange.
"""

from app.domains.germplasm.capabilities.accession_passport.adapters.mcpd_export import (
    accession_to_mcpd as accession_to_mcpd,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.mcpd_export import (
    export_to_mcpd_csv as export_to_mcpd_csv,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.mcpd_export import (
    export_to_mcpd_json as export_to_mcpd_json,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    ACQUISITION_SOURCE_CODES,
    BIOLOGICAL_STATUS_CODES,
    COUNTRY_CODES,
    STORAGE_TYPE_CODES,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    MLS_STATUS_CODES as MLS_STATUS_CODES,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    iso_to_country_name as iso_to_country_name,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    map_sampstat_to_status as map_sampstat_to_status,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    map_storage_to_vault_type as map_storage_to_vault_type,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    mcpd_to_accession_data as mcpd_to_accession_data,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    parse_mcpd_csv as parse_mcpd_csv,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    parse_mcpd_date as parse_mcpd_date,
)
from app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference import (
    validate_mcpd_record as validate_mcpd_record,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import (
    MCPDImportResult as MCPDImportResult,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import (
    MCPDRecord as MCPDRecord,
)


# ============ Reference Data ============

def get_biological_status_codes() -> dict[int, str]:
    """Get all biological status codes"""
    return BIOLOGICAL_STATUS_CODES.copy()


def get_acquisition_source_codes() -> dict[int, str]:
    """Get all acquisition source codes"""
    return ACQUISITION_SOURCE_CODES.copy()


def get_storage_type_codes() -> dict[int, str]:
    """Get all storage type codes"""
    return STORAGE_TYPE_CODES.copy()


def get_country_codes() -> dict[str, str]:
    """Get all country codes"""
    return COUNTRY_CODES.copy()
