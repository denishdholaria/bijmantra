"""SQLAlchemy adapters for MCPD accession import persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.germplasm.adapters import get_seed_bank_accession_model
from app.domains.germplasm.capabilities.accession_passport.application import (
    MCPDImportPlan,
)
from app.domains.germplasm.capabilities.accession_passport.ports import (
    MCPDImportPersistenceError,
    MCPDImportPersistenceResult,
)


class SqlAlchemyMCPDImportAdapter:
    """Persistence adapter for MCPD accession import plans."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        accession_model: type | None = None,
    ) -> None:
        self._db = db
        self._accession_model = accession_model or get_seed_bank_accession_model()

    async def list_existing_accession_numbers(self, organization_id: int) -> set[str]:
        result = await self._db.execute(
            select(self._accession_model.accession_number).where(
                self._accession_model.organization_id == organization_id
            )
        )
        return {row[0] for row in result.fetchall()}

    async def persist_import_plan(
        self,
        *,
        organization_id: int,
        import_plan: MCPDImportPlan,
    ) -> MCPDImportPersistenceResult:
        imported = 0
        errors: list[MCPDImportPersistenceError] = []

        for planned_accession in import_plan.accessions_to_create:
            try:
                accession = self._accession_model(
                    **planned_accession.accession_data,
                    organization_id=organization_id,
                )
                self._db.add(accession)
                imported += 1
            except Exception as exc:
                errors.append(
                    MCPDImportPersistenceError(
                        row=planned_accession.row,
                        accession_number=planned_accession.accession_number,
                        errors=(str(exc),),
                    )
                )

        if imported:
            await self._db.commit()

        return MCPDImportPersistenceResult(
            imported=imported,
            errors=tuple(errors),
        )
