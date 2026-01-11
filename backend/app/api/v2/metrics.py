"""
Metrics API - Single Source of Truth

Serves metrics from /metrics.json (project root) for dynamic updates across:
- Frontend Dev Progress page
- About page
- README badges (via shields.io)

FAILSAFE: If metrics.json is not found, returns sensible defaults.

NOTE: Uses aiofiles for async file I/O per GOVERNANCE.md §4.3.1
"""

import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import aiofiles
import aiofiles.os

router = APIRouter(prefix="/metrics", tags=["Metrics"])

# Path to metrics file (project root)
# Try multiple locations for failsafe
METRICS_PATHS = [
    Path(__file__).parent.parent.parent.parent.parent / "metrics.json",  # /metrics.json (root)
    Path(__file__).parent.parent.parent.parent.parent / ".kiro" / "metrics.json",  # /.kiro/metrics.json (legacy)
]

# Failsafe defaults if file not found
FALLBACK_METRICS = {
    "lastUpdated": "2025-12-29",
    "updatedBy": "Fallback (metrics.json not found)",
    "session": 0,
    "pages": {
        "total": 221,
        "functional": 208,
        "demo": 0,
        "uiOnly": 5,
        "removed": 12,
        "note": "Fallback data - metrics.json not found"
    },
    "api": {
        "totalEndpoints": 1344,
        "brapiEndpoints": 201,
        "brapiCoverage": 100,
        "customEndpoints": 1143
    },
    "database": {
        "models": 97,
        "migrations": 19,
        "seeders": 15,
        "tables": 106,
        "seededRecords": 413
    },
    "modules": {
        "total": 8,
        "list": [
            {"name": "Breeding", "pages": 35, "endpoints": 120},
            {"name": "Phenotyping", "pages": 25, "endpoints": 85},
            {"name": "Genomics", "pages": 35, "endpoints": 107},
            {"name": "Seed Bank", "pages": 15, "endpoints": 59},
            {"name": "Environment", "pages": 20, "endpoints": 97},
            {"name": "Seed Operations", "pages": 22, "endpoints": 96},
            {"name": "Knowledge", "pages": 5, "endpoints": 35},
            {"name": "Settings & Admin", "pages": 35, "endpoints": 79}
        ]
    },
    "workspaces": {
        "total": 5,
        "list": [
            {"id": "breeding", "name": "Plant Breeding", "pages": 83},
            {"id": "seed-ops", "name": "Seed Business", "pages": 22},
            {"id": "research", "name": "Innovation Lab", "pages": 28},
            {"id": "genebank", "name": "Gene Bank", "pages": 34},
            {"id": "admin", "name": "Administration", "pages": 25}
        ]
    },
    "build": {
        "status": "passing",
        "pwaEntries": 116,
        "sizeKB": 7960,
        "sizeMB": "7.9MB"
    },
    "milestones": {
        "brapiComplete": "2025-12-23",
        "gatewayComplete": "2025-12-26",
        "prakrutiComplete": "2025-12-26",
        "productionReady": "2025-12-25"
    },
    "techStack": {
        "frontend": ["React 18", "TypeScript 5", "Vite 5", "Tailwind CSS", "TanStack Query"],
        "backend": ["Python 3.11", "FastAPI", "SQLAlchemy 2.0", "Pydantic 2"],
        "database": ["PostgreSQL 15", "PostGIS", "pgvector", "Redis"],
        "compute": ["Rust/WASM", "Fortran"]
    }
}


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


async def load_metrics() -> dict:
    """Load metrics from JSON file with failsafe fallback (async)"""
    # Try each path in order
    for metrics_path in METRICS_PATHS:
        if metrics_path.exists():
            try:
                async with aiofiles.open(metrics_path, "r") as f:
                    content = await f.read()
                    return json.loads(content)
            except (json.JSONDecodeError, IOError):
                continue
    
    # Return fallback if no file found
    return FALLBACK_METRICS


@router.get("")
async def get_all_metrics():
    """Get all metrics from single source of truth"""
    return await load_metrics()


@router.get("/summary")
async def get_metrics_summary() -> MetricsSummary:
    """Get summary metrics for badges and quick display"""
    data = await load_metrics()
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


@router.get("/version")
async def get_version():
    """Get version information from single source of truth"""
    data = await load_metrics()
    version_data = data.get("version", {
        "app": "0.2.0",
        "brapi": "2.1",
        "schema": "1.0.0"
    })
    return {
        "app": version_data.get("app", "0.2.0"),
        "brapi": version_data.get("brapi", "2.1"),
        "schema": version_data.get("schema", "1.0.0"),
        "lastUpdated": data.get("lastUpdated", "unknown")
    }


@router.get("/pages")
async def get_page_metrics() -> PageMetrics:
    """Get page metrics"""
    data = await load_metrics()
    return PageMetrics(**data["pages"])


@router.get("/api")
async def get_api_metrics() -> ApiMetrics:
    """Get API metrics"""
    data = await load_metrics()
    return ApiMetrics(**data["api"])


@router.get("/database")
async def get_database_metrics() -> DatabaseMetrics:
    """Get database metrics"""
    data = await load_metrics()
    return DatabaseMetrics(**data["database"])


@router.get("/build")
async def get_build_metrics() -> BuildMetrics:
    """Get build metrics"""
    data = await load_metrics()
    return BuildMetrics(**data["build"])


@router.get("/modules")
async def get_modules():
    """Get module breakdown"""
    data = await load_metrics()
    return data["modules"]


@router.get("/workspaces")
async def get_workspaces():
    """Get workspace breakdown"""
    data = await load_metrics()
    return data["workspaces"]


@router.get("/milestones")
async def get_milestones():
    """Get milestone dates"""
    data = await load_metrics()
    return data["milestones"]


@router.get("/tech-stack")
async def get_tech_stack():
    """Get technology stack"""
    data = await load_metrics()
    return data["techStack"]


# Badge endpoints for shields.io dynamic badges
@router.get("/badge/pages")
async def badge_pages():
    """Badge data for pages count"""
    data = await load_metrics()
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
    data = await load_metrics()
    return {
        "schemaVersion": 1,
        "label": "API endpoints",
        "message": str(data["api"]["totalEndpoints"]),
        "color": "blue"
    }


@router.get("/badge/brapi")
async def badge_brapi():
    """Badge data for BrAPI coverage"""
    data = await load_metrics()
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
    data = await load_metrics()
    status = data["build"]["status"]
    return {
        "schemaVersion": 1,
        "label": "build",
        "message": status,
        "color": "brightgreen" if status == "passing" else "red"
    }


@router.get("/badge/version")
async def badge_version():
    """Badge data for app version"""
    data = await load_metrics()
    version = data.get("version", {}).get("app", "0.2.0")
    return {
        "schemaVersion": 1,
        "label": "version",
        "message": f"v{version}",
        "color": "blue"
    }
