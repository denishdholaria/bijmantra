"""
GRIN-Global / Genesys Integration Service

GRIN-Global is the USDA's Germplasm Resources Information Network database system.
Genesys is the global portal for plant genetic resources information.

This service provides:
- MCPD data exchange (already implemented in mcpd.py)
- Accession synchronization
- Passport data import/export
- Taxonomy validation
- Descriptor mapping

References:
- GRIN-Global: https://www.grin-global.org/
- Genesys: https://www.genesys-pgr.org/
- MCPD v2.1: https://www.bioversityinternational.org/e-library/publications/detail/faomulti-crop-passport-descriptors-v21-mcpd-v21/
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import httpx
from pydantic import BaseModel, Field


class GRINAccession(BaseModel):
    """GRIN-Global accession format."""
    accession_number: str
    genus: str
    species: str
    subspecies: Optional[str] = None
    variety: Optional[str] = None
    common_name: Optional[str] = None
    origin_country: Optional[str] = None
    collection_date: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation: Optional[float] = None
    biological_status: Optional[str] = None
    acquisition_source: Optional[str] = None
    storage_type: Optional[str] = None
    notes: Optional[str] = None


class GenesysSearchResult(BaseModel):
    """Genesys search result."""
    accession_id: str
    institute_code: str
    accession_number: str
    genus: str
    species: str
    country_of_origin: Optional[str] = None
    available: bool = False
    mlsStatus: Optional[str] = None  # Multilateral System status


class GRINGlobalService:
    """Service for GRIN-Global integration."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize GRIN-Global service.
        
        Args:
            base_url: GRIN-Global API base URL (if self-hosted)
            api_key: API key for authentication
        """
        self.base_url = base_url or "https://npgsweb.ars-grin.gov/gringlobal/api"
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_accessions(
        self,
        genus: Optional[str] = None,
        species: Optional[str] = None,
        country: Optional[str] = None,
        limit: int = 100
    ) -> List[GRINAccession]:
        """
        Search GRIN-Global for accessions.
        
        Args:
            genus: Genus name
            species: Species name
            country: Country of origin (ISO 3166-1 alpha-3)
            limit: Maximum results
            
        Returns:
            List of matching accessions
        """
        # Note: This is a placeholder - actual GRIN-Global API may differ
        # You'll need to adapt to the real API endpoints
        
        params = {
            "genus": genus,
            "species": species,
            "country": country,
            "limit": limit
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/accessions/search",
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            return [GRINAccession(**item) for item in data.get("results", [])]
        except httpx.HTTPError as e:
            print(f"GRIN-Global API error: {e}")
            return []
    
    async def get_accession(self, accession_number: str) -> Optional[GRINAccession]:
        """
        Get a specific accession by number.
        
        Args:
            accession_number: Accession number
            
        Returns:
            Accession data or None if not found
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/accessions/{accession_number}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            
            return GRINAccession(**data)
        except httpx.HTTPError:
            return None
    
    async def validate_taxonomy(
        self,
        genus: str,
        species: str,
        subspecies: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate taxonomy against GRIN-Global taxonomy database.
        
        Args:
            genus: Genus name
            species: Species name
            subspecies: Subspecies name
            
        Returns:
            Validation result with accepted name and synonyms
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/taxonomy/validate",
                params={
                    "genus": genus,
                    "species": species,
                    "subspecies": subspecies
                },
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "Bijmantra/0.1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class GenesysService:
    """Service for Genesys integration."""
    
    def __init__(self):
        """Initialize Genesys service."""
        self.base_url = "https://www.genesys-pgr.org/api/v1"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_accessions(
        self,
        genus: Optional[str] = None,
        species: Optional[str] = None,
        country: Optional[str] = None,
        available_only: bool = False,
        limit: int = 100
    ) -> List[GenesysSearchResult]:
        """
        Search Genesys for accessions.
        
        Args:
            genus: Genus name
            species: Species name
            country: Country of origin (ISO 3166-1 alpha-3)
            available_only: Only show available accessions
            limit: Maximum results
            
        Returns:
            List of matching accessions
        """
        params = {
            "genus": genus,
            "species": species,
            "country": country,
            "available": available_only,
            "limit": limit
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/accessions",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            return [GenesysSearchResult(**item) for item in data.get("data", [])]
        except httpx.HTTPError as e:
            print(f"Genesys API error: {e}")
            return []
    
    async def get_accession_details(
        self,
        institute_code: str,
        accession_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an accession.
        
        Args:
            institute_code: Institute code (e.g., "USA")
            accession_number: Accession number
            
        Returns:
            Accession details or None if not found
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/accessions/{institute_code}/{accession_number}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None
    
    async def get_crop_statistics(self, crop: str) -> Dict[str, Any]:
        """
        Get statistics for a crop.
        
        Args:
            crop: Crop name
            
        Returns:
            Statistics including accession count, countries, institutes
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/crops/{crop}/statistics"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e)
            }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Demo data for testing without external API
DEMO_GRIN_ACCESSIONS = [
    {
        "accession_number": "PI 123456",
        "genus": "Oryza",
        "species": "sativa",
        "subspecies": "indica",
        "common_name": "Rice",
        "origin_country": "IND",
        "biological_status": "Traditional cultivar/landrace",
        "storage_type": "Seed collection"
    },
    {
        "accession_number": "PI 234567",
        "genus": "Triticum",
        "species": "aestivum",
        "common_name": "Wheat",
        "origin_country": "USA",
        "biological_status": "Breeding/research material",
        "storage_type": "Seed collection"
    },
    {
        "accession_number": "PI 345678",
        "genus": "Zea",
        "species": "mays",
        "common_name": "Maize",
        "origin_country": "MEX",
        "biological_status": "Traditional cultivar/landrace",
        "storage_type": "Seed collection"
    }
]

DEMO_GENESYS_ACCESSIONS = [
    {
        "accession_id": "GEN001",
        "institute_code": "USA",
        "accession_number": "PI 123456",
        "genus": "Oryza",
        "species": "sativa",
        "country_of_origin": "India",
        "available": True,
        "mlsStatus": "INCLUDED"
    },
    {
        "accession_id": "GEN002",
        "institute_code": "IRRI",
        "accession_number": "IRGC 12345",
        "genus": "Oryza",
        "species": "sativa",
        "country_of_origin": "Philippines",
        "available": True,
        "mlsStatus": "INCLUDED"
    }
]


async def get_demo_grin_accessions(
    genus: Optional[str] = None,
    species: Optional[str] = None
) -> List[GRINAccession]:
    """Get demo GRIN accessions for testing."""
    results = DEMO_GRIN_ACCESSIONS
    
    if genus:
        results = [a for a in results if a["genus"].lower() == genus.lower()]
    
    if species:
        results = [a for a in results if a["species"].lower() == species.lower()]
    
    return [GRINAccession(**a) for a in results]


async def get_demo_genesys_accessions(
    genus: Optional[str] = None,
    species: Optional[str] = None
) -> List[GenesysSearchResult]:
    """Get demo Genesys accessions for testing."""
    results = DEMO_GENESYS_ACCESSIONS
    
    if genus:
        results = [a for a in results if a["genus"].lower() == genus.lower()]
    
    if species:
        results = [a for a in results if a["species"].lower() == species.lower()]
    
    return [GenesysSearchResult(**a) for a in results]
