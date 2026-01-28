"""
Seed Processing API
Manage seed processing batches through various stages

Endpoints:
- POST /api/v2/processing/batches - Create batch
- GET /api/v2/processing/batches - List batches
- GET /api/v2/processing/batches/{id} - Get batch details
- POST /api/v2/processing/batches/{id}/stages - Start stage
- PUT /api/v2/processing/batches/{id}/stages/{stage_id} - Complete stage
- POST /api/v2/processing/batches/{id}/quality-checks - Add quality check
- POST /api/v2/processing/batches/{id}/hold - Put on hold
- POST /api/v2/processing/batches/{id}/resume - Resume from hold
- POST /api/v2/processing/batches/{id}/reject - Reject batch
- GET /api/v2/processing/batches/{id}/summary - Get processing summary
- GET /api/v2/processing/stages - Get available stages
- GET /api/v2/processing/statistics - Get statistics
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from app.services.processing_batch import get_processing_service

router = APIRouter(prefix="/processing", tags=["Seed Processing"])


# ============================================
# SCHEMAS
# ============================================

class BatchCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "lot_id": "LOT-2024-001",
            "variety_name": "IR64",
            "crop": "Rice",
            "seed_class": "certified",
            "input_quantity_kg": 1000,
            "target_output_kg": 850,
            "notes": "Kharif 2024 harvest"
        }
    })

    lot_id: str = Field(..., description="Source seed lot ID")
    variety_name: str = Field(..., description="Variety name")
    crop: str = Field(..., description="Crop name")
    seed_class: str = Field("certified", description="Seed class")
    input_quantity_kg: float = Field(..., gt=0, description="Input quantity in kg")
    target_output_kg: Optional[float] = Field(None, description="Target output quantity")
    notes: str = Field("", description="Additional notes")


class StageStart(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "stage": "cleaning",
            "operator": "John Doe",
            "equipment": "Air Screen Cleaner ASC-100",
            "parameters": {"screen_size": "2.5mm", "air_flow": "high"}
        }
    })

    stage: str = Field(..., description="Stage name")
    operator: str = Field(..., description="Operator name")
    equipment: str = Field("", description="Equipment used")
    input_quantity_kg: Optional[float] = Field(None, description="Input quantity (defaults to current)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Stage parameters")


class StageComplete(BaseModel):
    output_quantity_kg: float = Field(..., gt=0, description="Output quantity in kg")
    notes: str = Field("", description="Completion notes")


class QualityCheck(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "check_type": "moisture",
            "result_value": 10.5,
            "passed": True,
            "checked_by": "Lab Tech",
            "notes": "Within acceptable range"
        }
    })

    check_type: str = Field(..., description="Check type: moisture, purity, germination, etc.")
    result_value: float = Field(..., description="Result value")
    passed: bool = Field(..., description="Whether check passed")
    checked_by: str = Field(..., description="Person who performed check")
    notes: str = Field("", description="Additional notes")


# ============================================
# BATCH ENDPOINTS
# ============================================

@router.post("/batches")
async def create_batch(request: BatchCreate):
    """
    Create a new processing batch
    
    Creates a batch in PENDING status at RECEIVING stage.
    """
    service = get_processing_service()
    
    try:
        batch = service.create_batch(
            lot_id=request.lot_id,
            variety_name=request.variety_name,
            crop=request.crop,
            seed_class=request.seed_class,
            input_quantity_kg=request.input_quantity_kg,
            target_output_kg=request.target_output_kg,
            notes=request.notes,
        )
        return {
            "success": True,
            "message": f"Batch {batch.batch_number} created",
            "data": batch.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to create batch: {str(e)}")


@router.get("/batches")
async def list_batches(
    status: Optional[str] = Query(None, description="Filter by status"),
    stage: Optional[str] = Query(None, description="Filter by current stage"),
    lot_id: Optional[str] = Query(None, description="Filter by lot ID"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
):
    """List processing batches with optional filters"""
    service = get_processing_service()
    
    batches = service.list_batches(
        status=status,
        stage=stage,
        lot_id=lot_id,
        crop=crop,
    )
    
    return {
        "success": True,
        "count": len(batches),
        "data": batches,
    }


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: str):
    """Get batch details"""
    service = get_processing_service()
    
    batch = service.get_batch(batch_id)
    if not batch:
        raise HTTPException(404, f"Batch {batch_id} not found")
    
    return {"success": True, "data": batch}


@router.post("/batches/{batch_id}/stages")
async def start_stage(batch_id: str, request: StageStart):
    """Start a processing stage"""
    service = get_processing_service()
    
    try:
        batch = service.start_stage(
            batch_id=batch_id,
            stage=request.stage,
            operator=request.operator,
            equipment=request.equipment,
            input_quantity_kg=request.input_quantity_kg,
            parameters=request.parameters,
        )
        return {
            "success": True,
            "message": f"Stage {request.stage} started",
            "data": batch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/batches/{batch_id}/stages/{stage_id}")
async def complete_stage(batch_id: str, stage_id: str, request: StageComplete):
    """Complete a processing stage"""
    service = get_processing_service()
    
    try:
        batch = service.complete_stage(
            batch_id=batch_id,
            stage_id=stage_id,
            output_quantity_kg=request.output_quantity_kg,
            notes=request.notes,
        )
        return {
            "success": True,
            "message": "Stage completed",
            "data": batch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/batches/{batch_id}/quality-checks")
async def add_quality_check(batch_id: str, request: QualityCheck):
    """Add quality check to batch"""
    service = get_processing_service()
    
    try:
        batch = service.add_quality_check(
            batch_id=batch_id,
            check_type=request.check_type,
            result_value=request.result_value,
            passed=request.passed,
            checked_by=request.checked_by,
            notes=request.notes,
        )
        status = "PASSED" if request.passed else "FAILED"
        return {
            "success": True,
            "message": f"Quality check recorded: {status}",
            "data": batch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/batches/{batch_id}/hold")
async def hold_batch(batch_id: str, reason: str = Query(...)):
    """Put batch on hold"""
    service = get_processing_service()
    
    try:
        batch = service.hold_batch(batch_id, reason)
        return {
            "success": True,
            "message": "Batch put on hold",
            "data": batch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/batches/{batch_id}/resume")
async def resume_batch(batch_id: str):
    """Resume batch from hold"""
    service = get_processing_service()
    
    try:
        batch = service.resume_batch(batch_id)
        return {
            "success": True,
            "message": "Batch resumed",
            "data": batch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/batches/{batch_id}/reject")
async def reject_batch(batch_id: str, reason: str = Query(...)):
    """Reject a batch"""
    service = get_processing_service()
    
    try:
        batch = service.reject_batch(batch_id, reason)
        return {
            "success": True,
            "message": "Batch rejected",
            "data": batch,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/batches/{batch_id}/summary")
async def get_batch_summary(batch_id: str):
    """Get processing summary for a batch"""
    service = get_processing_service()
    
    try:
        summary = service.get_stage_summary(batch_id)
        return {"success": True, "data": summary}
    except ValueError as e:
        raise HTTPException(404, str(e))


# ============================================
# REFERENCE DATA ENDPOINTS
# ============================================

@router.get("/stages")
async def get_processing_stages():
    """Get available processing stages"""
    service = get_processing_service()
    stages = service.get_processing_stages()
    return {"success": True, "data": stages}


@router.get("/statistics")
async def get_statistics():
    """Get processing statistics"""
    service = get_processing_service()
    stats = service.get_statistics()
    return {"success": True, "data": stats}
