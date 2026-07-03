"""SQLAlchemy and compatibility adapters for MCPD accession export."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.germplasm.adapters import get_seed_bank_accession_model
from app.domains.germplasm.capabilities.accession_passport.application.mcpd_export_service import (
    accession_to_mcpd as accession_record_to_mcpd,
)
from app.domains.germplasm.capabilities.accession_passport.application.mcpd_export_service import (
    export_to_mcpd_csv as export_records_to_mcpd_csv,
)
from app.domains.germplasm.capabilities.accession_passport.application.mcpd_export_service import (
    export_to_mcpd_json as export_records_to_mcpd_json,
)
from app.domains.germplasm.capabilities.accession_passport.ports import (
    MCPDAccessionExportRecord,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import MCPDRecord


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    resolved = value.value if hasattr(value, "value") else value
    return str(resolved) if resolved is not None else None


def mcpd_export_record_from_accession(accession: Any) -> MCPDAccessionExportRecord:
    """Map a legacy/ORM accession object into the capability export record."""

    vault = getattr(accession, "vault", None)
    vault_type = _enum_value(getattr(vault, "type", None)) if vault else None

    return MCPDAccessionExportRecord(
        accession_number=accession.accession_number,
        genus=accession.genus,
        species=accession.species,
        subspecies=accession.subspecies,
        common_name=accession.common_name,
        origin=accession.origin,
        collection_date=accession.collection_date,
        collection_site=accession.collection_site,
        latitude=accession.latitude,
        longitude=accession.longitude,
        altitude=accession.altitude,
        status=_enum_value(accession.status),
        vault_type=vault_type,
        mls=bool(accession.mls),
        donor_institution=accession.donor_institution,
        pedigree=accession.pedigree,
        notes=accession.notes,
    )


class SqlAlchemyMCPDExportAdapter:
    """Persistence adapter for reading accessions eligible for MCPD export."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        accession_model: type | None = None,
    ) -> None:
        self._db = db
        self._accession_model = accession_model or get_seed_bank_accession_model()

    async def list_export_records(
        self,
        organization_id: int,
    ) -> list[MCPDAccessionExportRecord]:
        result = await self._db.execute(
            select(self._accession_model)
            .where(self._accession_model.organization_id == organization_id)
            .options()
        )
        return [
            mcpd_export_record_from_accession(accession)
            for accession in result.scalars().all()
        ]


def accession_to_mcpd(accession: Any, inst_code: str = "BIJ001") -> MCPDRecord:
    """Compatibility helper accepting legacy accession objects."""

    return accession_record_to_mcpd(
        mcpd_export_record_from_accession(accession),
        inst_code=inst_code,
    )


def export_to_mcpd_csv(accessions: list[Any], inst_code: str = "BIJ001") -> str:
    """Compatibility helper accepting legacy accession objects."""

    return export_records_to_mcpd_csv(
        [mcpd_export_record_from_accession(accession) for accession in accessions],
        inst_code=inst_code,
    )


def export_to_mcpd_json(accessions: list[Any], inst_code: str = "BIJ001") -> list[dict[str, object]]:
    """Compatibility helper accepting legacy accession objects."""

    return export_records_to_mcpd_json(
        [mcpd_export_record_from_accession(accession) for accession in accessions],
        inst_code=inst_code,
    )
