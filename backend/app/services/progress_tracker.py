"""
Progress Tracker Service

Tracks development progress across divisions, features, and APIs.
Data is stored in a JSON file and can be auto-updated from steering files.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import json
import os


# ============ Enums ============

class ProgressStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in-progress"
    PLANNED = "planned"
    BACKLOG = "backlog"


class ProgressCategory(str, Enum):
    DIVISION = "division"
    FEATURE = "feature"
    API = "api"
    INTEGRATION = "integration"
    UI = "ui"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============ Schemas ============

class Milestone(BaseModel):
    name: str
    date: Optional[str] = None
    completed: bool = False


class ProgressLink(BaseModel):
    label: str
    url: str


class ProgressItem(BaseModel):
    id: str
    category: ProgressCategory
    name: str
    description: Optional[str] = None
    status: ProgressStatus = ProgressStatus.PLANNED
    priority: Priority = Priority.MEDIUM
    progress: int = Field(0, ge=0, le=100)
    start_date: Optional[str] = None
    completed_date: Optional[str] = None
    tags: List[str] = []
    dependencies: List[str] = []
    milestones: List[Milestone] = []
    links: List[ProgressLink] = []
    endpoints: int = 0
    pages: int = 0
    notes: Optional[str] = None



class RoadmapItem(BaseModel):
    quarter: str  # e.g., "Q1 2025"
    title: str
    items: List[str]
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

# This data structure mirrors what's in STATE.md
PROGRESS_DATA: Dict[str, Any] = {
    "summary": {
        "total_endpoints": 469,
        "total_pages": 271,
        "total_divisions": 11,
        "last_updated": "2025-12-10",
    },
    "divisions": [
        {"id": "div-1", "name": "Plant Sciences", "status": "completed", "progress": 100, "endpoints": 89, "pages": 45},
        {"id": "div-2", "name": "Seed Bank", "status": "completed", "progress": 100, "endpoints": 23, "pages": 9, "notes": "Production ready with MCPD support"},
        {"id": "div-3", "name": "Earth Systems", "status": "completed", "progress": 100, "endpoints": 28, "pages": 12},
        {"id": "div-4", "name": "Sun-Earth Systems", "status": "completed", "progress": 100, "endpoints": 12, "pages": 4},
        {"id": "div-5", "name": "Sensor Networks", "status": "completed", "progress": 100, "endpoints": 17, "pages": 4},
        {"id": "div-6", "name": "Commercial", "status": "completed", "progress": 100, "endpoints": 78, "pages": 21, "notes": "DUS Testing + Licensing UI complete"},
        {"id": "div-7", "name": "Space Research", "status": "completed", "progress": 100, "endpoints": 12, "pages": 4},
        {"id": "div-8", "name": "Integration Hub", "status": "completed", "progress": 100, "endpoints": 15, "pages": 3},
        {"id": "div-9", "name": "Knowledge", "status": "completed", "progress": 100, "endpoints": 12, "pages": 6},
        {"id": "div-10", "name": "Settings", "status": "completed", "progress": 100, "endpoints": 8, "pages": 4},
        {"id": "div-11", "name": "Home", "status": "completed", "progress": 100, "endpoints": 5, "pages": 3},
    ],
    "recent_features": [
        {
            "id": "feat-plant-sciences-pages",
            "name": "Plant Sciences Analysis Tools",
            "description": "Disease Resistance, Abiotic Stress, Bioinformatics, Crop Calendar, Spatial, Pedigree, and Phenotype Analysis",
            "status": "completed",
            "completed_date": "2025-12-10",
            "pages": 7,
            "tags": ["frontend", "plant-sciences", "molecular", "calendar", "spatial", "pedigree", "phenotype"],
        },
        {
            "id": "feat-detail-enhancements",
            "name": "Detail Page Enhancements",
            "description": "Progeny tracking, transaction history, data associations",
            "status": "completed",
            "completed_date": "2025-12-10",
            "tags": ["frontend", "ux"],
        },
        {
            "id": "feat-licensing-ui",
            "name": "Variety Licensing UI",
            "description": "Varieties, Agreements, Royalties pages with full API integration",
            "status": "completed",
            "completed_date": "2025-12-10",
            "pages": 3,
            "tags": ["frontend", "commercial"],
        },
        {
            "id": "feat-processing-stages",
            "name": "Processing Stages UI",
            "description": "10-stage seed processing workflow visualization",
            "status": "completed",
            "completed_date": "2025-12-10",
            "pages": 1,
            "tags": ["frontend", "seed-operations"],
        },
        {
            "id": "feat-dus-ui",
            "name": "DUS Testing Frontend",
            "description": "Trial management, character scoring, analysis UI",
            "status": "completed",
            "completed_date": "2025-12-10",
            "tags": ["frontend", "commercial"],
        },
        {
            "id": "feat-mcpd-ui",
            "name": "MCPD Import/Export UI",
            "description": "File upload, preview, validation, reference codes",
            "status": "completed",
            "completed_date": "2025-12-10",
            "tags": ["frontend", "seed-bank"],
        },
        {
            "id": "feat-progress-tracker",
            "name": "Dev Progress",
            "description": "Development progress dashboard with divisions, features, roadmap",
            "status": "completed",
            "completed_date": "2025-12-10",
            "endpoints": 11,
            "tags": ["backend", "frontend", "meta"],
        },
        {
            "id": "feat-dus",
            "name": "DUS Testing (UPOV)",
            "description": "Variety protection with 10 crop templates",
            "status": "completed",
            "completed_date": "2025-12-10",
            "endpoints": 17,
            "tags": ["backend", "commercial"],
        },
        {
            "id": "feat-mcpd",
            "name": "MCPD v2.1 Import/Export",
            "description": "Genebank data exchange standard",
            "status": "completed",
            "completed_date": "2025-12-10",
            "endpoints": 8,
            "tags": ["backend", "seed-bank"],
        },
        {
            "id": "feat-viz",
            "name": "Scientific Visualizations",
            "description": "PedigreeViewer, AMMIBiplot, KinshipNetwork, SpatialFieldPlot",
            "status": "completed",
            "completed_date": "2025-12-10",
            "tags": ["frontend", "charts"],
        },
        {
            "id": "feat-space",
            "name": "Space Research Division",
            "description": "Space crops, radiation calculator, life support",
            "status": "completed",
            "completed_date": "2025-12-10",
            "endpoints": 12,
            "tags": ["backend", "frontend"],
        },
        {
            "id": "feat-solar",
            "name": "Sun-Earth Systems Division",
            "description": "Photoperiod, UV index, solar activity",
            "status": "completed",
            "completed_date": "2025-12-10",
            "endpoints": 12,
            "tags": ["backend", "frontend"],
        },
        {
            "id": "feat-field-mode",
            "name": "Field Mode UI",
            "description": "WCAG AAA contrast, 48px touch targets",
            "status": "completed",
            "completed_date": "2025-12-10",
            "tags": ["frontend", "accessibility"],
        },
        {
            "id": "feat-virtual-scroll",
            "name": "Virtual Scrolling",
            "description": "100K+ row performance with @tanstack/react-virtual",
            "status": "completed",
            "completed_date": "2025-12-10",
            "tags": ["frontend", "performance"],
        },
    ],
    "roadmap": [
        {
            "quarter": "Q1 2026",
            "title": "Standards & Compliance",
            "items": ["MIAPPE compliance", "RTL language support", "ORCID integration", "DOI/PUID integration"],
            "status": "planned",
        },
        {
            "quarter": "Q2 2026",
            "title": "Mobile & Offline",
            "items": ["React Native mobile app", "Enhanced offline sync", "Barcode/QR scanning", "Voice data entry"],
            "status": "planned",
        },
        {
            "quarter": "Q3 2026",
            "title": "AI & Analytics",
            "items": ["AI crop recommendations", "Predictive analytics", "Computer vision models", "Natural language queries"],
            "status": "backlog",
        },
        {
            "quarter": "Q4 2026",
            "title": "Enterprise Features",
            "items": ["Multi-tenant SaaS", "Advanced RBAC", "Audit logging", "Custom reporting"],
            "status": "backlog",
        },
    ],
    "api_stats": {
        "brapi_endpoints": 34,
        "custom_endpoints": 435,
        "total_endpoints": 469,
    },
    "tech_stack": {
        "frontend": ["React 18", "TypeScript 5", "Tailwind CSS", "shadcn/ui", "TanStack Query", "ECharts"],
        "backend": ["Python 3.11", "FastAPI", "SQLAlchemy 2.0", "Pydantic 2"],
        "database": ["PostgreSQL 15", "PostGIS", "pgvector", "Redis"],
        "compute": ["Python", "Rust/WASM", "Fortran"],
    },
}



# ============ Progress Tracker Service ============

class ProgressTrackerService:
    """Service for tracking development progress"""
    
    def __init__(self):
        self.data = PROGRESS_DATA
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary statistics"""
        divisions = self.data.get("divisions", [])
        features = self.data.get("recent_features", [])
        
        completed = sum(1 for f in features if f.get("status") == "completed")
        in_progress = sum(1 for f in features if f.get("status") == "in-progress")
        planned = sum(1 for f in features if f.get("status") == "planned")
        
        return {
            **self.data.get("summary", {}),
            "completed_features": completed,
            "in_progress_features": in_progress,
            "planned_features": planned,
            "divisions_complete": sum(1 for d in divisions if d.get("progress", 0) == 100),
        }
    
    def get_divisions(self) -> List[Dict[str, Any]]:
        """Get all divisions with progress"""
        return self.data.get("divisions", [])
    
    def get_division(self, division_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific division"""
        divisions = self.data.get("divisions", [])
        return next((d for d in divisions if d.get("id") == division_id), None)
    
    def get_recent_features(self, limit: int = 10, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent features with optional status filter"""
        features = self.data.get("recent_features", [])
        if status:
            features = [f for f in features if f.get("status") == status]
        return features[:limit]
    
    def get_roadmap(self) -> List[Dict[str, Any]]:
        """Get development roadmap"""
        return self.data.get("roadmap", [])
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get API statistics"""
        return self.data.get("api_stats", {})
    
    def get_tech_stack(self) -> Dict[str, Any]:
        """Get technology stack"""
        return self.data.get("tech_stack", {})
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all progress data"""
        return {
            "summary": self.get_summary(),
            "divisions": self.get_divisions(),
            "recent_features": self.get_recent_features(limit=20),
            "roadmap": self.get_roadmap(),
            "api_stats": self.get_api_stats(),
            "tech_stack": self.get_tech_stack(),
        }
    
    def add_feature(
        self,
        name: str,
        description: str,
        status: str = "planned",
        tags: List[str] = None,
        endpoints: int = 0,
        priority: str = "medium",
    ) -> Dict[str, Any]:
        """Add a new feature to tracking"""
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
        
        self.data["recent_features"].insert(0, feature)
        return feature
    
    def update_feature_status(self, feature_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update feature status"""
        features = self.data.get("recent_features", [])
        for feature in features:
            if feature.get("id") == feature_id:
                feature["status"] = status
                if status == "completed":
                    feature["completed_date"] = datetime.now().strftime("%Y-%m-%d")
                return feature
        return None
    
    def update_division_progress(self, division_id: str, progress: int, endpoints: int = None) -> Optional[Dict[str, Any]]:
        """Update division progress"""
        divisions = self.data.get("divisions", [])
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
    
    def update_summary(self, endpoints: int = None, pages: int = None) -> Dict[str, Any]:
        """Update summary statistics"""
        summary = self.data.get("summary", {})
        if endpoints is not None:
            summary["total_endpoints"] = endpoints
        if pages is not None:
            summary["total_pages"] = pages
        summary["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        return summary


# Singleton instance
progress_service = ProgressTrackerService()
