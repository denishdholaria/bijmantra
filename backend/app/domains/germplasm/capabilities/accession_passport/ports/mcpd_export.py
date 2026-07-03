"""Published MCPD export ports for AccessionPassport."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class MCPDAccessionExportRecord:
    """Capability-owned accession snapshot used for MCPD export shaping."""

    accession_number: str
    genus: str
    species: str | None = None
    subspecies: str | None = None
    common_name: str | None = None
    origin: str | None = None
    collection_date: datetime | None = None
    collection_site: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    status: str | None = None
    vault_type: str | None = None
    mls: bool = False
    donor_institution: str | None = None
    pedigree: str | None = None
    notes: str | None = None


class MCPDExportRepository(Protocol):
    """Port for reading accession snapshots eligible for MCPD export."""

    async def list_export_records(
        self,
        organization_id: int,
    ) -> list[MCPDAccessionExportRecord]:
        """Return accession snapshots visible to the tenant for MCPD export."""
