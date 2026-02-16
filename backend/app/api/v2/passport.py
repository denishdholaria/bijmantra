"""
Germplasm Passport API for Plant Breeding
FAO/IPGRI Multi-Crop Passport Descriptors (MCPD) compliant

Endpoints:
- POST /api/v2/passport/accessions - Register accession
- GET /api/v2/passport/accessions - List accessions
- GET /api/v2/passport/accessions/{id} - Get passport
- POST /api/v2/passport/accessions/{id}/collection-site - Add collection site
- GET /api/v2/passport/search - Search accessions
- GET /api/v2/passport/export/mcpd - Export MCPD format
- GET /api/v2/passport/statistics - Collection statistics
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, ConfigDict

from app.services.germplasm_passport import get_passport_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/passport", tags=["Germplasm Passport"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class AccessionRegisterRequest(BaseModel):
    """Request to register an accession"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "accession_id": "ACC-2025-001",
            "accession_name": "IR64",
            "genus": "Oryza",
            "species": "sativa",
            "species_authority": "L.",
            "common_name": "Rice",
            "biological_status": "500",
            "sample_type": "seed",
            "acquisition_source": "40",
            "acquisition_date": "2020-06-15",
            "donor_institute": "IRRI",
            "pedigree": "IR5657-33-2-1/IR2061-465-1-5-5",
            "storage_location": "ROOM-A-SHELF-1"
        }
    })

    accession_id: str = Field(..., description="Unique accession number")
    accession_name: str = Field(..., description="Accession name")
    genus: str = Field(..., description="Genus name")
    species: str = Field(..., description="Species epithet")
    species_authority: str = Field("", description="Species authority")
    subtaxa: str = Field("", description="Subtaxa (subspecies, variety)")
    common_name: str = Field("", description="Common/vernacular name")
    biological_status: str = Field("999", description="MCPD biological status code")
    sample_type: str = Field("seed", description="Sample type: seed, vegetative, dna, tissue")
    acquisition_source: str = Field("99", description="MCPD acquisition source code")
    acquisition_date: Optional[str] = Field(None, description="Acquisition date (YYYY-MM-DD)")
    donor_institute: str = Field("", description="Donor institute code")
    donor_accession: str = Field("", description="Donor accession number")
    pedigree: str = Field("", description="Pedigree/ancestry")
    remarks: str = Field("", description="Remarks")
    storage_location: str = Field("", description="Storage location")
    mls_status: str = Field("", description="MLS status")


