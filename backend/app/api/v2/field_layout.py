"""
Field Layout API
Visual plot layout and management for studies

Converted to database queries per Zero Mock Data Policy (Session 77).
Queries Study and ObservationUnit tables for real data.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.core import Study, Program, Location
from app.models.phenotyping import ObservationUnit

router = APIRouter(prefix="/field-layout", tags=["Field Layout"])


# ============================================
# SCHEMAS
# ============================================

class StudyInfo(BaseModel):
    studyDbId: str
    studyName: str
    rows: int = 0
    cols: int = 0
    programDbId: Optional[str] = None
    locationDbId: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None


class Plot(BaseModel):
    plotNumber: str
    row: int
    col: int
    germplasmName: Optional[str] = None
    germplasmDbId: Optional[str] = None
    blockNumber: Optional[int] = None
    replicate: Optional[int] = None
    entryType: Optional[str] = None
    observationUnitDbId: Optional[str] = None


class FieldLayoutResponse(BaseModel):
    study: StudyInfo
    plots: List[Plot]
    summary: dict


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
    """Get list of studies with field layouts.
    
    Queries Study table for real data.
    Returns empty list when no studies exist.
    """
    stmt = select(Study).where(
        Study.organization_id == organization_id
    ).options(
        selectinload(Study.program),
        selectinload(Study.location),
    )
    
    if program_id:
        stmt = stmt.where(Study.program_id == int(program_id))
    
    if search:
        stmt = stmt.where(Study.study_name.ilike(f"%{search}%"))
    
    result = await db.execute(stmt)
    studies = result.scalars().all()
    
    data = []
    for study in studies:
        additional = study.additional_info or {}
        data.append(StudyInfo(
            studyDbId=study.study_db_id or str(study.id),
            studyName=study.study_name or "",
            rows=additional.get("rows", 0),
            cols=additional.get("cols", 0),
            programDbId=str(study.program_id) if study.program_id else None,
            locationDbId=str(study.location_id) if study.location_id else None,
            startDate=study.start_date.isoformat() if study.start_date else None,
            endDate=study.end_date.isoformat() if study.end_date else None,
        ).model_dump())
    
    return {"data": data, "total": len(data)}


@router.get("/studies/{study_id}")
async def get_study(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get study details.
    
    Returns 404 if study not found.
    """
    stmt = select(Study).where(
        and_(
            Study.organization_id == organization_id,
            Study.study_db_id == study_id,
        )
    )
    
    result = await db.execute(stmt)
    study = result.scalar_one_or_none()
    
    if not study:
        # Try by numeric ID
        if study_id.isdigit():
            stmt = select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.id == int(study_id),
                )
            )
            result = await db.execute(stmt)
            study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    additional = study.additional_info or {}
    
    return {"data": StudyInfo(
        studyDbId=study.study_db_id or str(study.id),
        studyName=study.study_name or "",
        rows=additional.get("rows", 0),
        cols=additional.get("cols", 0),
        programDbId=str(study.program_id) if study.program_id else None,
        locationDbId=str(study.location_id) if study.location_id else None,
        startDate=study.start_date.isoformat() if study.start_date else None,
        endDate=study.end_date.isoformat() if study.end_date else None,
    ).model_dump()}


