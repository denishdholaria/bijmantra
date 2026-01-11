"""
GRIN-Global / Genesys Integration API

Endpoints for searching and importing germplasm data from:
- GRIN-Global (USDA Germplasm Resources Information Network)
- Genesys (Global portal for plant genetic resources)
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.services.grin_global import (
    GRINGlobalService,
    GenesysService,
    GRINAccession,
    GenesysSearchResult,
    get_demo_grin_accessions,
    get_demo_genesys_accessions
)

router = APIRouter(prefix="/grin", tags=["GRIN-Global Integration"])


# ============================================
# Schemas
# ============================================

class GRINSearchParams(BaseModel):
    """GRIN-Global search parameters."""
    genus: Optional[str] = None
    species: Optional[str] = None
    country: Optional[str] = None
    limit: int = 100


class GenesysSearchParams(BaseModel):
    """Genesys search parameters."""
    genus: Optional[str] = None
    species: Optional[str] = None
    country: Optional[str] = None
    available_only: bool = False
    limit: int = 100


class TaxonomyValidation(BaseModel):
    """Taxonomy validation result."""
    valid: bool
    accepted_name: Optional[str] = None
    synonyms: List[str] = []
    error: Optional[str] = None


class ImportResult(BaseModel):
    """Import result."""
    success: bool
    imported_count: int
    skipped_count: int
    errors: List[str] = []


# ============================================
# GRIN-Global Endpoints
# ============================================

@router.get("/grin-global/search", response_model=List[GRINAccession])
async def search_grin_global(
    genus: Optional[str] = Query(None, description="Genus name"),
    species: Optional[str] = Query(None, description="Species name"),
    country: Optional[str] = Query(None, description="Country code (ISO 3166-1 alpha-3)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    use_demo: bool = Query(True, description="Use demo data (set false for real API)")
):
    """
    Search GRIN-Global for accessions.
    
    Returns matching accessions with passport data.
    """
    if use_demo:
        # Use demo data for testing
        return await get_demo_grin_accessions(genus, species)
    
    # Real API call
    service = GRINGlobalService()
    try:
        results = await service.search_accessions(genus, species, country, limit)
        return results
    finally:
        await service.close()


@router.get("/grin-global/accession/{accession_number}", response_model=GRINAccession)
async def get_grin_accession(
    accession_number: str,
    use_demo: bool = Query(True, description="Use demo data")
):
    """
    Get a specific GRIN-Global accession by number.
    
    Args:
        accession_number: Accession number (e.g., "PI 123456")
    """
    if use_demo:
        # Search demo data
        results = await get_demo_grin_accessions()
        for acc in results:
            if acc.accession_number == accession_number:
                return acc
        raise HTTPException(status_code=404, detail="Accession not found")
    
    # Real API call
    service = GRINGlobalService()
    try:
        result = await service.get_accession(accession_number)
        if not result:
            raise HTTPException(status_code=404, detail="Accession not found")
        return result
    finally:
        await service.close()


@router.post("/grin-global/validate-taxonomy", response_model=TaxonomyValidation)
async def validate_taxonomy(
    genus: str = Query(..., description="Genus name"),
    species: str = Query(..., description="Species name"),
    subspecies: Optional[str] = Query(None, description="Subspecies name"),
    use_demo: bool = Query(True, description="Use demo data")
):
    """
    Validate taxonomy against GRIN-Global taxonomy database.
    
    Returns accepted name and synonyms if valid.
    """
    if use_demo:
        # Demo validation - accept common crops
        valid_taxa = {
            ("Oryza", "sativa"): "Oryza sativa L.",
            ("Triticum", "aestivum"): "Triticum aestivum L.",
            ("Zea", "mays"): "Zea mays L.",
            ("Glycine", "max"): "Glycine max (L.) Merr.",
        }
        
        key = (genus, species)
        if key in valid_taxa:
            return TaxonomyValidation(
                valid=True,
                accepted_name=valid_taxa[key],
                synonyms=[]
            )
        else:
            return TaxonomyValidation(
                valid=False,
                error="Taxon not found in database"
            )
    
    # Real API call
    service = GRINGlobalService()
    try:
        result = await service.validate_taxonomy(genus, species, subspecies)
        return TaxonomyValidation(**result)
    finally:
        await service.close()


# ============================================
# Genesys Endpoints
# ============================================

@router.get("/genesys/search", response_model=List[GenesysSearchResult])
async def search_genesys(
    genus: Optional[str] = Query(None, description="Genus name"),
    species: Optional[str] = Query(None, description="Species name"),
    country: Optional[str] = Query(None, description="Country code"),
    available_only: bool = Query(False, description="Only available accessions"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    use_demo: bool = Query(True, description="Use demo data")
):
    """
    Search Genesys for accessions.
    
    Genesys is the global portal for plant genetic resources information.
    """
    if use_demo:
        return await get_demo_genesys_accessions(genus, species)
    
    # Real API call
    service = GenesysService()
    try:
        results = await service.search_accessions(
            genus, species, country, available_only, limit
        )
        return results
    finally:
        await service.close()


@router.get("/genesys/accession/{institute_code}/{accession_number}")
async def get_genesys_accession(
    institute_code: str,
    accession_number: str,
    use_demo: bool = Query(True, description="Use demo data")
):
    """
    Get detailed information about a Genesys accession.
    
    Args:
        institute_code: Institute code (e.g., "USA", "IRRI")
        accession_number: Accession number
    """
    if use_demo:
        # Search demo data
        results = await get_demo_genesys_accessions()
        for acc in results:
            if (acc.institute_code == institute_code and 
                acc.accession_number == accession_number):
                return acc
        raise HTTPException(status_code=404, detail="Accession not found")
    
    # Real API call
    service = GenesysService()
    try:
        result = await service.get_accession_details(institute_code, accession_number)
        if not result:
            raise HTTPException(status_code=404, detail="Accession not found")
        return result
    finally:
        await service.close()


@router.get("/genesys/crops/{crop}/statistics")
async def get_crop_statistics(
    crop: str,
    use_demo: bool = Query(True, description="Use demo data")
):
    """
    Get statistics for a crop from Genesys.
    
    Returns accession count, countries, institutes, etc.
    """
    if use_demo:
        # Demo statistics
        demo_stats = {
            "rice": {
                "crop": "Rice",
                "accession_count": 125000,
                "countries": 120,
                "institutes": 450,
                "available_count": 85000
            },
            "wheat": {
                "crop": "Wheat",
                "accession_count": 95000,
                "countries": 95,
                "institutes": 380,
                "available_count": 62000
            },
            "maize": {
                "crop": "Maize",
                "accession_count": 78000,
                "countries": 85,
                "institutes": 320,
                "available_count": 54000
            }
        }
        
        if crop.lower() in demo_stats:
            return demo_stats[crop.lower()]
        else:
            return {
                "crop": crop,
                "accession_count": 0,
                "error": "Crop not found"
            }
    
    # Real API call
    service = GenesysService()
    try:
        return await service.get_crop_statistics(crop)
    finally:
        await service.close()


# ============================================
# Import Endpoints
# ============================================

@router.post("/import/grin-global", response_model=ImportResult)
async def import_from_grin_global(
    accession_numbers: List[str],
    organization_id: int
):
    """
    Import accessions from GRIN-Global into Seed Bank.
    
    Args:
        accession_numbers: List of accession numbers to import
        organization_id: Target organization ID
        
    Returns:
        Import result with counts and errors
    """
    # This would integrate with the Seed Bank module
    # For now, return a placeholder
    
    return ImportResult(
        success=True,
        imported_count=len(accession_numbers),
        skipped_count=0,
        errors=[]
    )


@router.post("/import/genesys", response_model=ImportResult)
async def import_from_genesys(
    accessions: List[dict],
    organization_id: int
):
    """
    Import accessions from Genesys into Seed Bank.
    
    Args:
        accessions: List of accession data (institute_code + accession_number)
        organization_id: Target organization ID
        
    Returns:
        Import result with counts and errors
    """
    # This would integrate with the Seed Bank module
    # For now, return a placeholder
    
    return ImportResult(
        success=True,
        imported_count=len(accessions),
        skipped_count=0,
        errors=[]
    )


# ============================================
# Utility Endpoints
# ============================================

@router.get("/status")
async def get_integration_status():
    """
    Get status of GRIN-Global and Genesys integrations.
    
    Returns connection status and available features.
    """
    return {
        "grin_global": {
            "available": True,
            "mode": "demo",
            "features": ["search", "taxonomy_validation", "accession_details"]
        },
        "genesys": {
            "available": True,
            "mode": "demo",
            "features": ["search", "accession_details", "crop_statistics"]
        },
        "note": "Set use_demo=false to use real APIs (requires configuration)"
    }
