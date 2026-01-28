"""
Seed Inventory API for Seed Bank Management
Seed lot tracking, viability testing, and inventory management

Endpoints:
- POST /api/v2/seed-inventory/lots - Register seed lot
- GET /api/v2/seed-inventory/lots - List seed lots
- GET /api/v2/seed-inventory/lots/{lot_id} - Get lot details
- POST /api/v2/seed-inventory/viability - Record viability test
- GET /api/v2/seed-inventory/viability/{lot_id} - Get viability history
- POST /api/v2/seed-inventory/requests - Create seed request
- POST /api/v2/seed-inventory/requests/{id}/approve - Approve request
- POST /api/v2/seed-inventory/requests/{id}/ship - Ship request
- GET /api/v2/seed-inventory/summary - Inventory summary
- GET /api/v2/seed-inventory/alerts - Get alerts
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.seed_inventory import get_seed_inventory_service
from app.api.deps import get_db, get_organization_id

router = APIRouter(prefix="/seed-inventory", tags=["Seed Inventory"])


# ============================================
# SCHEMAS
# ============================================

class SeedLotRequest(BaseModel):
    """Request to register a seed lot"""
    accession_id: str = Field(..., description="Accession identifier")
    species: str = Field(..., description="Species name")
    variety: str = Field(..., description="Variety/cultivar name")
    harvest_date: str = Field(..., description="Harvest date (YYYY-MM-DD)")
    quantity: float = Field(..., gt=0, description="Quantity in grams")
    storage_type: str = Field(..., description="Storage type: short_term, medium_term, long_term, cryo")
    storage_location: str = Field(..., description="Storage location code")
    initial_viability: float = Field(..., ge=0, le=100, description="Initial germination %")
    notes: str = Field("", description="Additional notes")
    
    # Extended fields
    seed_class: Optional[str] = Field(None, description="Seed class (foundation, certified, etc)")
    purity_percent: Optional[float] = Field(None, ge=0, le=100, description="Purity percentage")
    moisture_percent: Optional[float] = Field(None, ge=0, le=100, description="Moisture percentage")
    production_year: Optional[int] = Field(None, description="Year of production")
    producer_name: Optional[str] = Field(None, description="Name of producer")
    production_location: Optional[str] = Field(None, description="Location of production")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "accession_id": "ACC-001",
            "species": "Oryza sativa",
            "variety": "IR64",
            "harvest_date": "2024-06-15",
            "quantity": 500.0,
            "storage_type": "medium_term",
            "storage_location": "ROOM-A-SHELF-3",
            "initial_viability": 95.0,
            "notes": "Foundation seed",
            "seed_class": "foundation",
            "purity_percent": 99.5,
            "moisture_percent": 12.0,
            "production_year": 2024,
            "producer_name": "ABC Seeds",
            "production_location": "Farm A"
        }
    })


class ViabilityTestRequest(BaseModel):
    """Request to record viability test"""
    lot_id: str = Field(..., description="Seed lot ID")
    test_date: str = Field(..., description="Test date (YYYY-MM-DD)")
    seeds_tested: int = Field(..., ge=1, description="Number of seeds tested")
    seeds_germinated: int = Field(..., ge=0, description="Number germinated")
    test_method: str = Field(..., description="Testing method")
    tester: str = Field(..., description="Person who conducted test")
    notes: str = Field("", description="Additional notes")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "lot_id": "LOT-000001",
            "test_date": "2025-01-15",
            "seeds_tested": 100,
            "seeds_germinated": 92,
            "test_method": "Standard germination test",
            "tester": "Dr. Smith",
            "notes": "Normal conditions"
        }
    })


class SeedRequestCreate(BaseModel):
    """Request to create seed distribution request"""
    lot_id: str = Field(..., description="Seed lot ID")
    requester: str = Field(..., description="Requester name")
    institution: str = Field(..., description="Institution name")
    quantity: float = Field(..., gt=0, description="Quantity requested (grams)")
    purpose: str = Field("", description="Purpose of request")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "lot_id": "LOT-000001",
            "requester": "Dr. Jane Doe",
            "institution": "University of Agriculture",
            "quantity": 50.0,
            "purpose": "Research trial"
        }
    })


class ApproveRequest(BaseModel):
    """Request to approve seed request"""
    quantity_approved: float = Field(..., gt=0, description="Quantity approved (grams)")


# ============================================
# ENDPOINTS
# ============================================

@router.post("/lots")
async def register_seed_lot(
    request: SeedLotRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """
    Register a new seed lot
    
    Creates a new seed lot record with initial inventory and viability data.
    """
    service = get_seed_inventory_service()
    
    try:
        lot = await service.register_seed_lot(
            db=db,
            organization_id=organization_id,
            accession_id=request.accession_id,
            species=request.species,
            variety=request.variety,
            harvest_date=request.harvest_date,
            quantity=request.quantity,
            storage_type=request.storage_type,
            storage_location=request.storage_location,
            initial_viability=request.initial_viability,
            notes=request.notes,
            # Extended fields
            seed_class=request.seed_class,
            purity_percent=request.purity_percent,
            moisture_percent=request.moisture_percent,
            production_year=request.production_year,
            producer_name=request.producer_name,
            production_location=request.production_location,
        )
        
        return {
            "success": True,
            "message": f"Seed lot {lot.lot_id} registered",
            **lot.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register seed lot: {str(e)}")


@router.get("/lots")
async def list_seed_lots(
    species: Optional[str] = Query(None, description="Filter by species"),
    status: Optional[str] = Query(None, description="Filter by status"),
    storage_type: Optional[str] = Query(None, description="Filter by storage type"),
    db: AsyncSession = Depends(get_db)
):
    """List seed lots with optional filters"""
    service = get_seed_inventory_service()
    
    lots = await service.list_lots(
        db=db,
        species=species,
        status=status,
        storage_type=storage_type,
    )
    
    return {
        "success": True,
        "count": len(lots),
        "filters": {"species": species, "status": status, "storage_type": storage_type},
        "lots": lots,
    }


@router.get("/lots/{lot_id}")
async def get_seed_lot(
    lot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get seed lot details"""
    service = get_seed_inventory_service()
    
    lot = await service.get_lot(db, lot_id)
    if lot is None:
        raise HTTPException(404, f"Seed lot {lot_id} not found")
    
    return {
        "success": True,
        **lot,
    }