@router.get("/studies/{study_id}/layout", response_model=FieldLayoutResponse)
async def get_field_layout(
    study_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get complete field layout for a study.
    
    Queries ObservationUnit table for plot data.
    Returns empty plots list when no observation units exist.
    """
    # Get study
    stmt = select(Study).where(
        and_(
            Study.organization_id == organization_id,
            Study.study_db_id == study_id,
        )
    )
    
    result = await db.execute(stmt)
    study = result.scalar_one_or_none()
    
    if not study:
        if study_id.isdigit():
            stmt = select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.id == int(study_id),
                )
            )
            result = await db.execute(stmt)
            study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    additional = study.additional_info or {}
    
    study_info = StudyInfo(
        studyDbId=study.study_db_id or str(study.id),
        studyName=study.study_name or "",
        rows=additional.get("rows", 0),
        cols=additional.get("cols", 0),
        programDbId=str(study.program_id) if study.program_id else None,
        locationDbId=str(study.location_id) if study.location_id else None,
        startDate=study.start_date.isoformat() if study.start_date else None,
        endDate=study.end_date.isoformat() if study.end_date else None,
    )
    
    # Get observation units (plots) for this study
    stmt = select(ObservationUnit).where(
        and_(
            ObservationUnit.study_id == study.id,
            ObservationUnit.organization_id == organization_id,
        )
    ).options(
        selectinload(ObservationUnit.germplasm),
    )
    
    result = await db.execute(stmt)
    observation_units = result.scalars().all()
    
    plots = []
    check_count = 0
    unique_germplasm = set()
    max_block = 0
    max_rep = 0
    
    for ou in observation_units:
        position = ou.position_coordinate_x or {}
        additional_ou = ou.additional_info or {}
        
        row = position.get("row", 0) if isinstance(position, dict) else 0
        col = position.get("col", 0) if isinstance(position, dict) else 0
        block = additional_ou.get("blockNumber", 0)
        rep = additional_ou.get("replicate", 0)
        entry_type = additional_ou.get("entryType", "TEST")
        
        if entry_type == "CHECK":
            check_count += 1
        
        if ou.germplasm:
            unique_germplasm.add(ou.germplasm.id)
        
        max_block = max(max_block, block)
        max_rep = max(max_rep, rep)
        
        plots.append(Plot(
            plotNumber=ou.observation_unit_db_id or str(ou.id),
            row=row,
            col=col,
            germplasmName=ou.germplasm.germplasm_name if ou.germplasm else None,
            germplasmDbId=str(ou.germplasm_id) if ou.germplasm_id else None,
            blockNumber=block,
            replicate=rep,
            entryType=entry_type,
            observationUnitDbId=ou.observation_unit_db_id or str(ou.id),
        ))
    
    summary = {
        "total_plots": len(plots),
        "check_plots": check_count,
        "test_plots": len(plots) - check_count,
        "unique_germplasm": len(unique_germplasm),
        "blocks": max_block,
        "replicates": max_rep,
    }
    
    return FieldLayoutResponse(
        study=study_info,
        plots=plots,
        summary=summary
    )


@router.get("/studies/{study_id}/plots")
async def get_plots(
    study_id: str,
    block: Optional[int] = Query(None, description="Filter by block"),
    replicate: Optional[int] = Query(None, description="Filter by replicate"),
    entry_type: Optional[str] = Query(None, description="Filter by entry type"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get plots for a study with optional filters.
    
    Returns empty list when no observation units exist.
    """
    # Get study
    stmt = select(Study).where(
        and_(
            Study.organization_id == organization_id,
            Study.study_db_id == study_id,
        )
    )
    
    result = await db.execute(stmt)
    study = result.scalar_one_or_none()
    
    if not study:
        if study_id.isdigit():
            stmt = select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.id == int(study_id),
                )
            )
            result = await db.execute(stmt)
            study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get observation units
    stmt = select(ObservationUnit).where(
        and_(
            ObservationUnit.study_id == study.id,
            ObservationUnit.organization_id == organization_id,
        )
    ).options(
        selectinload(ObservationUnit.germplasm),
    )
    
    result = await db.execute(stmt)
    observation_units = result.scalars().all()
    
    plots = []
    for ou in observation_units:
        position = ou.position_coordinate_x or {}
        additional_ou = ou.additional_info or {}
        
        row = position.get("row", 0) if isinstance(position, dict) else 0
        col = position.get("col", 0) if isinstance(position, dict) else 0
        block_num = additional_ou.get("blockNumber", 0)
        rep = additional_ou.get("replicate", 0)
        et = additional_ou.get("entryType", "TEST")
        
        # Apply filters
        if block is not None and block_num != block:
            continue
        if replicate is not None and rep != replicate:
            continue
        if entry_type is not None and et != entry_type:
            continue
        
        plots.append(Plot(
            plotNumber=ou.observation_unit_db_id or str(ou.id),
            row=row,
            col=col,
            germplasmName=ou.germplasm.germplasm_name if ou.germplasm else None,
            germplasmDbId=str(ou.germplasm_id) if ou.germplasm_id else None,
            blockNumber=block_num,
            replicate=rep,
            entryType=et,
            observationUnitDbId=ou.observation_unit_db_id or str(ou.id),
        ).model_dump())
    
    return {"data": plots, "total": len(plots)}


