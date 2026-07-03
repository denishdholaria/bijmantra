"""MCPD accession import planning use cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.germplasm.capabilities.accession_passport.domain import (
    mcpd_to_accession_data,
    parse_mcpd_csv,
    validate_mcpd_record,
)
from app.domains.germplasm.capabilities.accession_passport.ports import (
    MCPDImportRepository,
)


class MCPDImportParseError(ValueError):
    """Raised when an MCPD CSV payload cannot be parsed or planned."""


class EmptyMCPDImportError(ValueError):
    """Raised when an MCPD CSV payload contains no records."""


@dataclass(frozen=True)
class MCPDImportErrorRecord:
    """One MCPD import planning error."""

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
class PlannedMCPDAccession:
    """An adapter-ready accession create candidate."""

    row: int
    accession_number: str
    accession_data: dict[str, Any]


@dataclass(frozen=True)
class MCPDImportPlan:
    """Pure application plan for an MCPD import request."""

    total_records: int
    accepted_count: int
    skipped: int
    errors: tuple[MCPDImportErrorRecord, ...]
    accessions_to_create: tuple[PlannedMCPDAccession, ...]

    def error_dicts(self) -> list[dict[str, Any]]:
        return [error.as_response_dict() for error in self.errors]


@dataclass(frozen=True)
class MCPDImportExecutionResult:
    """Application-level result of an MCPD import request."""

    total_records: int
    imported: int
    skipped: int
    errors: tuple[dict[str, Any], ...]


def _public_accession_data(mcpd_row: dict[str, Any]) -> dict[str, Any]:
    accession_data = mcpd_to_accession_data(mcpd_row)
    return {key: value for key, value in accession_data.items() if not key.startswith("_")}


def plan_mcpd_accession_import(
    csv_content: str,
    *,
    existing_accession_numbers: set[str],
    skip_duplicates: bool,
    validate_only: bool,
) -> MCPDImportPlan:
    """Plan MCPD accession import work without touching persistence."""

    records = parse_mcpd_csv(csv_content)
    seen_numbers = set(existing_accession_numbers)
    accepted_count = 0
    skipped = 0
    errors: list[MCPDImportErrorRecord] = []
    accessions_to_create: list[PlannedMCPDAccession] = []

    for row_number, row in enumerate(records, start=2):
        validation_errors = validate_mcpd_record(row)
        accession_number = row.get("ACCENUMB")
        if validation_errors:
            errors.append(
                MCPDImportErrorRecord(
                    row=row_number,
                    accession_number=accession_number,
                    errors=tuple(validation_errors),
                )
            )
            continue

        if accession_number in seen_numbers:
            if skip_duplicates:
                skipped += 1
            else:
                errors.append(
                    MCPDImportErrorRecord(
                        row=row_number,
                        accession_number=accession_number,
                        errors=("Accession number already exists",),
                    )
                )
            continue

        accepted_count += 1
        if validate_only:
            continue

        accessions_to_create.append(
            PlannedMCPDAccession(
                row=row_number,
                accession_number=accession_number or "",
                accession_data=_public_accession_data(row),
            )
        )
        if accession_number:
            seen_numbers.add(accession_number)

    return MCPDImportPlan(
        total_records=len(records),
        accepted_count=accepted_count,
        skipped=skipped,
        errors=tuple(errors),
        accessions_to_create=tuple(accessions_to_create),
    )


async def import_mcpd_accessions(
    csv_content: str,
    *,
    repository: MCPDImportRepository,
    organization_id: int,
    skip_duplicates: bool,
    validate_only: bool,
) -> MCPDImportExecutionResult:
    """Execute MCPD accession import policy through a repository port."""

    existing_numbers = await repository.list_existing_accession_numbers(organization_id)

    try:
        import_plan = plan_mcpd_accession_import(
            csv_content,
            existing_accession_numbers=existing_numbers,
            skip_duplicates=skip_duplicates,
            validate_only=validate_only,
        )
    except Exception as exc:
        raise MCPDImportParseError(str(exc)) from exc

    if not import_plan.total_records:
        raise EmptyMCPDImportError("No records found in CSV file")

    imported = import_plan.accepted_count if validate_only else 0
    errors = import_plan.error_dicts()

    if not validate_only:
        persistence_result = await repository.persist_import_plan(
            organization_id=organization_id,
            import_plan=import_plan,
        )
        imported = persistence_result.imported
        errors.extend(persistence_result.error_dicts())

    return MCPDImportExecutionResult(
        total_records=import_plan.total_records,
        imported=imported,
        skipped=import_plan.skipped,
        errors=tuple(errors),
    )
