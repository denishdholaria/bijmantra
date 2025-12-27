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
# UPDATED: Dec 24, 2025 - SWAYAM TURBO Session 7 Complete
PROGRESS_DATA: Dict[str, Any] = {
    "summary": {
        "total_endpoints": 1340,  # Updated Dec 24, 2025 (verified via grep)
        "total_pages": 302,       # Updated Dec 24, 2025
        "functional_pages": 227,  # 75% functional (Session 7 complete)
        "demo_pages": 41,         # 14% demo data
        "ui_only_pages": 34,      # 11% UI only
        "total_divisions": 11,
        "total_components": 180,
        "brapi_coverage": 100,    # 201/201 BrAPI v2.1 endpoints
        "last_updated": "2025-12-24",
    },
    "divisions": [
        {"id": "div-1", "name": "Plant Sciences", "status": "completed", "progress": 100, "endpoints": 312, "pages": 110, "functional": 97, "notes": "BreedingPipeline, YieldPredictor, BreedingValueCalculator, Progeny, ParentSelection all connected"},
        {"id": "div-2", "name": "Seed Bank", "status": "completed", "progress": 100, "endpoints": 59, "pages": 15, "functional": 15, "notes": "Production ready with MCPD, MTA, GRIN, IoT monitoring, offline data entry"},
        {"id": "div-3", "name": "Earth Systems", "status": "completed", "progress": 100, "endpoints": 54, "pages": 9, "functional": 9, "notes": "Weather, soil, crop calendar, irrigation all connected"},
        {"id": "div-4", "name": "Sun-Earth Systems", "status": "completed", "progress": 100, "endpoints": 11, "pages": 4, "functional": 4},
        {"id": "div-5", "name": "Sensor Networks", "status": "completed", "progress": 100, "endpoints": 25, "pages": 7, "functional": 7, "notes": "BrAPI IoT Extension + 16 sensor API methods"},
        {"id": "div-6", "name": "Commercial", "status": "completed", "progress": 100, "endpoints": 96, "pages": 22, "functional": 22, "notes": "DUS Testing + Licensing + Crossing Projects"},
        {"id": "div-7", "name": "Space Research", "status": "completed", "progress": 100, "endpoints": 11, "pages": 4, "functional": 4},
        {"id": "div-8", "name": "Integration Hub", "status": "completed", "progress": 100, "endpoints": 7, "pages": 1, "functional": 1},
        {"id": "div-9", "name": "Knowledge", "status": "completed", "progress": 100, "endpoints": 35, "pages": 10, "functional": 3, "notes": "Forums, training, docs"},
        {"id": "div-10", "name": "System", "status": "completed", "progress": 100, "endpoints": 72, "pages": 32, "functional": 30, "notes": "Security, settings, admin, audit"},
        {"id": "div-11", "name": "Home", "status": "completed", "progress": 100, "endpoints": 18, "pages": 12, "functional": 12},
    ],
    "recent_features": [
        {
            "id": "feat-swayam-turbo-session-7",
            "name": "SWAYAM TURBO Session 7",
            "description": "BreedingPipeline, YieldPredictor, BreedingValueCalculator converted to real APIs (+21 typed methods)",
            "status": "completed",
            "completed_date": "2025-12-24",
            "pages": 3,
            "endpoints": 21,
            "tags": ["frontend", "api-integration", "breeding"],
        },
        {
            "id": "feat-swayam-turbo-session-6",
            "name": "SWAYAM TURBO Session 6",
            "description": "GermplasmSearch, Progeny, HarvestManagement, ParentSelection converted (+42 typed methods)",
            "status": "completed",
            "completed_date": "2025-12-24",
            "pages": 4,
            "endpoints": 42,
            "tags": ["frontend", "api-integration", "germplasm"],
        },
        {
            "id": "feat-swayam-turbo-session-5",
            "name": "SWAYAM TURBO Session 5",
            "description": "GeneticGainTracker, SpatialAnalysis, PopulationGenetics, TrialNetwork converted (+35 typed methods)",
            "status": "completed",
            "completed_date": "2025-12-24",
            "pages": 4,
            "endpoints": 35,
            "tags": ["frontend", "api-integration", "analytics"],
        },
        {
            "id": "feat-swayam-turbo-session-4",
            "name": "SWAYAM TURBO Session 4",
            "description": "ApexAnalytics, AdvancedReports, DataSync, CollaborationHub - 4 new backend APIs (+60 endpoints)",
            "status": "completed",
            "completed_date": "2025-12-24",
            "pages": 4,
            "endpoints": 60,
            "tags": ["backend", "frontend", "api-integration"],
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
        {
            "id": "feat-search-db-migration",
            "name": "Search Endpoints Database Migration",
            "description": "All 24 BrAPI search endpoints migrated from demo_results to real database queries",
            "status": "completed",
            "completed_date": "2025-12-23",
            "endpoints": 48,
            "tags": ["backend", "brapi", "database"],
        },
        {
            "id": "feat-earth-systems-functional",
            "name": "Earth Systems Demo→Functional",
            "description": "Weather, Soil Analysis, Crop Calendar, Environment Monitor, Irrigation Planner connected to APIs",
            "status": "completed",
            "completed_date": "2025-12-23",
            "pages": 6,
            "endpoints": 45,
            "tags": ["frontend", "earth-systems", "api-integration"],
        },
        {
            "id": "feat-breeding-analysis-functional",
            "name": "Breeding Analysis Demo→Functional",
            "description": "Breeding Values, Phenotype Comparison, Yield Map, Crossing Projects, Germplasm Attributes connected",
            "status": "completed",
            "completed_date": "2025-12-23",
            "pages": 5,
            "endpoints": 15,
            "tags": ["frontend", "plant-sciences", "api-integration"],
        },
        {
            "id": "feat-production-infrastructure",
            "name": "Production Infrastructure",
            "description": "Docker dev/prod split, database seeders, demo organization isolation, Caddy reverse proxy",
            "status": "completed",
            "completed_date": "2025-12-23",
            "tags": ["backend", "infrastructure", "production"],
        },
        {
            "id": "feat-genotyping-db-models",
            "name": "Genotyping Database Models",
            "description": "12 new models: ReferenceSet, Reference, GenomeMap, Variant, VariantSet, CallSet, Call, Plate, etc.",
            "status": "completed",
            "completed_date": "2025-12-23",
            "endpoints": 61,
            "tags": ["backend", "database", "genotyping"],
        },
        {
            "id": "feat-phenotyping-db-models",
            "name": "Phenotyping Database Models",
            "description": "6 new models for observations, observation units, variables, images, samples",
            "status": "completed",
            "completed_date": "2025-12-23",
            "endpoints": 51,
            "tags": ["backend", "database", "phenotyping"],
        },
        {
            "id": "feat-api-client-expansion",
            "name": "API Client Expansion",
            "description": "75+ new frontend API client methods for weather, soil, sensors, breeding values, phenotypes",
            "status": "completed",
            "completed_date": "2025-12-23",
            "tags": ["frontend", "api-client"],
        },
        {
            "id": "feat-forensic-audit",
            "name": "Forensic Codebase Audit",
            "description": "Verified actual API endpoints (935→1161) and pages (301→302) via source code analysis",
            "status": "completed",
            "completed_date": "2025-12-20",
            "endpoints": 0,
            "tags": ["audit", "metrics"],
        },
        {
            "id": "feat-resource-management",
            "name": "Resource Management",
            "description": "Budget tracking, staff allocation, field utilization, calendar scheduling, harvest logging",
            "status": "completed",
            "completed_date": "2025-12-20",
            "endpoints": 15,
            "tags": ["backend", "frontend"],
        },
        {
            "id": "feat-brapi-iot",
            "name": "BrAPI IoT Extension",
            "description": "7 new endpoints for sensor telemetry, aggregates, and environment linking",
            "status": "completed",
            "completed_date": "2025-12-20",
            "endpoints": 7,
            "tags": ["backend", "brapi", "iot"],
        },
        {
            "id": "feat-demo-mode",
            "name": "Demo Mode System",
            "description": "Toggle between demo and production data for learning and training purposes",
            "status": "completed",
            "completed_date": "2025-12-12",
            "endpoints": 0,
            "tags": ["frontend", "ux", "demo", "training"],
        },
        {
            "id": "feat-functionality-audit",
            "name": "Functionality Audit System",
            "description": "Comprehensive tracking of page production-readiness with priority queue",
            "status": "completed",
            "completed_date": "2025-12-12",
            "endpoints": 0,
            "tags": ["documentation", "tracking", "quality"],
        },
        {
            "id": "feat-germplasm-comparison",
            "name": "Germplasm Comparison Tool",
            "description": "Side-by-side germplasm comparison for selection decisions with trait and marker analysis",
            "status": "completed",
            "completed_date": "2025-12-12",
            "endpoints": 0,
            "tags": ["frontend", "plant-sciences", "breeding", "selection", "comparison"],
        },
        {
            "id": "feat-vision-strategy",
            "name": "Plant Vision Strategy",
            "description": "Multi-tier approach to plant disease detection with community data collection",
            "status": "completed",
            "completed_date": "2025-12-12",
            "endpoints": 0,
            "tags": ["frontend", "plant-sciences", "ai", "vision", "strategy"],
        },
        {
            "id": "feat-offline-entry",
            "name": "Offline Data Entry",
            "description": "PWA-enabled field data collection for Seed Bank with GPS and sync workflow",
            "status": "completed",
            "completed_date": "2025-12-12",
            "endpoints": 0,
            "tags": ["frontend", "seed-bank", "pwa", "offline", "field-work"],
        },
        {
            "id": "feat-vault-sensors",
            "name": "Vault Sensor Integration (IoT)",
            "description": "Real-time environmental monitoring for Seed Bank vaults with threshold alerts",
            "status": "completed",
            "completed_date": "2025-12-12",
            "endpoints": 15,
            "tags": ["backend", "frontend", "seed-bank", "iot", "monitoring"],
        },
        {
            "id": "feat-barcode-system",
            "name": "Barcode/QR Scanning System",
            "description": "Complete barcode management with camera scanning for seed operations",
            "status": "completed",
            "completed_date": "2025-12-12",
            "endpoints": 9,
            "tags": ["backend", "frontend", "seed-operations", "scanning"],
        },
        {
            "id": "feat-mta-workflow",
            "name": "Material Transfer Agreement (MTA) Workflow",
            "description": "Complete MTA management for germplasm exchange compliance under ITPGRFA",
            "status": "completed",
            "completed_date": "2025-12-12",
            "endpoints": 15,
            "tags": ["backend", "frontend", "seed-bank", "compliance"],
        },
        {
            "id": "feat-ashta-stambha-complete",
            "name": "ASHTA-STAMBHA Security Framework Complete",
            "description": "Full security framework with eight pillars: defense, monitoring, threat analysis, response, self-healing, and central orchestration",
            "status": "completed",
            "completed_date": "2025-12-11",
            "endpoints": 29,
            "pages": 1,
            "tags": ["backend", "security", "monitoring", "self-healing", "defense", "orchestration"],
        },
    ],
    "roadmap": [
        {
            "quarter": "Q1 2026",
            "title": "MVP Launch & Beta Users",
            "items": ["100% functional pages (67%→100%)", "10 beta users onboarded", "80% test coverage", "Production deployment"],
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
        "brapi_total": 201,
        "brapi_coverage": "100%",
        "brapi_iot_extension": 7,
        "custom_v2": 1132,
        "modules": 37,
        "total_endpoints": 1340,  # Updated Dec 24, 2025 (verified via grep)
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
