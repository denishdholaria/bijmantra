"""
Metrics API - Single Source of Truth

Serves metrics from .kiro/metrics.json for dynamic updates across:
- Frontend Dev Progress page
- About page
- README badges (via shields.io)
"""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/metrics", tags=["Metrics"])

# Path to metrics file (relative to backend directory)
METRICS_FILE = Path(__file__).parent.parent.parent.parent.parent / ".kiro" / "metrics.json"


class PageMetrics(BaseModel):
    total: int
    functional: int
    demo: int
    uiOnly: int
    removed: int
    note: Optional[str] = None


class ApiMetrics(BaseModel):
    totalEndpoints: int
    brapiEndpoints: int
    brapiCoverage: int
    customEndpoints: int


class DatabaseMetrics(BaseModel):
    models: int
    migrations: int
    seeders: int


class BuildMetrics(BaseModel):
    status: str
    pwaEntries: int
    sizeKB: int
    sizeMB: str


class MetricsSummary(BaseModel):
    """Summary metrics for badges and quick display"""
    pages: int
    functionalPercent: int
    endpoints: int
    brapiCoverage: int
    models: int
    modules: int
    workspaces: int
    buildStatus: str


def load_metrics() -> dict:
    """Load metrics from JSON file"""
    if not METRICS_FILE.exists():
        raise HTTPException(status_code=404, detail="Metrics file not found")
    
    with open(METRICS_FILE, "r") as f:
        return json.load(f)


@router.get("")
async def get_all_metrics():
    """Get all metrics from single source of truth"""
    return load_metrics()


@router.get("/summary")
async def get_metrics_summary() -> MetricsSummary:
    """Get summary metrics for badges and quick display"""
    data = load_metrics()
    pages = data["pages"]
    
    return MetricsSummary(
        pages=pages["total"],
        functionalPercent=round(pages["functional"] / pages["total"] * 100),
        endpoints=data["api"]["totalEndpoints"],
        brapiCoverage=data["api"]["brapiCoverage"],
        models=data["database"]["models"],
        modules=data["modules"]["total"],
        workspaces=data["workspaces"]["total"],
        buildStatus=data["build"]["status"]
    )


@router.get("/pages")
async def get_page_metrics() -> PageMetrics:
    """Get page metrics"""
    return PageMetrics(**load_metrics()["pages"])


@router.get("/api")
async def get_api_metrics() -> ApiMetrics:
    """Get API metrics"""
    return ApiMetrics(**load_metrics()["api"])


@router.get("/database")
async def get_database_metrics() -> DatabaseMetrics:
    """Get database metrics"""
    return DatabaseMetrics(**load_metrics()["database"])


@router.get("/build")
async def get_build_metrics() -> BuildMetrics:
    """Get build metrics"""
    return BuildMetrics(**load_metrics()["build"])


@router.get("/modules")
async def get_modules():
    """Get module breakdown"""
    return load_metrics()["modules"]


@router.get("/workspaces")
async def get_workspaces():
    """Get workspace breakdown"""
    return load_metrics()["workspaces"]


@router.get("/milestones")
async def get_milestones():
    """Get milestone dates"""
    return load_metrics()["milestones"]


@router.get("/tech-stack")
async def get_tech_stack():
    """Get technology stack"""
    return load_metrics()["techStack"]


# Badge endpoints for shields.io dynamic badges
@router.get("/badge/pages")
async def badge_pages():
    """Badge data for pages count"""
    data = load_metrics()
    pages = data["pages"]
    return {
        "schemaVersion": 1,
        "label": "pages",
        "message": f"{pages['functional']}/{pages['total']} functional",
        "color": "green" if pages["functional"] / pages["total"] > 0.8 else "yellow"
    }


@router.get("/badge/endpoints")
async def badge_endpoints():
    """Badge data for endpoint count"""
    data = load_metrics()
    return {
        "schemaVersion": 1,
        "label": "API endpoints",
        "message": str(data["api"]["totalEndpoints"]),
        "color": "blue"
    }


@router.get("/badge/brapi")
async def badge_brapi():
    """Badge data for BrAPI coverage"""
    data = load_metrics()
    coverage = data["api"]["brapiCoverage"]
    return {
        "schemaVersion": 1,
        "label": "BrAPI v2.1",
        "message": f"{coverage}%",
        "color": "brightgreen" if coverage == 100 else "yellow"
    }


@router.get("/badge/build")
async def badge_build():
    """Badge data for build status"""
    data = load_metrics()
    status = data["build"]["status"]
    return {
        "schemaVersion": 1,
        "label": "build",
        "message": status,
        "color": "brightgreen" if status == "passing" else "red"
    }
