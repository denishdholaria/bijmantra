"""
Data Visualization API
Chart management and data visualization endpoints
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import random

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


# ============================================
# DEMO DATA
# ============================================

DEMO_CHARTS = [
    ChartConfig(
        id="chart-1",
        name="Yield Distribution",
        type="bar",
        dataSource="Trials",
        description="Distribution of yield across all trials",
        createdAt="2025-12-20T10:00:00Z",
        updatedAt="2025-12-24T14:30:00Z",
        createdBy="Dr. Sarah Johnson",
        isPublic=True,
        config={"xAxis": "germplasm", "yAxis": "yield", "groupBy": "trial"}
    ),
    ChartConfig(
        id="chart-2",
        name="Trait Correlations",
        type="scatter",
        dataSource="Observations",
        description="Correlation between yield and plant height",
        createdAt="2025-12-18T09:00:00Z",
        updatedAt="2025-12-23T11:00:00Z",
        createdBy="Dr. Michael Chen",
        isPublic=True,
        config={"xAxis": "plant_height", "yAxis": "yield", "colorBy": "program"}
    ),
    ChartConfig(
        id="chart-3",
        name="Germplasm by Origin",
        type="pie",
        dataSource="Germplasm",
        description="Distribution of germplasm by country of origin",
        createdAt="2025-12-15T08:00:00Z",
        updatedAt="2025-12-22T16:00:00Z",
        createdBy="Dr. Priya Patel",
        isPublic=False,
        config={"groupBy": "country", "metric": "count"}
    ),
    ChartConfig(
        id="chart-4",
        name="Yield Trends",
        type="line",
        dataSource="Historical",
        description="Yield trends over the past 10 years",
        createdAt="2025-12-10T12:00:00Z",
        updatedAt="2025-12-21T09:00:00Z",
        createdBy="Dr. Sarah Johnson",
        isPublic=True,
        config={"xAxis": "year", "yAxis": "mean_yield", "showTrend": True}
    ),
    ChartConfig(
        id="chart-5",
        name="Selection Progress",
        type="bar",
        dataSource="Pipeline",
        description="Entries at each breeding stage",
        createdAt="2025-12-08T14:00:00Z",
        updatedAt="2025-12-20T10:00:00Z",
        createdBy="Dr. Michael Chen",
        isPublic=True,
        config={"xAxis": "stage", "yAxis": "count", "stacked": False}
    ),
    ChartConfig(
        id="chart-6",
        name="Disease Scores",
        type="scatter",
        dataSource="Phenotyping",
        description="Disease resistance scores by germplasm",
        createdAt="2025-12-05T11:00:00Z",
        updatedAt="2025-12-19T15:00:00Z",
        createdBy="Dr. Priya Patel",
        isPublic=False,
        config={"xAxis": "germplasm", "yAxis": "disease_score", "colorBy": "resistance_gene"}
    ),
    ChartConfig(
        id="chart-7",
        name="GxE Heatmap",
        type="heatmap",
        dataSource="Trials",
        description="Genotype by Environment interaction",
        createdAt="2025-12-01T10:00:00Z",
        updatedAt="2025-12-18T12:00:00Z",
        createdBy="Dr. Sarah Johnson",
        isPublic=True,
        config={"xAxis": "environment", "yAxis": "genotype", "metric": "yield"}
    ),
    ChartConfig(
        id="chart-8",
        name="Trait Box Plots",
        type="box",
        dataSource="Observations",
        description="Distribution of key traits",
        createdAt="2025-11-28T09:00:00Z",
        updatedAt="2025-12-17T14:00:00Z",
        createdBy="Dr. Michael Chen",
        isPublic=True,
        config={"traits": ["yield", "height", "maturity"], "groupBy": "program"}
    ),
]

DATA_SOURCES = [
    DataSource(id="ds-1", name="Trials", type="trials", recordCount=47, lastUpdated="2025-12-25T08:00:00Z"),
    DataSource(id="ds-2", name="Observations", type="observations", recordCount=284000, lastUpdated="2025-12-25T07:30:00Z"),
    DataSource(id="ds-3", name="Germplasm", type="germplasm", recordCount=12847, lastUpdated="2025-12-24T18:00:00Z"),
    DataSource(id="ds-4", name="Phenotyping", type="phenotyping", recordCount=156000, lastUpdated="2025-12-25T06:00:00Z"),
    DataSource(id="ds-5", name="Genotyping", type="genotyping", recordCount=8500, lastUpdated="2025-12-23T12:00:00Z"),
    DataSource(id="ds-6", name="Historical", type="historical", recordCount=450000, lastUpdated="2025-12-20T00:00:00Z"),
    DataSource(id="ds-7", name="Pipeline", type="pipeline", recordCount=1250, lastUpdated="2025-12-25T09:00:00Z"),
]

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
):
    """Get list of saved charts."""
    charts = DEMO_CHARTS
    
    if type:
        charts = [c for c in charts if c.type == type]
    
    if data_source:
        charts = [c for c in charts if c.dataSource.lower() == data_source.lower()]
    
    if search:
        search_lower = search.lower()
        charts = [c for c in charts if search_lower in c.name.lower() or search_lower in (c.description or "").lower()]
    
    if public_only:
        charts = [c for c in charts if c.isPublic]
    
    return {"data": [c.model_dump() for c in charts], "total": len(charts)}


@router.get("/charts/{chart_id}")
async def get_chart(chart_id: str):
    """Get chart configuration."""
    chart = next((c for c in DEMO_CHARTS if c.id == chart_id), None)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    return {"data": chart.model_dump()}


@router.post("/charts")
async def create_chart(data: dict):
    """Create a new chart."""
    chart_id = f"chart-{len(DEMO_CHARTS) + 1}"
    return {
        "message": "Chart created successfully",
        "chart_id": chart_id,
        "name": data.get("name", "Untitled Chart")
    }


@router.put("/charts/{chart_id}")
async def update_chart(chart_id: str, data: dict):
    """Update chart configuration."""
    chart = next((c for c in DEMO_CHARTS if c.id == chart_id), None)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    
    return {
        "message": "Chart updated successfully",
        "chart_id": chart_id,
        "updated_fields": list(data.keys())
    }


@router.delete("/charts/{chart_id}")
async def delete_chart(chart_id: str):
    """Delete a chart."""
    chart = next((c for c in DEMO_CHARTS if c.id == chart_id), None)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    
    return {"message": "Chart deleted successfully", "chart_id": chart_id}


@router.get("/charts/{chart_id}/data")
async def get_chart_data(
    chart_id: str,
    limit: int = Query(100, ge=1, le=1000),
):
    """Get data for a specific chart."""
    chart = next((c for c in DEMO_CHARTS if c.id == chart_id), None)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    
    # Generate sample data based on chart type
    if chart.type == "bar":
        labels = [f"Entry-{i}" for i in range(1, 11)]
        data = [round(random.uniform(4, 8), 2) for _ in range(10)]
        return ChartData(
            labels=labels,
            datasets=[{"label": "Yield (t/ha)", "data": data, "backgroundColor": "#3b82f6"}],
            options={"responsive": True, "plugins": {"legend": {"position": "top"}}}
        )
    
    elif chart.type == "line":
        labels = [str(year) for year in range(2015, 2026)]
        data = [round(4.5 + i * 0.15 + random.uniform(-0.1, 0.1), 2) for i in range(11)]
        return ChartData(
            labels=labels,
            datasets=[{"label": "Mean Yield", "data": data, "borderColor": "#10b981", "fill": False}],
            options={"responsive": True}
        )
    
    elif chart.type == "pie":
        labels = ["Asia", "Africa", "Americas", "Europe", "Oceania"]
        data = [45, 25, 15, 10, 5]
        return ChartData(
            labels=labels,
            datasets=[{"data": data, "backgroundColor": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]}],
            options={"responsive": True}
        )
    
    elif chart.type == "scatter":
        points = [{"x": random.uniform(80, 120), "y": random.uniform(4, 8)} for _ in range(50)]
        return ChartData(
            labels=[],
            datasets=[{"label": "Height vs Yield", "data": points, "backgroundColor": "#3b82f6"}],
            options={"responsive": True}
        )
    
    else:
        return ChartData(labels=[], datasets=[], options={})


@router.get("/data-sources")
async def get_data_sources():
    """Get available data sources for visualization."""
    return {"data": [ds.model_dump() for ds in DATA_SOURCES]}


@router.get("/chart-types")
async def get_chart_types():
    """Get available chart types."""
    return {"data": CHART_TYPES}


@router.get("/statistics")
async def get_visualization_statistics():
    """Get visualization statistics."""
    return {
        "total_charts": len(DEMO_CHARTS),
        "by_type": {
            "bar": len([c for c in DEMO_CHARTS if c.type == "bar"]),
            "line": len([c for c in DEMO_CHARTS if c.type == "line"]),
            "pie": len([c for c in DEMO_CHARTS if c.type == "pie"]),
            "scatter": len([c for c in DEMO_CHARTS if c.type == "scatter"]),
            "heatmap": len([c for c in DEMO_CHARTS if c.type == "heatmap"]),
            "box": len([c for c in DEMO_CHARTS if c.type == "box"]),
        },
        "public_charts": len([c for c in DEMO_CHARTS if c.isPublic]),
        "private_charts": len([c for c in DEMO_CHARTS if not c.isPublic]),
        "data_sources": len(DATA_SOURCES),
    }


@router.post("/preview")
async def preview_chart(
    chart_type: str = Query(..., description="Chart type"),
    data_source: str = Query(..., description="Data source"),
    x_axis: Optional[str] = Query(None),
    y_axis: Optional[str] = Query(None),
    group_by: Optional[str] = Query(None),
):
    """Generate a preview of chart with given configuration."""
    return {
        "preview_url": f"/api/v2/visualizations/preview/{chart_type}",
        "config": {
            "type": chart_type,
            "dataSource": data_source,
            "xAxis": x_axis,
            "yAxis": y_axis,
            "groupBy": group_by
        },
        "estimated_records": random.randint(100, 10000)
    }


@router.post("/charts/{chart_id}/export")
async def export_chart(
    chart_id: str,
    format: str = Query("png", description="Export format: png, svg, pdf"),
    width: int = Query(800, ge=200, le=4000),
    height: int = Query(600, ge=200, le=3000),
):
    """Export chart as image."""
    chart = next((c for c in DEMO_CHARTS if c.id == chart_id), None)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    
    return {
        "message": f"Chart exported as {format.upper()}",
        "chart_id": chart_id,
        "format": format,
        "dimensions": {"width": width, "height": height},
        "download_url": f"/api/v2/visualizations/download/{chart_id}.{format}"
    }
