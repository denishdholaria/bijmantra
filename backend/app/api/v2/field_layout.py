"""
Field Layout API
Visual plot layout and management for studies

Converted to database queries per Zero Mock Data Policy (Session 77).
Queries Study and ObservationUnit tables for real data.
Uses FieldLayoutService for business logic.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import io
import csv

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.schemas.field_layout import (
    StudyInfo,
    Plot,
    FieldLayoutResponse,
    GermplasmListResponse,
    LayoutGenerationResponse,
    ExportResponse
)
from app.services.field_layout_service import FieldLayoutService

from app.api.deps import get_current_user

router = APIRouter(prefix="/field-layout", tags=["Field Layout"], dependencies=[Depends(get_current_user)])

# ============================================
# ENDPOINTS
# ============================================

@router.get("/studies")
async def get_studies(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get list of studies with field layouts."""
    studies = await FieldLayoutService.get_studies(db, organization_id, program_id, search)
    return {"data": [s.model_dump() for s in studies], "total": len(studies)}


@router.get("/studies/{study_id}")
async def get_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get study details."""
    study = await FieldLayoutService.get_study(db, organization_id, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return {"data": study.model_dump()}


@router.get("/studies/{study_id}/layout", response_model=FieldLayoutResponse)
async def get_field_layout(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get complete field layout for a study."""
    layout = await FieldLayoutService.get_field_layout(db, organization_id, study_id)
    if not layout:
        raise HTTPException(status_code=404, detail="Study not found or no layout available")
    return layout


@router.get("/studies/{study_id}/plots")
async def get_plots(
    study_id: str,
    block: Optional[int] = Query(None, description="Filter by block"),
    replicate: Optional[int] = Query(None, description="Filter by replicate"),
    entry_type: Optional[str] = Query(None, description="Filter by entry type"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get plots for a study with optional filters."""
    plots = await FieldLayoutService.get_plots(
        db, organization_id, study_id, block, replicate, entry_type
    )
    return {"data": [p.model_dump() for p in plots], "total": len(plots)}


@router.get("/studies/{study_id}/plots/{plot_number}")
async def get_plot(
    study_id: str,
    plot_number: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get single plot details."""
    plot = await FieldLayoutService.get_plot(db, organization_id, study_id, plot_number)
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    return {"data": plot.model_dump()}


@router.put("/studies/{study_id}/plots/{plot_number}")
async def update_plot(
    study_id: str,
    plot_number: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Update plot information."""
    success = await FieldLayoutService.update_plot(db, organization_id, study_id, plot_number, data)
    if not success:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    return {
        "message": "Plot updated successfully",
        "plot_number": plot_number,
        "study_id": study_id,
        "updated_fields": list(data.keys())
    }


@router.get("/germplasm")
async def get_available_germplasm(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get list of germplasm available for field layout."""
    data = await FieldLayoutService.get_available_germplasm(db, organization_id)
    return {"data": data}


@router.post("/studies/{study_id}/generate")
async def generate_layout(
    study_id: str,
    design: str = Query("rcbd", description="Design type: rcbd, alpha, crd, augmented"),
    blocks: int = Query(3, ge=1, le=20),
    replicates: int = Query(2, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Generate a new field layout using specified design."""
    result = await FieldLayoutService.generate_layout(
        db, organization_id, study_id, design, blocks, replicates
    )
    if not result:
        raise HTTPException(status_code=404, detail="Study not found")
    return result


@router.get("/export/{study_id}")
async def export_layout(
    study_id: str,
    format: str = Query("csv", description="Export format: csv, json, xlsx"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Export field layout."""
    result = await FieldLayoutService.export_layout(db, organization_id, study_id, format)
    if not result:
         raise HTTPException(status_code=404, detail="Study not found or layout empty")
    return result


@router.get("/download/{study_id}.csv")
async def download_layout_csv(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Download field layout as CSV."""
    layout = await FieldLayoutService.get_field_layout(db, organization_id, study_id)
    if not layout:
        raise HTTPException(status_code=404, detail="Study not found or layout empty")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Plot", "Row", "Col", "Block", "Rep", "EntryType", "Germplasm", "GermplasmID"])
    
    for p in layout.plots:
        writer.writerow([
            p.plotNumber,
            p.row,
            p.col,
            p.blockNumber,
            p.replicate,
            p.entryType,
            p.germplasmName,
            p.germplasmDbId
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=layout_{study_id}.csv"}
    )
