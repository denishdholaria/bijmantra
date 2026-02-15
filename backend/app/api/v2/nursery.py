"""
Nursery Management API for Plant Breeding
Breeding nursery planning, tracking, and management

Endpoints:
- POST /api/v2/nursery/nurseries - Create nursery
- GET /api/v2/nursery/nurseries - List nurseries
- GET /api/v2/nursery/nurseries/{id} - Get nursery details
- POST /api/v2/nursery/nurseries/{id}/entries - Add entry
- POST /api/v2/nursery/nurseries/{id}/entries/bulk - Bulk add entries
- POST /api/v2/nursery/entries/{id}/selection - Record selection
- POST /api/v2/nursery/advance - Advance selections
- GET /api/v2/nursery/nurseries/{id}/summary - Get summary
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, ConfigDict

from app.services.nursery import get_nursery_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/nursery", tags=["Nursery Management"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class NurseryCreateRequest(BaseModel):
    """Request to create a nursery"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Rice OYT 2025 Kharif",
            "nursery_type": "observation",
            "season": "Kharif",
            "year": 2025,
            "location": "NRRI Cuttack",
            "sowing_date": "2025-06-15",
            "notes": "Observation yield trial"
        }
    })

    name: str = Field(..., description="Nursery name")
    nursery_type: str = Field(..., description="Type: observation, preliminary, advanced, elite, crossing_block, seed_increase")
    season: str = Field(..., description="Season (e.g., Kharif, Rabi, Wet, Dry)")
    year: int = Field(..., ge=2000, le=2100, description="Year")
    location: str = Field(..., description="Location/station")
    sowing_date: Optional[str] = Field(None, description="Sowing date (YYYY-MM-DD)")
    notes: str = Field("", description="Notes")


class EntryAddRequest(BaseModel):
    """Request to add an entry"""
    genotype_id: str = Field(..., description="Genotype ID")
    genotype_name: str = Field(..., description="Genotype name")
    pedigree: str = Field("", description="Pedigree")
    source_nursery: str = Field("", description="Source nursery ID")


class BulkEntryRequest(BaseModel):
    """Request to add multiple entries"""
    entries: List[EntryAddRequest]