class CollectionSiteRequest(BaseModel):
    """Request to add collection site"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "country": "IND",
            "state_province": "Odisha",
            "municipality": "Cuttack",
            "locality": "Near Mahanadi River",
            "latitude": 20.4625,
            "longitude": 85.8830,
            "elevation": 26,
            "collection_date": "2019-11-15",
            "collector_name": "Dr. R. Sharma",
            "collector_institute": "NRRI"
        }
    })

    country: str = Field(..., description="Country code (ISO 3166-1 alpha-3)")
    state_province: str = Field(..., description="State/Province")
    municipality: str = Field("", description="Municipality/District")
    locality: str = Field(..., description="Locality description")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude (decimal degrees)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude (decimal degrees)")
    elevation: Optional[float] = Field(None, description="Elevation (meters)")
    collection_date: Optional[str] = Field(None, description="Collection date (YYYY-MM-DD)")
    collector_name: str = Field("", description="Collector name")
    collector_institute: str = Field("", description="Collector institute code")


# ============================================
# ENDPOINTS
# ============================================

@router.post("/accessions")
async def register_accession(request: AccessionRegisterRequest):
    """
    Register a new germplasm accession
    
    Uses FAO/IPGRI Multi-Crop Passport Descriptors (MCPD) standard.
    """
    service = get_passport_service()

    try:
        passport = service.register_accession(
            accession_id=request.accession_id,
            accession_name=request.accession_name,
            genus=request.genus,
            species=request.species,
            species_authority=request.species_authority,
            subtaxa=request.subtaxa,
            common_name=request.common_name,
            biological_status=request.biological_status,
            sample_type=request.sample_type,
            acquisition_source=request.acquisition_source,
            acquisition_date=request.acquisition_date,
            donor_institute=request.donor_institute,
            donor_accession=request.donor_accession,
            pedigree=request.pedigree,
            remarks=request.remarks,
            storage_location=request.storage_location,
            mls_status=request.mls_status,
        )

        return {
            "success": True,
            "message": f"Accession {request.accession_id} registered",
            **passport.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register accession: {str(e)}")


@router.get("/accessions")
async def list_accessions(
    genus: Optional[str] = Query(None, description="Filter by genus"),
    species: Optional[str] = Query(None, description="Filter by species"),
    biological_status: Optional[str] = Query(None, description="Filter by biological status code"),
    country: Optional[str] = Query(None, description="Filter by collection country")
):
    """List germplasm accessions with optional filters"""
    service = get_passport_service()

    passports = service.list_passports(
        genus=genus,
        species=species,
        biological_status=biological_status,
        country=country,
    )

    return {
        "success": True,
        "count": len(passports),
        "filters": {
            "genus": genus,
            "species": species,
            "biological_status": biological_status,
            "country": country,
        },
        "accessions": passports,
    }


@router.get("/accessions/{accession_id}")
async def get_passport(accession_id: str):
    """Get passport data for an accession"""
    service = get_passport_service()

    passport = service.get_passport(accession_id)
    if passport is None:
        raise HTTPException(404, f"Accession {accession_id} not found")

    return {
        "success": True,
        **passport,
    }


@router.post("/accessions/{accession_id}/collection-site")
async def add_collection_site(accession_id: str, request: CollectionSiteRequest):
    """
    Add collection site information to an accession
    
    Records geographic origin and collection details.
    """
    service = get_passport_service()

    try:
        passport = service.add_collection_site(
            accession_id=accession_id,
            country=request.country,
            state_province=request.state_province,
            municipality=request.municipality,
            locality=request.locality,
            latitude=request.latitude,
            longitude=request.longitude,
            elevation=request.elevation,
            collection_date=request.collection_date,
            collector_name=request.collector_name,
            collector_institute=request.collector_institute,
        )

        return {
            "success": True,
            "message": f"Collection site added to {accession_id}",
            **passport.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to add collection site: {str(e)}")


@router.get("/search")
async def search_accessions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results")
):
    """
    Search accessions by name, ID, or taxonomy
    
    Searches across accession ID, name, genus, species, and common name.
    """
    service = get_passport_service()

    results = service.search(q, limit)

    return {
        "success": True,
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/export/mcpd")
async def export_mcpd(
    accession_ids: Optional[str] = Query(None, description="Comma-separated accession IDs (empty = all)")
):
    """
    Export passport data in MCPD format
    
    Multi-Crop Passport Descriptors format for data exchange.
    """
    service = get_passport_service()

    ids = accession_ids.split(",") if accession_ids else None
    mcpd_data = service.export_mcpd(ids)

    return {
        "success": True,
        "format": "MCPD",
        "count": len(mcpd_data),
        "data": mcpd_data,
    }


@router.get("/statistics")
async def get_statistics():
    """Get collection statistics"""
    service = get_passport_service()

    stats = service.get_statistics()

    return {
        "success": True,
        **stats,
    }


@router.get("/biological-status-codes")
async def list_biological_status_codes():
    """List MCPD biological status codes"""
    return {
        "codes": [
            {"code": "100", "name": "Wild", "description": "Wild material"},
            {"code": "200", "name": "Weedy", "description": "Weedy form"},
            {"code": "300", "name": "Traditional cultivar/Landrace", "description": "Traditional cultivar or landrace"},
            {"code": "400", "name": "Breeding/Research material", "description": "Breeding line or research material"},
            {"code": "500", "name": "Advanced/Improved cultivar", "description": "Advanced or improved cultivar"},
            {"code": "600", "name": "GMO", "description": "Genetically modified organism"},
            {"code": "999", "name": "Other", "description": "Other (elaborate in remarks)"},
        ]
    }


@router.get("/acquisition-source-codes")
async def list_acquisition_source_codes():
    """List MCPD acquisition source codes"""
    return {
        "codes": [
            {"code": "10", "name": "Wild habitat", "description": "Collected from wild habitat"},
            {"code": "20", "name": "Farm/Field", "description": "Collected from farm or cultivated field"},
            {"code": "30", "name": "Market", "description": "Obtained from market"},
            {"code": "40", "name": "Institute/Genebank", "description": "Obtained from research institute or genebank"},
            {"code": "50", "name": "Seed company", "description": "Obtained from seed company"},
            {"code": "99", "name": "Other", "description": "Other (elaborate in remarks)"},
        ]
    }
