"""
Data Visualization API
Chart management and data visualization endpoints

Converted to database queries per Zero Mock Data Policy (Session 77).
Returns empty results when no chart data exists.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, UTC
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.core import Trial, Study
from app.models.germplasm import Germplasm
from app.models.phenotyping import Observation

router = APIRouter(prefix="/visualizations", tags=["Data Visualization"])


# ============================================
# SCHEMAS
# ============================================

class ChartConfig(BaseModel):
    id: str
    name: str
    type: str  # bar, line, pie, scatter, heatmap, box
    dataSource: str
    description: Optional[str] = None
    createdAt: str
    updatedAt: str
    createdBy: str
    isPublic: bool = False
    config: dict = {}


class ChartData(BaseModel):
    labels: List[str]
    datasets: List[dict]
    options: dict = {}


class DataSource(BaseModel):
    id: str
    name: str
    type: str  # trials, germplasm, observations, phenotyping, genotyping
    recordCount: int
    lastUpdated: str


# Static chart types (reference data)
CHART_TYPES = [
    {"id": "bar", "name": "Bar Chart", "icon": "bar-chart", "description": "Compare values across categories"},
    {"id": "line", "name": "Line Chart", "icon": "trending-up", "description": "Show trends over time"},
    {"id": "pie", "name": "Pie Chart", "icon": "pie-chart", "description": "Show proportions of a whole"},
    {"id": "scatter", "name": "Scatter Plot", "icon": "scatter-chart", "description": "Show relationships between variables"},
    {"id": "heatmap", "name": "Heatmap", "icon": "grid", "description": "Visualize matrix data with colors"},
    {"id": "box", "name": "Box Plot", "icon": "box", "description": "Show distribution statistics"},
    {"id": "histogram", "name": "Histogram", "icon": "bar-chart-2", "description": "Show frequency distribution"},
    {"id": "radar", "name": "Radar Chart", "icon": "activity", "description": "Compare multiple variables"},
]


# ============================================
# ENDPOINTS
# ============================================

@router.get("/charts")
async def get_charts(
    type: Optional[str] = Query(None, description="Filter by chart type"),
    data_source: Optional[str] = Query(None, description="Filter by data source"),
    search: Optional[str] = Query(None, description="Search by name"),
    public_only: bool = Query(False, description="Show only public charts"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get list of saved charts.
    
    Note: Chart storage requires a charts table to be created.
    Returns empty list until charts table exists.
    """
    # TODO: Query charts table when created
    return {"data": [], "total": 0, "message": "Chart storage requires charts table"}


