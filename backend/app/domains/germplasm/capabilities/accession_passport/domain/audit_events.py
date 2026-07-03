"""Accession Passport audit event vocabulary."""

MCPD_EXPORTED = "germplasm.mcpd_exported"
MCPD_IMPORTED = "germplasm.mcpd_imported"
MCPD_AUDIT_ACTIONS = (
    MCPD_EXPORTED,
    MCPD_IMPORTED,
)
MCPD_AUDIT_TARGET_TYPE = "mcpd_accession_passport"
