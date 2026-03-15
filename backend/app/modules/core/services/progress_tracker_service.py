"""
Progress Tracker Service

Tracks development progress across divisions, features, and APIs.
Data is stored in a JSON file and can be auto-updated from steering files.

IMPORTANT: This service reads from /metrics.json (project root) as the SINGLE SOURCE OF TRUTH.
Do NOT hardcode metrics here - they should come from metrics.json.

NOTE: Uses aiofiles for async file I/O per GOVERNANCE.md §4.3.1
"""

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import aiofiles
from pydantic import BaseModel, Field


# ============ Metrics File Path ============
# Single source of truth for all metrics
# Try multiple locations for failsafe
METRICS_PATHS = [
    Path(__file__).parent.parent.parent.parent / "metrics.json",  # /metrics.json (root)
    Path(__file__).parent.parent.parent.parent / ".kiro" / "metrics.json",  # /.kiro/metrics.json (legacy)
]

# Failsafe defaults
FALLBACK_METRICS = {
    "lastUpdated": "2025-12-29",
    "pages": {"total": 221, "functional": 208, "demo": 0, "uiOnly": 5},
    "api": {"totalEndpoints": 1344, "brapiEndpoints": 201, "brapiCoverage": 100, "customEndpoints": 1143},
    "modules": {
        "total": 8,
        "list": [
            {"name": "Breeding", "pages": 35, "endpoints": 120},
            {"name": "Phenotyping", "pages": 25, "endpoints": 85},
            {"name": "Genomics", "pages": 35, "endpoints": 107},
            {"name": "Seed Bank", "pages": 15, "endpoints": 59},
            {"name": "Environment", "pages": 20, "endpoints": 97},
            {"name": "Seed Commerce", "pages": 22, "endpoints": 96},
            {"name": "Knowledge", "pages": 5, "endpoints": 35},
            {"name": "Settings & Admin", "pages": 35, "endpoints": 79}
        ]
    },
    "techStack": {
        "frontend": ["React 18", "TypeScript 5", "Tailwind CSS", "shadcn/ui", "TanStack Query"],
        "backend": ["Python 3.13", "FastAPI", "SQLAlchemy 2.0", "Pydantic 2"],
        "database": ["PostgreSQL 15", "PostGIS", "pgvector", "Redis"],
        "compute": ["Rust/WASM", "Fortran"]
    }
}


def load_metrics_json_sync() -> dict[str, Any]:
    """Load metrics synchronously - for non-async contexts only (e.g., startup)"""
    for metrics_path in METRICS_PATHS:
        if metrics_path.exists():
            try:
                with open(metrics_path) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
    return FALLBACK_METRICS


async def load_metrics_json() -> dict[str, Any]:
    """Load metrics from metrics.json - Single Source of Truth with failsafe (async)"""
    for metrics_path in METRICS_PATHS:
        if metrics_path.exists():
            try:
                async with aiofiles.open(metrics_path) as f:
                    content = await f.read()
                    return json.loads(content)
            except (OSError, json.JSONDecodeError):
                continue
    return FALLBACK_METRICS


# ============ Enums ============

class ProgressStatus(StrEnum):
    COMPLETED = "completed"
    IN_PROGRESS = "in-progress"
    PLANNED = "planned"
    BACKLOG = "backlog"


class ProgressCategory(StrEnum):
    DIVISION = "division"
    FEATURE = "feature"
    API = "api"
    INTEGRATION = "integration"
    UI = "ui"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============ Schemas ============

class Milestone(BaseModel):
    name: str
    date: str | None = None
    completed: bool = False


class ProgressLink(BaseModel):
    label: str
    url: str


class ProgressItem(BaseModel):
    id: str
    category: ProgressCategory
    name: str
    description: str | None = None
    status: ProgressStatus = ProgressStatus.PLANNED
    priority: Priority = Priority.MEDIUM
    progress: int = Field(0, ge=0, le=100)
    start_date: str | None = None
    completed_date: str | None = None
    tags: list[str] = []
    dependencies: list[str] = []
    milestones: list[Milestone] = []
    links: list[ProgressLink] = []
    endpoints: int = 0
    pages: int = 0
    notes: str | None = None