@router.get("/charts/{chart_id}")
async def get_chart(
    chart_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get chart configuration.
    
    Returns 404 until charts table exists.
    """
    # TODO: Query charts table when created
    raise HTTPException(status_code=404, detail="Chart not found - charts table not yet created")


@router.post("/charts")
async def create_chart(
    data: dict,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Create a new chart.
    
    Note: Chart storage requires a charts table to be created.
    """
    # TODO: Insert into charts table when created
    return {
        "message": "Chart creation pending - charts table not yet created",
        "chart_id": None,
        "name": data.get("name", "Untitled Chart")
    }


@router.put("/charts/{chart_id}")
async def update_chart(
    chart_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Update chart configuration.
    
    Returns 404 until charts table exists.
    """
    # TODO: Update charts table when created
    raise HTTPException(status_code=404, detail="Chart not found - charts table not yet created")


@router.delete("/charts/{chart_id}")
async def delete_chart(
    chart_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Delete a chart.
    
    Returns 404 until charts table exists.
    """
    # TODO: Delete from charts table when created
    raise HTTPException(status_code=404, detail="Chart not found - charts table not yet created")


@router.get("/charts/{chart_id}/data")
async def get_chart_data(
    chart_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get data for a specific chart.
    
    Returns empty data until charts table exists.
    """
    # TODO: Query chart config and generate data
    return ChartData(labels=[], datasets=[], options={})


@router.get("/data-sources")
async def get_data_sources(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get available data sources for visualization.
    
    Queries actual table counts from database.
    """
    now = datetime.now(UTC).isoformat() + "Z"
    
    # Count trials
    trial_count = await db.execute(
        select(func.count()).select_from(Trial).where(
            Trial.organization_id == organization_id
        )
    )
    
    # Count germplasm
    germplasm_count = await db.execute(
        select(func.count()).select_from(Germplasm).where(
            Germplasm.organization_id == organization_id
        )
    )
    
    # Count observations
    observation_count = await db.execute(
        select(func.count()).select_from(Observation).where(
            Observation.organization_id == organization_id
        )
    )
    
    # Count studies
    study_count = await db.execute(
        select(func.count()).select_from(Study).where(
            Study.organization_id == organization_id
        )
    )
    
    data_sources = [
        DataSource(
            id="ds-trials",
            name="Trials",
            type="trials",
            recordCount=trial_count.scalar() or 0,
            lastUpdated=now
        ),
        DataSource(
            id="ds-germplasm",
            name="Germplasm",
            type="germplasm",
            recordCount=germplasm_count.scalar() or 0,
            lastUpdated=now
        ),
        DataSource(
            id="ds-observations",
            name="Observations",
            type="observations",
            recordCount=observation_count.scalar() or 0,
            lastUpdated=now
        ),
        DataSource(
            id="ds-studies",
            name="Studies",
            type="studies",
            recordCount=study_count.scalar() or 0,
            lastUpdated=now
        ),
    ]
    
    return {"data": [ds.model_dump() for ds in data_sources]}


@router.get("/chart-types")
async def get_chart_types():
    """Get available chart types.
    
    Returns static reference data.
    """
    return {"data": CHART_TYPES}


@router.get("/statistics")
async def get_visualization_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get visualization statistics.
    
    Returns zeros until charts table exists.
    """
    # Count data sources
    trial_count = await db.execute(
        select(func.count()).select_from(Trial).where(
            Trial.organization_id == organization_id
        )
    )
    germplasm_count = await db.execute(
        select(func.count()).select_from(Germplasm).where(
            Germplasm.organization_id == organization_id
        )
    )
    
    return {
        "total_charts": 0,
        "by_type": {
            "bar": 0,
            "line": 0,
            "pie": 0,
            "scatter": 0,
            "heatmap": 0,
            "box": 0,
        },
        "public_charts": 0,
        "private_charts": 0,
        "data_sources": 4,
        "total_records": (trial_count.scalar() or 0) + (germplasm_count.scalar() or 0),
        "message": "Chart statistics require charts table",
    }


@router.post("/preview")
async def preview_chart(
    chart_type: str = Query(..., description="Chart type"),
    data_source: str = Query(..., description="Data source"),
    x_axis: Optional[str] = Query(None),
    y_axis: Optional[str] = Query(None),
    group_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Generate a preview of chart with given configuration.
    
    Returns configuration without actual data preview.
    """
    # Count records in data source
    record_count = 0
    if data_source.lower() == "trials":
        result = await db.execute(
            select(func.count()).select_from(Trial).where(
                Trial.organization_id == organization_id
            )
        )
        record_count = result.scalar() or 0
    elif data_source.lower() == "germplasm":
        result = await db.execute(
            select(func.count()).select_from(Germplasm).where(
                Germplasm.organization_id == organization_id
            )
        )
        record_count = result.scalar() or 0
    
    return {
        "preview_url": None,
        "config": {
            "type": chart_type,
            "dataSource": data_source,
            "xAxis": x_axis,
            "yAxis": y_axis,
            "groupBy": group_by
        },
        "estimated_records": record_count,
        "message": "Preview generation requires chart rendering service",
    }


@router.post("/charts/{chart_id}/export")
async def export_chart(
    chart_id: str,
    format: str = Query("png", description="Export format: png, svg, pdf"),
    width: int = Query(800, ge=200, le=4000),
    height: int = Query(600, ge=200, le=3000),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Export chart as image.
    
    Returns 404 until charts table exists.
    """
    # TODO: Query charts table when created
    raise HTTPException(status_code=404, detail="Chart not found - charts table not yet created")
