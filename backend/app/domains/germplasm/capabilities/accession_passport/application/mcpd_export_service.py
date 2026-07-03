"""MCPD export orchestration owned by AccessionPassport."""

from __future__ import annotations

import csv
import io

from app.domains.germplasm.capabilities.accession_passport.domain import (
    MCPD_TEMPLATE_FIELDNAMES,
    country_name_to_iso,
    format_mcpd_date,
    map_status_to_sampstat,
    map_vault_type_to_storage,
)
from app.domains.germplasm.capabilities.accession_passport.ports import (
    MCPDAccessionExportRecord,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import MCPDRecord


def accession_to_mcpd(
    accession: MCPDAccessionExportRecord,
    inst_code: str = "BIJ001",
) -> MCPDRecord:
    """Convert an accession export snapshot to an MCPD v2.1 record."""

    return MCPDRecord(
        INSTCODE=inst_code,
        ACCENUMB=accession.accession_number,
        GENUS=accession.genus,
        SPECIES=accession.species,
        SUBTAXA=accession.subspecies,
        CROPNAME=accession.common_name,
        ORIGCTY=country_name_to_iso(accession.origin),
        COLLDATE=format_mcpd_date(accession.collection_date),
        COLLSITE=accession.collection_site,
        LATITUDE=accession.latitude,
        LONGITUDE=accession.longitude,
        ELEVATION=accession.altitude,
        SAMPSTAT=map_status_to_sampstat(accession.status),
        STORAGE=map_vault_type_to_storage(accession.vault_type),
        MLSSTAT=1 if accession.mls else 0,
        DONORNAME=accession.donor_institution,
        ANCEST=accession.pedigree,
        REMARKS=accession.notes,
        MCPDVERSION="2.1",
    )


def export_to_mcpd_csv(
    accessions: list[MCPDAccessionExportRecord],
    inst_code: str = "BIJ001",
) -> str:
    """Export accessions to MCPD CSV format."""

    output = io.StringIO()

    writer = csv.DictWriter(output, fieldnames=MCPD_TEMPLATE_FIELDNAMES, extrasaction="ignore")
    writer.writeheader()

    for accession in accessions:
        mcpd = accession_to_mcpd(accession, inst_code)
        row = mcpd.model_dump(by_alias=True, exclude_none=False)
        row = {key: (value if value is not None else "") for key, value in row.items()}
        writer.writerow(row)

    return output.getvalue()


def export_to_mcpd_json(
    accessions: list[MCPDAccessionExportRecord],
    inst_code: str = "BIJ001",
) -> list[dict[str, object]]:
    """Export accessions to MCPD JSON format."""

    return [
        accession_to_mcpd(accession, inst_code).model_dump(by_alias=True, exclude_none=True)
        for accession in accessions
    ]
