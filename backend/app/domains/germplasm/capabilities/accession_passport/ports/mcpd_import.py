"""Published MCPD import ports for AccessionPassport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class MCPDImportPersistenceError:
    """One adapter-level MCPD import persistence error."""

    row: int
    accession_number: str | None
    errors: tuple[str, ...]

    def as_response_dict(self) -> dict[str, Any]:
        return {
            "row": self.row,
            "accession_number": self.accession_number,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class MCPDImportPersistenceResult:
    """Result of writing planned MCPD accessions through a persistence adapter."""

    imported: int
    errors: tuple[MCPDImportPersistenceError, ...]

    def error_dicts(self) -> list[dict[str, Any]]:
        return [error.as_response_dict() for error in self.errors]


@runtime_checkable
class MCPDImportRepository(Protocol):
    """Port for duplicate checks and persistence during MCPD import."""

    async def list_existing_accession_numbers(self, organization_id: int) -> set[str]:
        """Return tenant-visible accession numbers that already exist."""

    async def persist_import_plan(
        self,
        *,
        organization_id: int,
        import_plan: Any,
    ) -> MCPDImportPersistenceResult:
        """Persist adapter-ready accessions from an MCPD import plan."""
