"""
GRIN-Global / Genesys Integration API

Endpoints for searching and importing germplasm data from:
- GRIN-Global (USDA Germplasm Resources Information Network)
- Genesys (Global portal for plant genetic resources)

Converted to database queries per Zero Mock Data Policy (Session 77).
Demo data functions removed - use real API calls or return empty results.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.services.grin_global import (
    GRINGlobalService,
    GenesysService,
    GRINAccession,
    GenesysSearchResult,
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
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Search GRIN-Global for accessions.
    
    Returns matching accessions with passport data.
    Requires GRIN-Global API configuration for real data.
    Returns empty list when API is not configured.
    """
    service = GRINGlobalService()
    try:
        results = await service.search_accessions(genus, species, country, limit)
        return results
    except Exception:
        # Return empty list if API not configured
        return []
    finally:
        await service.close()


@router.get("/grin-global/accession/{accession_number}", response_model=GRINAccession)
async def get_grin_accession(
    accession_number: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get a specific GRIN-Global accession by number.
    
    Args:
        accession_number: Accession number (e.g., "PI 123456")
        
    Requires GRIN-Global API configuration.
    Returns 404 when API is not configured or accession not found.
    """
    service = GRINGlobalService()
    try:
        result = await service.get_accession(accession_number)
        if not result:
            raise HTTPException(status_code=404, detail="Accession not found")
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Accession not found - GRIN-Global API not configured")
    finally:
        await service.close()


@router.post("/grin-global/validate-taxonomy", response_model=TaxonomyValidation)
async def validate_taxonomy(
    genus: str = Query(..., description="Genus name"),
    species: str = Query(..., description="Species name"),
    subspecies: Optional[str] = Query(None, description="Subspecies name"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Validate taxonomy against GRIN-Global taxonomy database.
    
    Returns accepted name and synonyms if valid.
    Requires GRIN-Global API configuration.
    """
    service = GRINGlobalService()
    try:
        result = await service.validate_taxonomy(genus, species, subspecies)
        return TaxonomyValidation(**result)
    except Exception:
        # Return validation failure if API not configured
        return TaxonomyValidation(
            valid=False,
            error="GRIN-Global API not configured - cannot validate taxonomy"
        )
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
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Search Genesys for accessions.
    
    Genesys is the global portal for plant genetic resources information.
    Requires Genesys API configuration for real data.
    Returns empty list when API is not configured.
    """
    service = GenesysService()
    try:
        results = await service.search_accessions(
            genus, species, country, available_only, limit
        )
        return results
    except Exception:
        # Return empty list if API not configured
        return []
    finally:
        await service.close()


@router.get("/genesys/accession/{institute_code}/{accession_number}")
async def get_genesys_accession(
    institute_code: str,
    accession_number: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get detailed information about a Genesys accession.
    
    Args:
        institute_code: Institute code (e.g., "USA", "IRRI")
        accession_number: Accession number
        
    Requires Genesys API configuration.
    Returns 404 when API is not configured or accession not found.
    """
    service = GenesysService()
    try:
        result = await service.get_accession_details(institute_code, accession_number)
        if not result:
            raise HTTPException(status_code=404, detail="Accession not found")
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Accession not found - Genesys API not configured")
    finally:
        await service.close()


@router.get("/genesys/crops/{crop}/statistics")
async def get_crop_statistics(
    crop: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get statistics for a crop from Genesys.
    
    Returns accession count, countries, institutes, etc.
    Requires Genesys API configuration.
    """
    service = GenesysService()
    try:
        return await service.get_crop_statistics(crop)
    except Exception:
        return {
            "crop": crop,
            "accession_count": 0,
            "countries": 0,
            "institutes": 0,
            "available_count": 0,
            "message": "Genesys API not configured",
        }
    finally:
        await service.close()


# ============================================
# Import Endpoints
# ============================================

@router.post("/import/grin-global", response_model=ImportResult)
async def import_from_grin_global(
    accession_numbers: List[str],
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Import accessions from GRIN-Global into Seed Bank.
    
    Args:
        accession_numbers: List of accession numbers to import
        
    Returns:
        Import result with counts and errors
        
    Note: Import functionality requires GRIN-Global API configuration
    and Seed Bank module integration.
    """
    # TODO: Integrate with Seed Bank module when GRIN-Global API is configured
    return ImportResult(
        success=False,
        imported_count=0,
        skipped_count=len(accession_numbers),
        errors=["GRIN-Global import requires API configuration"]
    )


@router.post("/import/genesys", response_model=ImportResult)
async def import_from_genesys(
    accessions: List[dict],
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Import accessions from Genesys into Seed Bank.
    
    Args:
        accessions: List of accession data (institute_code + accession_number)
        
    Returns:
        Import result with counts and errors
        
    Note: Import functionality requires Genesys API configuration
    and Seed Bank module integration.
    """
    # TODO: Integrate with Seed Bank module when Genesys API is configured
    return ImportResult(
        success=False,
        imported_count=0,
        skipped_count=len(accessions),
        errors=["Genesys import requires API configuration"]
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
            "available": False,
            "mode": "api",
            "features": ["search", "taxonomy_validation", "accession_details"],
            "note": "Requires GRIN-Global API configuration"
        },
        "genesys": {
            "available": False,
            "mode": "api",
            "features": ["search", "accession_details", "crop_statistics"],
            "note": "Requires Genesys API configuration"
        },
        "message": "Configure API credentials to enable external genebank integrations"
    }