@router.post("/viability")
async def record_viability_test(
    request: ViabilityTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record a viability test result
    
    Updates the lot's current viability and test date.
    Automatically flags lots with low viability.
    """
    service = get_seed_inventory_service()
    
    try:
        if request.seeds_germinated > request.seeds_tested:
            raise HTTPException(400, "Germinated seeds cannot exceed tested seeds")
        
        test = await service.record_viability_test(
            db=db,
            lot_id=request.lot_id,
            test_date=request.test_date,
            seeds_tested=request.seeds_tested,
            seeds_germinated=request.seeds_germinated,
            test_method=request.test_method,
            tester=request.tester,
            notes=request.notes,
        )
        
        return {
            "success": True,
            "message": f"Viability test recorded: {test.germination_percent:.1f}%",
            **test.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to record test: {str(e)}")


@router.get("/viability/{lot_id}")
async def get_viability_history(
    lot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get viability test history for a seed lot"""
    service = get_seed_inventory_service()
    
    history = await service.get_viability_history(db, lot_id)
    
    return {
        "success": True,
        "lot_id": lot_id,
        "test_count": len(history),
        "tests": history,
    }


@router.post("/requests")
async def create_seed_request(
    request: SeedRequestCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id)
):
    """
    Create a seed distribution request
    
    Request must be approved before seeds can be shipped.
    """
    service = get_seed_inventory_service()
    
    try:
        req = await service.create_request(
            db=db,
            organization_id=organization_id,
            lot_id=request.lot_id,
            requester=request.requester,
            institution=request.institution,
            quantity=request.quantity,
            purpose=request.purpose,
        )
        
        return {
            "success": True,
            "message": f"Request {req.request_id} created",
            **req.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to create request: {str(e)}")


@router.post("/requests/{request_id}/approve")
async def approve_seed_request(
    request_id: str,
    request: ApproveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a seed distribution request
    
    Validates that sufficient stock is available.
    """
    service = get_seed_inventory_service()
    
    try:
        req = await service.approve_request(db, request_id, request.quantity_approved)
        
        return {
            "success": True,
            "message": f"Request {request_id} approved for {request.quantity_approved}g",
            **req.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to approve request: {str(e)}")


@router.post("/requests/{request_id}/ship")
async def ship_seed_request(
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark request as shipped
    
    Deducts approved quantity from inventory.
    Updates lot status if stock becomes low.
    """
    service = get_seed_inventory_service()
    
    try:
        req = await service.ship_request(db, request_id)
        
        return {
            "success": True,
            "message": f"Request {request_id} shipped",
            **req.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to ship request: {str(e)}")


@router.get("/summary")
async def get_inventory_summary(
    db: AsyncSession = Depends(get_db)
):
    """
    Get inventory summary statistics
    
    Returns counts by status, storage type, and species.
    Also lists lots needing viability testing.
    """
    service = get_seed_inventory_service()
    
    summary = await service.get_inventory_summary(db)
    
    return {
        "success": True,
        **summary,
    }


@router.get("/alerts")
async def get_inventory_alerts(
    db: AsyncSession = Depends(get_db)
):
    """
    Get inventory alerts
    
    Returns alerts for:
    - Low stock
    - Low viability
    - Overdue viability tests
    """
    service = get_seed_inventory_service()
    
    alerts = await service.get_alerts(db)
    
    return {
        "success": True,
        "alert_count": len(alerts),
        "alerts": alerts,
    }


@router.get("/storage-types")
async def list_storage_types():
    """List available storage types"""
    return {
        "storage_types": [
            {
                "id": "short_term",
                "name": "Short-term Storage",
                "temperature": "5°C",
                "expected_viability": "5-10 years",
                "use_case": "Active collection, frequent access",
            },
            {
                "id": "medium_term",
                "name": "Medium-term Storage",
                "temperature": "-5°C",
                "expected_viability": "10-20 years",
                "use_case": "Base collection backup",
            },
            {
                "id": "long_term",
                "name": "Long-term Storage",
                "temperature": "-18°C",
                "expected_viability": "50+ years",
                "use_case": "Base collection, conservation",
            },
            {
                "id": "cryo",
                "name": "Cryopreservation",
                "temperature": "-196°C (liquid nitrogen)",
                "expected_viability": "Indefinite",
                "use_case": "Recalcitrant seeds, vegetative material",
            },
        ]
    }
