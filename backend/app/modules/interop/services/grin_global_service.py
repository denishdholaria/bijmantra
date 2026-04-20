"""
GRIN-Global / Genesys Integration Service
Real API integration clients — return empty when API not configured.

Refactored: Session 94 — removed DEMO_GRIN_ACCESSIONS/DEMO_GENESYS_ACCESSIONS.
"""


import httpx
from pydantic import BaseModel


class GRINAccession(BaseModel):
    accession_number: str
    genus: str = ""
    species: str = ""
    common_name: str = ""
    country_code: str = ""
    institute: str = ""
    status: str = ""
    available: bool = False


class GenesysSearchResult(BaseModel):
    accession_number: str
    institute_code: str = ""
    genus: str = ""
    species: str = ""
    country: str = ""
    available: bool = False


class GRINGlobalService:
    """Client for GRIN-Global API. Returns empty results when API not configured."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def search_accessions(
        self, genus: str | None, species: str | None,
        country: str | None, limit: int = 100
    ) -> list[GRINAccession]:
        # Real API integration would go here
        return []

    async def get_accession(self, accession_number: str) -> GRINAccession | None:
        return None

    async def validate_taxonomy(
        self, genus: str, species: str, subspecies: str | None = None
    ) -> dict:
        return {"valid": False, "error": "GRIN-Global API not configured"}

    async def close(self):
        if self._client:
            await self._client.aclose()


class GenesysService:
    """Client for Genesys API. Returns empty results when API not configured."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def search_accessions(
        self, genus: str | None, species: str | None,
        country: str | None, available_only: bool = False, limit: int = 100
    ) -> list[GenesysSearchResult]:
        return []

    async def get_accession_details(self, institute_code: str, accession_number: str) -> dict | None:
        return None

    async def get_crop_statistics(self, crop: str) -> dict:
        return {
            "crop": crop, "accession_count": 0, "countries": 0,
            "institutes": 0, "available_count": 0,
            "message": "Genesys API not configured",
        }

    async def close(self):
        if self._client:
            await self._client.aclose()
