"""MCPD request and response DTOs owned by AccessionPassport."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MCPDRecord(BaseModel):
    """MCPD v2.1 compliant accession passport record."""

    # Identifiers
    PUID: str | None = Field(None, description="Persistent Unique Identifier (DOI)")
    INSTCODE: str | None = Field(None, description="FAO WIEWS institute code")
    ACCESSION_NUMBER: str = Field(..., alias="ACCENUMB", description="Accession number")
    COLLNUMB: str | None = Field(None, description="Collecting number")
    OTHERNUMB: str | None = Field(None, description="Other identifiers")

    # Collecting
    COLLCODE: str | None = Field(None, description="Collecting institute code")
    COLLNAME: str | None = Field(None, description="Collecting institute name")
    COLLINSTADDRESS: str | None = Field(None, description="Collecting institute address")
    COLLMISSID: str | None = Field(None, description="Collecting mission ID")
    COLLDATE: str | None = Field(None, description="Collection date (YYYYMMDD)")

    # Taxonomy
    GENUS: str = Field(..., description="Genus name")
    SPECIES: str | None = Field(None, description="Species epithet")
    SPAUTHOR: str | None = Field(None, description="Species authority")
    SUBTAXA: str | None = Field(None, description="Subtaxon")
    SUBTAUTHOR: str | None = Field(None, description="Subtaxon authority")
    CROPNAME: str | None = Field(None, description="Common crop name")

    # Accession info
    ACCENAME: str | None = Field(None, description="Accession name")
    ACQDATE: str | None = Field(None, description="Acquisition date (YYYYMMDD)")
    ORIGCTY: str | None = Field(None, description="Country of origin (ISO 3166-1 alpha-3)")

    # Geographic
    COLLSITE: str | None = Field(None, description="Collection site")
    LATITUDE: float | None = Field(None, ge=-90, le=90, description="Latitude (decimal)")
    LONGITUDE: float | None = Field(None, ge=-180, le=180, description="Longitude (decimal)")
    COORDUNCERT: float | None = Field(None, description="Coordinate uncertainty (m)")
    COORDDATUM: str | None = Field(None, description="Coordinate datum")
    GEOREFMETH: str | None = Field(None, description="Georeferencing method")
    ELEVATION: float | None = Field(None, description="Elevation (m)")

    # Breeding
    BREDCODE: str | None = Field(None, description="Breeding institute code")
    BREDNAME: str | None = Field(None, description="Breeding institute name")
    ANCEST: str | None = Field(None, description="Ancestral/pedigree data")

    # Donor
    DONORCODE: str | None = Field(None, description="Donor institute code")
    DONORNAME: str | None = Field(None, description="Donor institute name")
    DONORNUMB: str | None = Field(None, description="Donor accession number")

    # Status codes
    SAMPSTAT: int | None = Field(None, description="Biological status code")
    COLLSRC: int | None = Field(None, description="Acquisition source code")

    # Safety duplication
    DUPLSITE: str | None = Field(None, description="Safety duplicate site code")
    DUPLINSTNAME: str | None = Field(None, description="Safety duplicate institute name")

    # Storage
    STORAGE: str | None = Field(None, description="Storage type code(s)")

    # MLS
    MLSSTAT: int | None = Field(None, description="MLS status (0/1/99)")

    # Additional
    REMARKS: str | None = Field(None, description="Remarks")
    ACCEURL: str | None = Field(None, description="Accession URL")

    # Metadata
    MCPDVERSION: str = Field("2.1", description="MCPD version")

    model_config = ConfigDict(populate_by_name=True)


class MCPDImportResult(BaseModel):
    """Result of an MCPD import operation."""

    total_records: int
    imported: int
    skipped: int
    errors: list[dict[str, Any]]