class SelectionRequest(BaseModel):
    """Request to record selection decision"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "decision": "advance",
            "notes": "Good yield, disease resistant",
            "seed_harvested": 250.0
        }
    })

    decision: str = Field(..., description="Decision: advance, reject, hold, release")
    notes: str = Field("", description="Selection notes")
    seed_harvested: float = Field(0.0, ge=0, description="Seed harvested (grams)")


class AdvanceRequest(BaseModel):
    """Request to advance selections"""
    source_nursery_id: str = Field(..., description="Source nursery ID")
    target_nursery_id: str = Field(..., description="Target nursery ID")


class StatusUpdateRequest(BaseModel):
    """Request to update nursery status"""
    status: str = Field(..., description="Status: planned, active, completed")
    harvest_date: Optional[str] = Field(None, description="Harvest date (YYYY-MM-DD)")


# ============================================
# ENDPOINTS
# ============================================

@router.post("/nurseries")
async def create_nursery(request: NurseryCreateRequest):
    """
    Create a new breeding nursery
    
    Nursery types:
    - observation: Initial observation (OYT)
    - preliminary: Preliminary yield trial (PYT)
    - advanced: Advanced yield trial (AYT)
    - elite: Elite lines for release
    - crossing_block: Crossing block
    - seed_increase: Seed multiplication
    """
    service = get_nursery_service()
    
    try:
        nursery = service.create_nursery(
            name=request.name,
            nursery_type=request.nursery_type,
            season=request.season,
            year=request.year,
            location=request.location,
            sowing_date=request.sowing_date,
            notes=request.notes,
        )
        
        return {
            "success": True,
            "message": f"Nursery {nursery.nursery_id} created",
            **nursery.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to create nursery: {str(e)}")


@router.get("/nurseries")
async def list_nurseries(
    year: Optional[int] = Query(None, description="Filter by year"),
    nursery_type: Optional[str] = Query(None, description="Filter by type"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """List nurseries with optional filters"""
    service = get_nursery_service()
    
    nurseries = service.list_nurseries(
        year=year,
        nursery_type=nursery_type,
        status=status,
    )
    
    return {
        "success": True,
        "count": len(nurseries),
        "filters": {"year": year, "nursery_type": nursery_type, "status": status},
        "nurseries": nurseries,
    }


@router.get("/nurseries/{nursery_id}")
async def get_nursery(nursery_id: str):
    """Get nursery details with all entries"""
    service = get_nursery_service()
    
    nursery = service.get_nursery(nursery_id)
    if nursery is None:
        raise HTTPException(404, f"Nursery {nursery_id} not found")
    
    return {
        "success": True,
        **nursery,
    }


@router.post("/nurseries/{nursery_id}/entries")
async def add_entry(nursery_id: str, request: EntryAddRequest):
    """Add an entry to a nursery"""
    service = get_nursery_service()
    
    try:
        entry = service.add_entry(
            nursery_id=nursery_id,
            genotype_id=request.genotype_id,
            genotype_name=request.genotype_name,
            pedigree=request.pedigree,
            source_nursery=request.source_nursery,
        )
        
        return {
            "success": True,
            "message": f"Entry {entry.entry_id} added",
            **entry.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to add entry: {str(e)}")


@router.post("/nurseries/{nursery_id}/entries/bulk")
async def bulk_add_entries(nursery_id: str, request: BulkEntryRequest):
    """Add multiple entries to a nursery"""
    service = get_nursery_service()
    
    try:
        entries_data = [e.model_dump() for e in request.entries]
        result = service.bulk_add_entries(nursery_id, entries_data)
        
        return {
            "success": True,
            "nursery_id": nursery_id,
            **result,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to add entries: {str(e)}")


@router.post("/entries/{entry_id}/selection")
async def record_selection(entry_id: str, request: SelectionRequest):
    """
    Record selection decision for an entry
    
    Decisions:
    - advance: Promote to next stage
    - reject: Discard
    - hold: Keep for re-evaluation
    - release: Recommend for variety release
    """
    service = get_nursery_service()
    
    try:
        entry = service.record_selection(
            entry_id=entry_id,
            decision=request.decision,
            notes=request.notes,
            seed_harvested=request.seed_harvested,
        )
        
        return {
            "success": True,
            "message": f"Selection recorded: {request.decision}",
            **entry.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to record selection: {str(e)}")


@router.post("/advance")
async def advance_selections(request: AdvanceRequest):
    """
    Advance selected entries to next nursery
    
    Copies all entries with 'advance' decision to target nursery.
    """
    service = get_nursery_service()
    
    try:
        result = service.advance_selections(
            source_nursery_id=request.source_nursery_id,
            target_nursery_id=request.target_nursery_id,
        )
        
        return {
            "success": True,
            "message": f"{result['entries_advanced']} entries advanced",
            **result,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to advance selections: {str(e)}")


@router.patch("/nurseries/{nursery_id}/status")
async def update_status(nursery_id: str, request: StatusUpdateRequest):
    """Update nursery status"""
    service = get_nursery_service()
    
    try:
        nursery = service.update_nursery_status(
            nursery_id=nursery_id,
            status=request.status,
            harvest_date=request.harvest_date,
        )
        
        return {
            "success": True,
            "message": f"Status updated to {request.status}",
            **nursery.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to update status: {str(e)}")


@router.get("/nurseries/{nursery_id}/summary")
async def get_nursery_summary(nursery_id: str):
    """
    Get selection summary for a nursery
    
    Returns counts by selection decision and selection rate.
    """
    service = get_nursery_service()
    
    try:
        summary = service.get_nursery_summary(nursery_id)
        return {
            "success": True,
            **summary,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/types")
async def list_nursery_types():
    """List nursery types"""
    return {
        "types": [
            {"id": "observation", "name": "Observation Yield Trial (OYT)", "description": "Initial evaluation of new lines"},
            {"id": "preliminary", "name": "Preliminary Yield Trial (PYT)", "description": "First replicated yield trial"},
            {"id": "advanced", "name": "Advanced Yield Trial (AYT)", "description": "Multi-location yield trial"},
            {"id": "elite", "name": "Elite Trial", "description": "Final evaluation before release"},
            {"id": "crossing_block", "name": "Crossing Block", "description": "Parents for hybridization"},
            {"id": "seed_increase", "name": "Seed Increase", "description": "Seed multiplication"},
        ]
    }
