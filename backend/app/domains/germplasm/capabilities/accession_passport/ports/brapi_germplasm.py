"""Published BrAPI germplasm records for Accession Passport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class BrAPIGermplasmRecord:
    """Capability-owned germplasm snapshot used for BrAPI response shaping."""

    germplasm_db_id: str
    germplasm_name: str
    germplasm_pui: str | None = None
    default_display_name: str | None = None
    accession_number: str | None = None
    species: str | None = None
    genus: str | None = None
    subtaxa: str | None = None
    common_crop_name: str | None = None
    institute_code: str | None = None
    institute_name: str | None = None
    biological_status_of_accession_code: str | None = None
    country_of_origin_code: str | None = None
    synonyms: tuple[str, ...] | None = None
    pedigree: str | None = None
    seed_source: str | None = None
    seed_source_description: str | None = None
    additional_info: dict[str, Any] | None = None
    external_references: Any = None


@dataclass(frozen=True)
class BrAPIGermplasmListQuery:
    """Capability-owned BrAPI germplasm list query."""

    page: int
    page_size: int
    organization_id: int | None = None
    germplasm_name: str | None = None
    common_crop_name: str | None = None
    species: str | None = None
    genus: str | None = None


@dataclass(frozen=True)
class BrAPIGermplasmListResult:
    """Result of a BrAPI germplasm list query."""

    records: tuple[BrAPIGermplasmRecord, ...]
    total: int


@dataclass(frozen=True)
class BrAPIGermplasmPedigreeQuery:
    """Capability-owned BrAPI germplasm pedigree query."""

    germplasm_db_id: str
    organization_id: int | None = None
    notation: str | None = None
    include_siblings: bool = False


@dataclass(frozen=True)
class BrAPIGermplasmPedigreeRelation:
    """Parent or sibling reference in a BrAPI pedigree response."""

    germplasm_db_id: str
    germplasm_name: str
    parent_type: str | None = None


@dataclass(frozen=True)
class BrAPIGermplasmPedigreeRecord:
    """Capability-owned BrAPI germplasm pedigree result."""

    germplasm_db_id: str
    germplasm_name: str
    pedigree: str
    crossing_project_db_id: str | None = None
    crossing_year: int | None = None
    family_code: str | None = None
    breeding_method_db_id: str | None = None
    breeding_method_name: str | None = None
    parents: tuple[BrAPIGermplasmPedigreeRelation, ...] = ()
    siblings: tuple[BrAPIGermplasmPedigreeRelation, ...] = ()


@dataclass(frozen=True)
class BrAPIGermplasmProgenyQuery:
    """Capability-owned BrAPI germplasm progeny query."""

    germplasm_db_id: str
    page: int
    page_size: int
    organization_id: int | None = None


@dataclass(frozen=True)
class BrAPIGermplasmProgenyRecord:
    """A progeny record for a BrAPI germplasm progeny response."""

    germplasm_db_id: str
    germplasm_name: str
    parent_type: str | None = None


@dataclass(frozen=True)
class BrAPIGermplasmProgenyResult:
    """Capability-owned BrAPI germplasm progeny result."""

    germplasm_db_id: str
    germplasm_name: str
    progeny: tuple[BrAPIGermplasmProgenyRecord, ...]
    total: int


@dataclass(frozen=True)
class BrAPIGermplasmMCPDQuery:
    """Capability-owned BrAPI germplasm MCPD query."""

    germplasm_db_id: str
    organization_id: int | None = None


@dataclass(frozen=True)
class BrAPIGermplasmMCPDRecord:
    """Capability-owned BrAPI germplasm MCPD result."""

    germplasm_db_id: str
    accession_number: str | None
    accession_names: tuple[str, ...]
    acquisition_date: Any = None
    acquisition_source_code: str | None = None
    alternate_ids: tuple[str, ...] = ()
    ancestral_data: str | None = None
    biological_status_of_accession_code: str | None = None
    breeding_institutes: tuple[str, ...] = ()
    collecting_date: Any = None
    collecting_institutes: tuple[str, ...] = ()
    collecting_mission_identifier: str | None = None
    collecting_number: str | None = None
    collecting_site: str | None = None
    common_crop_name: str | None = None
    country_of_origin: str | None = None
    donor_accession_number: str | None = None
    donor_accession_pui: str | None = None
    donor_institute: str | None = None
    genus: str | None = None
    germplasm_pui: str | None = None
    institute_code: str | None = None
    mls_status: str | None = None
    remarks: str | None = None
    safety_duplicate_institutes: tuple[str, ...] = ()
    species: str | None = None
    species_authority: str | None = None
    storage_type_codes: tuple[str, ...] = ()
    subtaxon: str | None = None
    subtaxon_authority: str | None = None


@dataclass(frozen=True)
class BrAPIGermplasmMutationData:
    """Capability-owned BrAPI germplasm mutation payload."""

    germplasm_name: str
    accession_number: str | None = None
    germplasm_pui: str | None = None
    default_display_name: str | None = None
    species: str | None = None
    genus: str | None = None
    subtaxa: str | None = None
    common_crop_name: str | None = None
    institute_code: str | None = None
    institute_name: str | None = None
    biological_status_of_accession_code: str | None = None
    country_of_origin_code: str | None = None
    synonyms: tuple[str, ...] | None = None
    pedigree: str | None = None
    seed_source: str | None = None
    seed_source_description: str | None = None


@dataclass(frozen=True)
class BrAPIGermplasmCreateCommand:
    """Command to create a tenant-owned BrAPI germplasm record."""

    organization_id: int
    actor_id: int | None
    data: BrAPIGermplasmMutationData


@dataclass(frozen=True)
class BrAPIGermplasmUpdateCommand:
    """Command to update a tenant-visible BrAPI germplasm record."""

    germplasm_db_id: str
    organization_id: int
    actor_id: int | None
    data: BrAPIGermplasmMutationData


@dataclass(frozen=True)
class BrAPIGermplasmDeleteCommand:
    """Command to delete a tenant-visible BrAPI germplasm record."""

    germplasm_db_id: str
    organization_id: int
    actor_id: int | None


@runtime_checkable
class BrAPIGermplasmReadRepository(Protocol):
    """Port for BrAPI germplasm read access."""

    async def list_germplasm(
        self,
        query: BrAPIGermplasmListQuery,
    ) -> BrAPIGermplasmListResult:
        """Return tenant-visible germplasm records for a BrAPI list query."""

    async def get_germplasm(
        self,
        *,
        germplasm_db_id: str,
        organization_id: int | None = None,
    ) -> BrAPIGermplasmRecord | None:
        """Return one tenant-visible germplasm record by BrAPI identifier."""

    async def get_pedigree(
        self,
        query: BrAPIGermplasmPedigreeQuery,
    ) -> BrAPIGermplasmPedigreeRecord | None:
        """Return tenant-visible pedigree data for one germplasm."""

    async def get_progeny(
        self,
        query: BrAPIGermplasmProgenyQuery,
    ) -> BrAPIGermplasmProgenyResult | None:
        """Return tenant-visible progeny data for one germplasm."""

    async def get_mcpd(
        self,
        query: BrAPIGermplasmMCPDQuery,
    ) -> BrAPIGermplasmMCPDRecord | None:
        """Return tenant-visible MCPD data for one germplasm."""


@runtime_checkable
class BrAPIGermplasmWriteRepository(Protocol):
    """Port for BrAPI germplasm mutation persistence."""

    async def create_germplasm(
        self,
        command: BrAPIGermplasmCreateCommand,
    ) -> BrAPIGermplasmRecord:
        """Create and audit a tenant-owned germplasm record."""

    async def update_germplasm(
        self,
        command: BrAPIGermplasmUpdateCommand,
    ) -> BrAPIGermplasmRecord | None:
        """Update and audit a tenant-visible germplasm record."""

    async def delete_germplasm(
        self,
        command: BrAPIGermplasmDeleteCommand,
    ) -> bool:
        """Delete and audit a tenant-visible germplasm record."""
