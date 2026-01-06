"""
Field Layout API
Visual plot layout and management for studies
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import random

router = APIRouter(prefix="/field-layout", tags=["Field Layout"])


# ============================================
# SCHEMAS
# ============================================

class Study(BaseModel):
    studyDbId: str
    studyName: str
    rows: int
    cols: int
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
    study: Study
    plots: List[Plot]
    summary: dict


# ============================================
# DEMO DATA
# ============================================

DEMO_STUDIES = [
    Study(studyDbId="study001", studyName="Rice Yield Trial 2024", rows=10, cols=8, programDbId="prog001"),
    Study(studyDbId="study002", studyName="Wheat Disease Screening", rows=8, cols=12, programDbId="prog002"),
    Study(studyDbId="study003", studyName="Maize Drought Trial", rows=6, cols=10, programDbId="prog003"),
    Study(studyDbId="study004", studyName="Soybean Quality Trial", rows=12, cols=6, programDbId="prog001"),
    Study(studyDbId="study005", studyName="Barley Multi-Location", rows=8, cols=8, programDbId="prog002"),
]

GERMPLASM_NAMES = [
    "IR64", "Nipponbare", "Kasalath", "Azucena", "N22", "Moroberekan",
    "Check-1", "Check-2", "Elite-001", "Elite-002", "Donor-A", "Donor-B"
]


def generate_plots(study: Study) -> List[Plot]:
    """Generate plot layout for a study."""
    plots = []
    for r in range(1, study.rows + 1):
        for c in range(1, study.cols + 1):
            is_check = random.random() > 0.9
            plots.append(Plot(
                plotNumber=f"P{r:02d}{c:02d}",
                row=r,
                col=c,
                germplasmName=random.choice(GERMPLASM_NAMES),
                germplasmDbId=f"grm-{random.randint(1000, 9999)}",
                blockNumber=(r - 1) // 2 + 1,
                replicate=((r - 1) % 2) + 1,
                entryType="CHECK" if is_check else "TEST",
                observationUnitDbId=f"ou-{study.studyDbId}-{r:02d}{c:02d}"
            ))
    return plots


# ============================================
# ENDPOINTS
# ============================================

@router.get("/studies")
async def get_studies(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    search: Optional[str] = Query(None, description="Search by name"),
):
    """Get list of studies with field layouts."""
    studies = DEMO_STUDIES
    
    if program_id:
        studies = [s for s in studies if s.programDbId == program_id]
    
    if search:
        search_lower = search.lower()
        studies = [s for s in studies if search_lower in s.studyName.lower()]
    
    return {"data": [s.model_dump() for s in studies], "total": len(studies)}


@router.get("/studies/{study_id}")
async def get_study(study_id: str):
    """Get study details."""
    study = next((s for s in DEMO_STUDIES if s.studyDbId == study_id), None)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return {"data": study.model_dump()}


@router.get("/studies/{study_id}/layout", response_model=FieldLayoutResponse)
async def get_field_layout(study_id: str):
    """Get complete field layout for a study."""
    study = next((s for s in DEMO_STUDIES if s.studyDbId == study_id), None)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    plots = generate_plots(study)
    
    # Calculate summary
    check_count = sum(1 for p in plots if p.entryType == "CHECK")
    test_count = len(plots) - check_count
    unique_germplasm = len(set(p.germplasmName for p in plots))
    
    summary = {
        "total_plots": len(plots),
        "check_plots": check_count,
        "test_plots": test_count,
        "unique_germplasm": unique_germplasm,
        "blocks": max(p.blockNumber or 0 for p in plots),
        "replicates": max(p.replicate or 0 for p in plots),
    }
    
    return FieldLayoutResponse(
        study=study,
        plots=plots,
        summary=summary
    )


@router.get("/studies/{study_id}/plots")
async def get_plots(
    study_id: str,
    block: Optional[int] = Query(None, description="Filter by block"),
    replicate: Optional[int] = Query(None, description="Filter by replicate"),
    entry_type: Optional[str] = Query(None, description="Filter by entry type"),
):
    """Get plots for a study with optional filters."""
    study = next((s for s in DEMO_STUDIES if s.studyDbId == study_id), None)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    plots = generate_plots(study)
    
    if block:
        plots = [p for p in plots if p.blockNumber == block]
    if replicate:
        plots = [p for p in plots if p.replicate == replicate]
    if entry_type:
        plots = [p for p in plots if p.entryType == entry_type]
    
    return {"data": [p.model_dump() for p in plots], "total": len(plots)}


@router.get("/studies/{study_id}/plots/{plot_number}")
async def get_plot(study_id: str, plot_number: str):
    """Get single plot details."""
    study = next((s for s in DEMO_STUDIES if s.studyDbId == study_id), None)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    plots = generate_plots(study)
    plot = next((p for p in plots if p.plotNumber == plot_number), None)
    
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    return {"data": plot.model_dump()}


@router.put("/studies/{study_id}/plots/{plot_number}")
async def update_plot(study_id: str, plot_number: str, data: dict):
    """Update plot information."""
    # In production, this would update the database
    return {
        "message": "Plot updated successfully",
        "plot_number": plot_number,
        "study_id": study_id,
        "updated_fields": list(data.keys())
    }


@router.get("/germplasm")
async def get_available_germplasm():
    """Get list of germplasm available for field layout."""
    return {
        "data": [
            {"germplasmDbId": f"grm-{i}", "germplasmName": name}
            for i, name in enumerate(GERMPLASM_NAMES, 1)
        ]
    }


@router.post("/studies/{study_id}/generate")
async def generate_layout(
    study_id: str,
    design: str = Query("rcbd", description="Design type: rcbd, alpha, crd, augmented"),
    blocks: int = Query(3, ge=1, le=20),
    replicates: int = Query(2, ge=1, le=10),
):
    """Generate a new field layout using specified design."""
    study = next((s for s in DEMO_STUDIES if s.studyDbId == study_id), None)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    return {
        "message": f"Layout generated using {design.upper()} design",
        "study_id": study_id,
        "design": design,
        "blocks": blocks,
        "replicates": replicates,
        "total_plots": study.rows * study.cols
    }


@router.get("/export/{study_id}")
async def export_layout(
    study_id: str,
    format: str = Query("csv", description="Export format: csv, json, xlsx"),
):
    """Export field layout."""
    study = next((s for s in DEMO_STUDIES if s.studyDbId == study_id), None)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    return {
        "message": f"Layout exported as {format.upper()}",
        "study_id": study_id,
        "format": format,
        "download_url": f"/api/v2/field-layout/download/{study_id}.{format}"
    }