@router.get("/studies/{study_id}/plots/{plot_number}")
async def get_plot(
    study_id: str,
    plot_number: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get single plot details.
    
    Returns 404 if plot not found.
    """
    # Get study
    stmt = select(Study).where(
        and_(
            Study.organization_id == organization_id,
            Study.study_db_id == study_id,
        )
    )
    
    result = await db.execute(stmt)
    study = result.scalar_one_or_none()
    
    if not study:
        if study_id.isdigit():
            stmt = select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.id == int(study_id),
                )
            )
            result = await db.execute(stmt)
            study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get observation unit
    stmt = select(ObservationUnit).where(
        and_(
            ObservationUnit.study_id == study.id,
            ObservationUnit.organization_id == organization_id,
            ObservationUnit.observation_unit_db_id == plot_number,
        )
    ).options(
        selectinload(ObservationUnit.germplasm),
    )
    
    result = await db.execute(stmt)
    ou = result.scalar_one_or_none()
    
    if not ou:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    position = ou.position_coordinate_x or {}
    additional_ou = ou.additional_info or {}
    
    return {"data": Plot(
        plotNumber=ou.observation_unit_db_id or str(ou.id),
        row=position.get("row", 0) if isinstance(position, dict) else 0,
        col=position.get("col", 0) if isinstance(position, dict) else 0,
        germplasmName=ou.germplasm.germplasm_name if ou.germplasm else None,
        germplasmDbId=str(ou.germplasm_id) if ou.germplasm_id else None,
        blockNumber=additional_ou.get("blockNumber", 0),
        replicate=additional_ou.get("replicate", 0),
        entryType=additional_ou.get("entryType", "TEST"),
        observationUnitDbId=ou.observation_unit_db_id or str(ou.id),
    ).model_dump()}


@router.put("/studies/{study_id}/plots/{plot_number}")
async def update_plot(
    study_id: str,
    plot_number: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Update plot information.
    
    Updates ObservationUnit additional_info.
    """
    # Get study
    stmt = select(Study).where(
        and_(
            Study.organization_id == organization_id,
            Study.study_db_id == study_id,
        )
    )
    
    result = await db.execute(stmt)
    study = result.scalar_one_or_none()
    
    if not study:
        if study_id.isdigit():
            stmt = select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.id == int(study_id),
                )
            )
            result = await db.execute(stmt)
            study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get observation unit
    stmt = select(ObservationUnit).where(
        and_(
            ObservationUnit.study_id == study.id,
            ObservationUnit.organization_id == organization_id,
            ObservationUnit.observation_unit_db_id == plot_number,
        )
    )
    
    result = await db.execute(stmt)
    ou = result.scalar_one_or_none()
    
    if not ou:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    # Update additional_info
    additional = ou.additional_info or {}
    for key in ["blockNumber", "replicate", "entryType"]:
        if key in data:
            additional[key] = data[key]
    ou.additional_info = additional
    
    await db.commit()
    
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
    """Get list of germplasm available for field layout.
    
    Queries Germplasm table for real data.
    """
    stmt = select(Germplasm).where(
        Germplasm.organization_id == organization_id
    ).limit(100)
    
    result = await db.execute(stmt)
    germplasm_list = result.scalars().all()
    
    return {
        "data": [
            {"germplasmDbId": str(g.id), "germplasmName": g.germplasm_name}
            for g in germplasm_list
        ]
    }


@router.post("/studies/{study_id}/generate")
async def generate_layout(
    study_id: str,
    design: str = Query("rcbd", description="Design type: rcbd, alpha, crd, augmented"),
    blocks: int = Query(3, ge=1, le=20),
    replicates: int = Query(2, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Generate a new field layout using specified design.
    
    Experimental Design Types:
    - RCBD: Randomized Complete Block Design
    - Alpha: Alpha-lattice design for large trials
    - CRD: Completely Randomized Design
    - Augmented: Augmented design with checks
    
    Note: Layout generation requires experimental design service.
    """
    # Get study
    stmt = select(Study).where(
        and_(
            Study.organization_id == organization_id,
            Study.study_db_id == study_id,
        )
    )
    
    result = await db.execute(stmt)
    study = result.scalar_one_or_none()
    
    if not study:
        if study_id.isdigit():
            stmt = select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.id == int(study_id),
                )
            )
            result = await db.execute(stmt)
            study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    additional = study.additional_info or {}
    rows = additional.get("rows", 0)
    cols = additional.get("cols", 0)
    
    return {
        "message": f"Layout generation pending - {design.upper()} design",
        "study_id": study_id,
        "design": design,
        "blocks": blocks,
        "replicates": replicates,
        "total_plots": rows * cols if rows and cols else 0,
        "note": "Layout generation requires experimental design service",
    }


@router.get("/export/{study_id}")
async def export_layout(
    study_id: str,
    format: str = Query("csv", description="Export format: csv, json, xlsx"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Export field layout.
    
    Note: Export functionality requires file generation service.
    """
    # Get study
    stmt = select(Study).where(
        and_(
            Study.organization_id == organization_id,
            Study.study_db_id == study_id,
        )
    )
    
    result = await db.execute(stmt)
    study = result.scalar_one_or_none()
    
    if not study:
        if study_id.isdigit():
            stmt = select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.id == int(study_id),
                )
            )
            result = await db.execute(stmt)
            study = result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    return {
        "message": f"Export pending - {format.upper()} format",
        "study_id": study_id,
        "format": format,
        "download_url": None,
        "note": "Export functionality requires file generation service",
    }
