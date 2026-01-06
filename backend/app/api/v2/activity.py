"""
Activity Timeline API
Track all changes and activities in the breeding program
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from enum import Enum
import uuid

router = APIRouter(prefix="/activity", tags=["Activity"])


class ActivityType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    IMPORT = "import"
    EXPORT = "export"
    VIEW = "view"


class ActivityEntity(str, Enum):
    GERMPLASM = "Germplasm"
    TRIAL = "Trial"
    STUDY = "Study"
    OBSERVATION = "Observation"
    CROSS = "Cross"
    LOCATION = "Location"
    PROGRAM = "Program"
    SAMPLE = "Sample"
    SEEDLOT = "Seedlot"
    REPORT = "Report"


# In-memory store (would be database in production)
_activities: List[dict] = []


def _init_demo_activities():
    """Initialize demo activities if empty"""
    global _activities
    if not _activities:
        now = datetime.now(timezone.utc)
        _activities = [
            {
                "id": "act001",
                "type": "create",
                "entity": "Germplasm",
                "entity_id": "GERM-2025-001",
                "entity_name": "BM-Gold-2025",
                "user": "Dr. Sarah Johnson",
                "user_id": "user001",
                "timestamp": (now - timedelta(minutes=10)).isoformat(),
                "details": "New elite line registered with high yield potential"
            },
            {
                "id": "act002",
                "type": "update",
                "entity": "Trial",
                "entity_id": "TRIAL-2025-047",
                "entity_name": "Yield Trial Spring 2025",
                "user": "John Smith",
                "user_id": "user002",
                "timestamp": (now - timedelta(minutes=25)).isoformat(),
                "details": "Status changed from Planning to Active"
            },
            {
                "id": "act003",
                "type": "import",
                "entity": "Observation",
                "entity_id": "BATCH-001",
                "entity_name": "1,247 observations",
                "user": "Maria Garcia",
                "user_id": "user003",
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "details": "Field data imported from mobile devices"
            },
            {
                "id": "act004",
                "type": "create",
                "entity": "Cross",
                "entity_id": "CROSS-2025-089",
                "entity_name": "IR64 × FR13A",
                "user": "Dr. Raj Patel",
                "user_id": "user004",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "details": "Submergence tolerance cross initiated"
            },
            {
                "id": "act005",
                "type": "export",
                "entity": "Report",
                "entity_id": "RPT-2025-012",
                "entity_name": "Monthly Progress Report",
                "user": "Admin",
                "user_id": "admin",
                "timestamp": (now - timedelta(hours=3)).isoformat(),
                "details": "PDF export completed successfully"
            },
            {
                "id": "act006",
                "type": "update",
                "entity": "Germplasm",
                "entity_id": "GERM-2024-456",
                "entity_name": "Swarna-Sub1",
                "user": "Dr. Sarah Johnson",
                "user_id": "user001",
                "timestamp": (now - timedelta(hours=4)).isoformat(),
                "details": "Pedigree information updated with verified parentage"
            },
            {
                "id": "act007",
                "type": "delete",
                "entity": "Observation",
                "entity_id": "OBS-2025-789",
                "entity_name": "Duplicate entry",
                "user": "John Smith",
                "user_id": "user002",
                "timestamp": (now - timedelta(hours=5)).isoformat(),
                "details": "Removed duplicate observation record"
            },
            {
                "id": "act008",
                "type": "view",
                "entity": "Trial",
                "entity_id": "TRIAL-2024-089",
                "entity_name": "Disease Screening 2024",
                "user": "Guest User",
                "user_id": "guest",
                "timestamp": (now - timedelta(hours=6)).isoformat(),
                "details": None
            },
            {
                "id": "act009",
                "type": "create",
                "entity": "Location",
                "entity_id": "LOC-2025-003",
                "entity_name": "North Field Block C",
                "user": "Admin",
                "user_id": "admin",
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "details": "New trial location added with GPS coordinates"
            },
            {
                "id": "act010",
                "type": "import",
                "entity": "Germplasm",
                "entity_id": "BATCH-002",
                "entity_name": "234 accessions",
                "user": "Dr. Raj Patel",
                "user_id": "user004",
                "timestamp": (now - timedelta(days=1, hours=2)).isoformat(),
                "details": "Genebank import from IRRI collection"
            },
            {
                "id": "act011",
                "type": "create",
                "entity": "Study",
                "entity_id": "STUDY-2025-015",
                "entity_name": "Drought Tolerance Screening",
                "user": "Dr. Priya Sharma",
                "user_id": "user005",
                "timestamp": (now - timedelta(days=1, hours=5)).isoformat(),
                "details": "New study created under Abiotic Stress Program"
            },
            {
                "id": "act012",
                "type": "update",
                "entity": "Seedlot",
                "entity_id": "SL-2025-001",
                "entity_name": "IR64 Foundation Seed",
                "user": "Maria Garcia",
                "user_id": "user003",
                "timestamp": (now - timedelta(days=2)).isoformat(),
                "details": "Inventory updated: 500g added from harvest"
            },
            {
                "id": "act013",
                "type": "create",
                "entity": "Sample",
                "entity_id": "SAMP-2025-089",
                "entity_name": "DNA Sample Batch 12",
                "user": "Lab Tech",
                "user_id": "labtech",
                "timestamp": (now - timedelta(days=2, hours=3)).isoformat(),
                "details": "96 samples prepared for genotyping"
            },
            {
                "id": "act014",
                "type": "export",
                "entity": "Germplasm",
                "entity_id": "EXP-2025-003",
                "entity_name": "BrAPI Export",
                "user": "Admin",
                "user_id": "admin",
                "timestamp": (now - timedelta(days=3)).isoformat(),
                "details": "Exported 1,500 germplasm records to partner institution"
            },
            {
                "id": "act015",
                "type": "update",
                "entity": "Program",
                "entity_id": "PROG-001",
                "entity_name": "Rice Breeding Program",
                "user": "Dr. Sarah Johnson",
                "user_id": "user001",
                "timestamp": (now - timedelta(days=3, hours=6)).isoformat(),
                "details": "Annual objectives updated for 2025"
            },
        ]


@router.get("")
async def get_activities(
    type: Optional[str] = Query(None, description="Filter by activity type"),
    entity: Optional[str] = Query(None, description="Filter by entity type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    search: Optional[str] = Query(None, description="Search in entity name or details"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get activity timeline with optional filters"""
    _init_demo_activities()
    
    filtered = _activities.copy()
    
    # Apply filters
    if type:
        filtered = [a for a in filtered if a["type"] == type]
    if entity:
        filtered = [a for a in filtered if a["entity"].lower() == entity.lower()]
    if user_id:
        filtered = [a for a in filtered if a["user_id"] == user_id]
    if search:
        search_lower = search.lower()
        filtered = [a for a in filtered if 
                   search_lower in a["entity_name"].lower() or 
                   search_lower in a["user"].lower() or
                   (a.get("details") and search_lower in a["details"].lower())]
    
    # Sort by timestamp descending
    filtered.sort(key=lambda x: x["timestamp"], reverse=True)
    
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    
    return {
        "status": "success",
        "data": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/stats")
async def get_activity_stats(days: int = Query(7, ge=1, le=90)):
    """Get activity statistics"""
    _init_demo_activities()
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = [a for a in _activities if datetime.fromisoformat(a["timestamp"]) > cutoff]
    
    by_type = {}
    by_entity = {}
    by_user = {}
    
    for a in recent:
        by_type[a["type"]] = by_type.get(a["type"], 0) + 1
        by_entity[a["entity"]] = by_entity.get(a["entity"], 0) + 1
        by_user[a["user"]] = by_user.get(a["user"], 0) + 1
    
    return {
        "status": "success",
        "data": {
            "total": len(recent),
            "period_days": days,
            "by_type": by_type,
            "by_entity": by_entity,
            "by_user": by_user,
            "creates": by_type.get("create", 0),
            "updates": by_type.get("update", 0),
            "deletes": by_type.get("delete", 0),
            "imports": by_type.get("import", 0),
            "exports": by_type.get("export", 0),
        }
    }


@router.get("/users")
async def get_active_users():
    """Get list of users with recent activity"""
    _init_demo_activities()
    
    users = {}
    for a in _activities:
        user_id = a["user_id"]
        if user_id not in users:
            users[user_id] = {
                "user_id": user_id,
                "user_name": a["user"],
                "activity_count": 0,
                "last_activity": a["timestamp"]
            }
        users[user_id]["activity_count"] += 1
    
    return {
        "status": "success",
        "data": list(users.values()),
        "count": len(users)
    }


@router.get("/entities")
async def get_entity_types():
    """Get list of entity types with activity counts"""
    _init_demo_activities()
    
    entities = {}
    for a in _activities:
        entity = a["entity"]
        if entity not in entities:
            entities[entity] = {"entity": entity, "count": 0}
        entities[entity]["count"] += 1
    
    return {
        "status": "success",
        "data": list(entities.values()),
        "count": len(entities)
    }


@router.post("")
async def log_activity(
    type: str,
    entity: str,
    entity_id: str,
    entity_name: str,
    user: str = "System",
    user_id: str = "system",
    details: Optional[str] = None
):
    """Log a new activity (internal use)"""
    _init_demo_activities()
    
    new_activity = {
        "id": f"act{str(uuid.uuid4())[:8]}",
        "type": type,
        "entity": entity,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "user": user,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details
    }
    
    _activities.insert(0, new_activity)
    
    return {"status": "success", "data": new_activity}
