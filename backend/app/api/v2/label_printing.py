"""
Label Printing API
Endpoints for label template management and print job operations
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.label_printing import label_printing_service


router = APIRouter(prefix="/labels", tags=["Label Printing"])


class CreateTemplateRequest(BaseModel):
    name: str
    type: str = "custom"
    size: str = "2x1 inch"
    width_mm: float = 50.8
    height_mm: float = 25.4
    fields: list[str] = []
    barcode_type: str = "qr"


class CreatePrintJobRequest(BaseModel):
    template_id: str
    items: list[dict]
    copies: int = 1


class UpdateJobStatusRequest(BaseModel):
    status: str


@router.get("/templates")
async def get_templates(
    label_type: Optional[str] = Query(None, description="Filter by label type"),
):
    """Get all label templates."""
    templates = label_printing_service.get_templates(label_type=label_type)
    return {"templates": templates, "total": len(templates)}


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get a single template by ID."""
    template = label_printing_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/templates")
async def create_template(request: CreateTemplateRequest):
    """Create a custom label template."""
    template = label_printing_service.create_template(request.model_dump())
    return template


@router.get("/data")
async def get_label_data(
    source_type: str = Query(..., description="Source type: plots, seedlots, samples, accessions"),
    study_id: Optional[str] = Query(None, description="Filter by study ID"),
    trial_id: Optional[str] = Query(None, description="Filter by trial ID"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get data for label generation."""
    data = label_printing_service.get_label_data(
        source_type=source_type,
        study_id=study_id,
        trial_id=trial_id,
        limit=limit,
    )
    return {"data": data, "total": len(data), "source_type": source_type}


@router.get("/jobs")
async def get_print_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get print job history."""
    jobs = label_printing_service.get_print_jobs(status=status, limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/jobs/{job_id}")
async def get_print_job(job_id: str):
    """Get a single print job."""
    job = label_printing_service.get_print_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")
    return job


@router.post("/jobs")
async def create_print_job(request: CreatePrintJobRequest):
    """Create a new print job."""
    # Validate template exists
    template = label_printing_service.get_template(request.template_id)
    if not template:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    job = label_printing_service.create_print_job({
        "template_id": request.template_id,
        "items": request.items,
        "copies": request.copies,
        "label_count": len(request.items),
    })
    return job


@router.patch("/jobs/{job_id}/status")
async def update_job_status(job_id: str, request: UpdateJobStatusRequest):
    """Update print job status."""
    if request.status not in ["pending", "printing", "completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    job = label_printing_service.update_print_job_status(job_id, request.status)
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")
    return job


@router.get("/stats")
async def get_stats():
    """Get label printing statistics."""
    return label_printing_service.get_stats()