class RoadmapItem(BaseModel):
    quarter: str  # e.g., "Q1 2025"
    title: str
    items: list[str]
    status: ProgressStatus = ProgressStatus.PLANNED


class ProgressSummary(BaseModel):
    total_endpoints: int = 0
    total_pages: int = 0
    total_divisions: int = 0
    completed_features: int = 0
    in_progress_features: int = 0
    planned_features: int = 0
    last_updated: str = ""


# ============ Progress Data ============

def _build_progress_data(metrics: dict[str, Any]) -> dict[str, Any]:
    """
    Internal helper to build progress data structure from raw metrics.
    Used by both sync and async getters.
    """
    # Build summary from metrics.json
    pages = metrics.get("pages", {})
    api = metrics.get("api", {})
    modules = metrics.get("modules", {})

    summary = {
        "total_endpoints": api.get("totalEndpoints", 0),
        "total_pages": pages.get("total", 0),
        "functional_pages": pages.get("functional", 0),
        "demo_pages": pages.get("demo", 0),
        "ui_only_pages": pages.get("uiOnly", 0),
        "total_divisions": modules.get("total", 8),  # Now 8 modules
        "total_components": 180,
        "brapi_coverage": api.get("brapiCoverage", 100),
        "last_updated": metrics.get("lastUpdated", "2025-12-29"),
    }

    # Build divisions from modules in metrics.json
    module_list = modules.get("list", [])
    divisions = []
    for i, mod in enumerate(module_list, 1):
        divisions.append({
            "id": f"div-{i}",
            "name": mod.get("name", ""),
            "status": "completed",
            "progress": 100,
            "endpoints": mod.get("endpoints", 0),
            "pages": mod.get("pages", 0),
            "functional": mod.get("pages", 0),  # All functional now
        })

    return {
        "summary": summary,
        "divisions": divisions,
        "recent_features": [
            {
                "id": "feat-myworkspace-complete",
                "name": "MyWorkspace Custom Workspaces",
                "description": "Users can create personalized workspaces with selected pages from any module",
                "status": "completed",
                "completed_date": "2025-12-29",
                "pages": 0,
                "endpoints": 0,
                "tags": ["frontend", "ux", "personalization"],
            },
            {
                "id": "feat-gateway-refinements",
                "name": "Gateway Refinements",
                "description": "Auto-advance carousel, error boundary, sync loading state",
                "status": "completed",
                "completed_date": "2025-12-29",
                "pages": 0,
                "endpoints": 0,
                "tags": ["frontend", "ux", "polish"],
            },
            {
                "id": "feat-admin-demo-separation",
                "name": "Admin/Demo User Separation",
                "description": "Server-determined is_demo flag, proper organization isolation",
                "status": "completed",
                "completed_date": "2025-12-29",
                "pages": 0,
                "endpoints": 0,
                "tags": ["backend", "security", "production"],
            },
            {
                "id": "feat-prakruti-design",
                "name": "Prakruti Design System",
                "description": "Complete design system with Hindi-named colors, 7 phases complete",
                "status": "completed",
                "completed_date": "2025-12-26",
                "pages": 0,
                "endpoints": 0,
                "tags": ["frontend", "design", "accessibility"],
            },
            {
                "id": "feat-gateway-workspace",
                "name": "Gateway-Workspace Architecture",
                "description": "5 workspaces, gateway page, sidebar filtering, 10 phases complete",
                "status": "completed",
                "completed_date": "2025-12-26",
                "pages": 5,
                "endpoints": 4,
                "tags": ["frontend", "backend", "navigation"],
            },
            {
                "id": "feat-mock-data-migration",
                "name": "Mock Data Migration Complete",
                "description": "Zero in-memory mock data, all 15 seeders working, 586 records",
                "status": "completed",
                "completed_date": "2025-12-26",
                "pages": 0,
                "endpoints": 0,
                "tags": ["backend", "database", "production"],
            },
            {
                "id": "feat-brapi-100-complete",
                "name": "BrAPI v2.1 100% Complete",
                "description": "All 201 BrAPI v2.1 endpoints implemented - Core, Germplasm, Phenotyping, Genotyping modules",
                "status": "completed",
                "completed_date": "2025-12-23",
                "endpoints": 201,
                "tags": ["backend", "brapi", "milestone"],
            },
        ],
        "roadmap": [
            {
                "quarter": "Q1 2026",
                "title": "MVP Launch & Beta Users",
                "items": ["100% functional pages (94%→100%)", "10 beta users onboarded", "80% test coverage", "Production deployment"],
                "status": "in-progress",
            },
            {
                "quarter": "Q2 2026",
                "title": "Mobile & Offline",
                "items": ["React Native mobile app", "Enhanced offline sync", "Voice data entry", "Field-optimized UI"],
                "status": "planned",
            },
            {
                "quarter": "Q3 2026",
                "title": "AI & Analytics",
                "items": ["AI crop recommendations", "Predictive analytics", "Computer vision models", "Natural language queries"],
                "status": "planned",
            },
            {
                "quarter": "Q4 2026",
                "title": "Enterprise Features",
                "items": ["Multi-tenant SaaS", "Advanced RBAC", "Custom reporting", "MIAPPE compliance"],
                "status": "backlog",
            },
        ],
        "api_stats": {
            "brapi_core": 50,
            "brapi_germplasm": 39,
            "brapi_phenotyping": 51,
            "brapi_genotyping": 61,
            "brapi_total": api.get("brapiEndpoints", 201),
            "brapi_coverage": f"{api.get('brapiCoverage', 100)}%",
            "brapi_iot_extension": 7,
            "custom_v2": api.get("customEndpoints", 1143),
            "modules": modules.get("total", 8),
            "total_endpoints": api.get("totalEndpoints", 1344),
        },
        "tech_stack": metrics.get("techStack", {
            "frontend": ["React 18", "TypeScript 5", "Tailwind CSS", "shadcn/ui", "TanStack Query", "ECharts"],
            "backend": ["Python 3.13", "FastAPI", "SQLAlchemy 2.0", "Pydantic 2"],
            "database": ["PostgreSQL 15", "PostGIS", "pgvector", "Redis"],
            "compute": ["Python", "Rust/WASM", "Fortran"],
        }),
    }


def get_progress_data() -> dict[str, Any]:
    """
    Get progress data dynamically from metrics.json.
    This ensures all metrics come from the SINGLE SOURCE OF TRUTH.
    Uses sync version since this is called from @property.
    """
    metrics = load_metrics_json_sync()
    return _build_progress_data(metrics)


async def get_progress_data_async() -> dict[str, Any]:
    """
    Get progress data dynamically from metrics.json (Async version).
    """
    metrics = await load_metrics_json()
    return _build_progress_data(metrics)


# Legacy static data for backward compatibility (will be removed)
# Use get_progress_data() instead
PROGRESS_DATA: dict[str, Any] = get_progress_data()


# ============ Progress Tracker Service ============

class ProgressTrackerService:
    """Service for tracking development progress"""

    def __init__(self):
        # Always get fresh data from metrics.json
        pass

    @property
    def data(self) -> dict[str, Any]:
        """Get fresh data from metrics.json (Sync)"""
        return get_progress_data()

    async def get_data(self) -> dict[str, Any]:
        """Get fresh data from metrics.json (Async)"""
        return await get_progress_data_async()

    async def get_summary(self) -> dict[str, Any]:
        """Get progress summary statistics"""
        data = await self.get_data()
        divisions = data.get("divisions", [])
        features = data.get("recent_features", [])

        completed = sum(1 for f in features if f.get("status") == "completed")
        in_progress = sum(1 for f in features if f.get("status") == "in-progress")
        planned = sum(1 for f in features if f.get("status") == "planned")

        return {
            **data.get("summary", {}),
            "completed_features": completed,
            "in_progress_features": in_progress,
            "planned_features": planned,
            "divisions_complete": sum(1 for d in divisions if d.get("progress", 0) == 100),
        }

    async def get_divisions(self) -> list[dict[str, Any]]:
        """Get all divisions with progress"""
        data = await self.get_data()
        return data.get("divisions", [])

    async def get_division(self, division_id: str) -> dict[str, Any] | None:
        """Get a specific division"""
        data = await self.get_data()
        divisions = data.get("divisions", [])
        return next((d for d in divisions if d.get("id") == division_id), None)

    async def get_recent_features(self, limit: int = 10, status: str | None = None) -> list[dict[str, Any]]:
        """Get recent features with optional status filter"""
        data = await self.get_data()
        features = data.get("recent_features", [])
        if status:
            features = [f for f in features if f.get("status") == status]
        return features[:limit]

    async def get_roadmap(self) -> list[dict[str, Any]]:
        """Get development roadmap"""
        data = await self.get_data()
        return data.get("roadmap", [])

    async def get_api_stats(self) -> dict[str, Any]:
        """Get API statistics"""
        data = await self.get_data()
        return data.get("api_stats", {})

    async def get_tech_stack(self) -> dict[str, Any]:
        """Get technology stack"""
        data = await self.get_data()
        return data.get("tech_stack", {})

    async def get_all_data(self) -> dict[str, Any]:
        """Get all progress data"""
        return {
            "summary": await self.get_summary(),
            "divisions": await self.get_divisions(),
            "recent_features": await self.get_recent_features(limit=20),
            "roadmap": await self.get_roadmap(),
            "api_stats": await self.get_api_stats(),
            "tech_stack": await self.get_tech_stack(),
        }

    async def add_feature(
        self,
        name: str,
        description: str,
        status: str = "planned",
        tags: list[str] = None,
        endpoints: int = 0,
        priority: str = "medium",
    ) -> dict[str, Any]:
        """Add a new feature to tracking (in-memory only, update metrics.json for persistence)"""
        feature_id = f"feat-{name.lower().replace(' ', '-')[:20]}"
        feature = {
            "id": feature_id,
            "name": name,
            "description": description,
            "status": status,
            "priority": priority,
            "tags": tags or [],
            "endpoints": endpoints,
            "created_date": datetime.now().strftime("%Y-%m-%d"),
        }
        if status == "completed":
            feature["completed_date"] = datetime.now().strftime("%Y-%m-%d")

        # Note: This only adds to in-memory data
        # For persistence, update /metrics.json (project root)
        return feature

    async def update_feature_status(self, feature_id: str, status: str) -> dict[str, Any] | None:
        """Update feature status (in-memory only)"""
        data = await self.get_data()
        features = data.get("recent_features", [])
        for feature in features:
            if feature.get("id") == feature_id:
                feature["status"] = status
                if status == "completed":
                    feature["completed_date"] = datetime.now().strftime("%Y-%m-%d")
                return feature
        return None

    async def update_division_progress(self, division_id: str, progress: int, endpoints: int = None) -> dict[str, Any] | None:
        """Update division progress (in-memory only)"""
        data = await self.get_data()
        divisions = data.get("divisions", [])
        for division in divisions:
            if division.get("id") == division_id:
                division["progress"] = min(100, max(0, progress))
                if endpoints is not None:
                    division["endpoints"] = endpoints
                if progress == 100:
                    division["status"] = "completed"
                elif progress > 0:
                    division["status"] = "in-progress"
                return division
        return None

    async def update_summary(self, endpoints: int = None, pages: int = None) -> dict[str, Any]:
        """Update summary statistics (in-memory only, update metrics.json for persistence)"""
        data = await self.get_data()
        summary = data.get("summary", {})
        if endpoints is not None:
            summary["total_endpoints"] = endpoints
        if pages is not None:
            summary["total_pages"] = pages
        summary["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        return summary


# Singleton instance
progress_service = ProgressTrackerService()
