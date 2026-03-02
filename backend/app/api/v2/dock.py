"""
Dock Preferences API
Endpoints for Mahasarthi navigation dock persistence

Production-ready: All data stored in database, enables cross-device sync.

@see docs/gupt/1-MAHASARTHI.md for full specification
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.models.user_management import ActivityLog, UserDockPreference, UserRole


router = APIRouter(prefix="/dock", tags=["Dock"], dependencies=[Depends(get_current_user)])


# ============================================================================
# Request/Response Models
# ============================================================================

class DockItem(BaseModel):
    """Single dock item (pinned or recent page)"""
    id: str = Field(..., description="Unique identifier for the item")
    path: str = Field(..., description="Route path (e.g., /programs)")
    label: str = Field(..., description="Display label")
    icon: str = Field(..., description="Lucide icon name")
    isPinned: bool = Field(default=False, description="Whether item is pinned")
    lastVisited: str | None = Field(None, description="ISO timestamp of last visit")
    visitCount: int | None = Field(None, description="Number of visits")


class DockPreferences(BaseModel):
    """Dock display preferences"""
    maxPinned: int = Field(default=8, ge=1, le=12, description="Maximum pinned items")
    maxRecent: int = Field(default=4, ge=1, le=10, description="Maximum recent items")
    showLabels: bool = Field(default=False, description="Show labels on dock icons")
    compactMode: bool = Field(default=False, description="Use compact dock layout")


class DockStateResponse(BaseModel):
    """Full dock state response"""
    userId: int
    pinnedItems: list[DockItem]
    recentItems: list[DockItem]
    preferences: DockPreferences
    updatedAt: str


class UpdateDockRequest(BaseModel):
    """Request to update dock state"""
    pinnedItems: list[DockItem] | None = None
    recentItems: list[DockItem] | None = None
    preferences: DockPreferences | None = None


class PinItemRequest(BaseModel):
    """Request to pin a single item"""
    id: str
    path: str
    label: str
    icon: str


class RecordVisitRequest(BaseModel):
    """Request to record a page visit"""
    id: str
    path: str
    label: str
    icon: str


# ============================================================================
# Default Docks by Role
# ============================================================================

DEFAULT_DOCKS = {
    "breeder": [
        {"id": "dashboard", "path": "/dashboard", "label": "Dashboard", "icon": "LayoutDashboard"},
        {"id": "programs", "path": "/programs", "label": "Programs", "icon": "Wheat"},
        {"id": "trials", "path": "/trials", "label": "Trials", "icon": "FlaskConical"},
        {"id": "germplasm", "path": "/germplasm", "label": "Germplasm", "icon": "Sprout"},
        {"id": "crosses", "path": "/crosses", "label": "Crosses", "icon": "GitMerge"},
        {"id": "statistics", "path": "/statistics", "label": "Statistics", "icon": "BarChart3"},
        {"id": "breeding-values", "path": "/breeding-values", "label": "Breeding Values", "icon": "Dna"},
        {"id": "settings", "path": "/settings", "label": "Settings", "icon": "Settings"},
    ],
    "seed_company": [
        {"id": "dashboard", "path": "/dashboard", "label": "Dashboard", "icon": "LayoutDashboard"},
        {"id": "lab-samples", "path": "/seed-operations/samples", "label": "Lab Samples", "icon": "TestTube2"},
        {"id": "quality-gate", "path": "/seed-operations/quality-gate", "label": "Quality Gate", "icon": "Shield"},
        {"id": "seed-lots", "path": "/seed-operations/lots", "label": "Seed Lots", "icon": "Package"},
        {"id": "dispatch", "path": "/seed-operations/dispatch", "label": "Dispatch", "icon": "Truck"},
        {"id": "certificates", "path": "/seed-operations/certificates", "label": "Certificates", "icon": "FileCheck"},
        {"id": "reports", "path": "/reports", "label": "Reports", "icon": "FileText"},
        {"id": "settings", "path": "/settings", "label": "Settings", "icon": "Settings"},
    ],
    "genebank_curator": [
        {"id": "dashboard", "path": "/dashboard", "label": "Dashboard", "icon": "LayoutDashboard"},
        {"id": "vault", "path": "/seed-bank/vault", "label": "Vault Management", "icon": "Building2"},
        {"id": "accessions", "path": "/seed-bank/accessions", "label": "Accessions", "icon": "Package"},
        {"id": "viability", "path": "/seed-bank/viability", "label": "Viability Testing", "icon": "TestTube2"},
        {"id": "regeneration", "path": "/seed-bank/regeneration", "label": "Regeneration", "icon": "RefreshCw"},
        {"id": "grin-search", "path": "/seed-bank/grin-search", "label": "GRIN Search", "icon": "Globe"},
        {"id": "conservation", "path": "/seed-bank/conservation", "label": "Conservation", "icon": "Shield"},
        {"id": "settings", "path": "/settings", "label": "Settings", "icon": "Settings"},
    ],
    "researcher": [
        {"id": "dashboard", "path": "/dashboard", "label": "Dashboard", "icon": "LayoutDashboard"},
        {"id": "genomic-selection", "path": "/genomic-selection", "label": "Genomic Selection", "icon": "Dna"},
        {"id": "wasm-genomics", "path": "/wasm-genomics", "label": "WASM Analytics", "icon": "Cpu"},
        {"id": "qtl-mapping", "path": "/qtl-mapping", "label": "QTL Mapping", "icon": "Target"},
        {"id": "gxe", "path": "/gxe-interaction", "label": "G×E Analysis", "icon": "Globe"},
        {"id": "space-research", "path": "/space-research", "label": "Space Research", "icon": "Rocket"},
        {"id": "publications", "path": "/publications", "label": "Publications", "icon": "BookOpen"},
        {"id": "settings", "path": "/settings", "label": "Settings", "icon": "Settings"},
    ],
    "default": [
        {"id": "dashboard", "path": "/dashboard", "label": "Dashboard", "icon": "LayoutDashboard"},
        {"id": "programs", "path": "/programs", "label": "Programs", "icon": "Wheat"},
        {"id": "trials", "path": "/trials", "label": "Trials", "icon": "FlaskConical"},
        {"id": "germplasm", "path": "/germplasm", "label": "Germplasm", "icon": "Sprout"},
        {"id": "settings", "path": "/settings", "label": "Settings", "icon": "Settings"},
    ],
}


def get_default_dock(role: str) -> list[dict]:
    """Get default dock items for a role"""
    return DEFAULT_DOCKS.get(role, DEFAULT_DOCKS["default"])


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=dict)
async def get_dock_state(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's dock state (pinned items, recent items, preferences).

    Returns default dock based on user role if no preferences saved.
    """
    user_id = current_user.id

    # Get user to determine role
    # Eagerly load roles to determine defaults if needed
    user_result = await db.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get dock preferences
    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if not dock_prefs:
        # Return defaults based on user role
        role = "default"

        # Check user roles for a match in DEFAULT_DOCKS
        if user.user_roles:
            for ur in user.user_roles:
                if ur.role and ur.role.role_id in DEFAULT_DOCKS:
                    role = ur.role.role_id
                    break

        default_items = get_default_dock(role)

        return {
            "status": "success",
            "data": DockStateResponse(
                userId=user_id,
                pinnedItems=[
                    DockItem(id=item["id"], path=item["path"], label=item["label"],
                            icon=item["icon"], isPinned=True)
                    for item in default_items
                ],
                recentItems=[],
                preferences=DockPreferences(),
                updatedAt=datetime.now(UTC).isoformat()
            ).model_dump()
        }

    return {
        "status": "success",
        "data": DockStateResponse(
            userId=dock_prefs.user_id,
            pinnedItems=[DockItem(**item) for item in (dock_prefs.pinned_items or [])],
            recentItems=[DockItem(**item) for item in (dock_prefs.recent_items or [])],
            preferences=DockPreferences(
                maxPinned=dock_prefs.max_pinned,
                maxRecent=dock_prefs.max_recent,
                showLabels=dock_prefs.show_labels,
                compactMode=dock_prefs.compact_mode
            ),
            updatedAt=dock_prefs.updated_at.isoformat()
        ).model_dump()
    }


@router.put("", response_model=dict)
async def update_dock_state(
    data: UpdateDockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user's dock state (full replacement).

    Used for syncing entire dock state from frontend.
    """
    user_id = current_user.id
    organization_id = current_user.organization_id

    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if not dock_prefs:
        dock_prefs = UserDockPreference(
            organization_id=organization_id,
            user_id=user_id,
            pinned_items=[],
            recent_items=[]
        )
        db.add(dock_prefs)

    # Update fields if provided
    if data.pinnedItems is not None:
        dock_prefs.pinned_items = [item.model_dump() for item in data.pinnedItems]

    if data.recentItems is not None:
        dock_prefs.recent_items = [item.model_dump() for item in data.recentItems]

    if data.preferences is not None:
        dock_prefs.max_pinned = data.preferences.maxPinned
        dock_prefs.max_recent = data.preferences.maxRecent
        dock_prefs.show_labels = data.preferences.showLabels
        dock_prefs.compact_mode = data.preferences.compactMode

    await db.commit()
    await db.refresh(dock_prefs)

    return {
        "status": "success",
        "message": "Dock state updated",
        "data": {
            "updatedAt": dock_prefs.updated_at.isoformat()
        }
    }


@router.post("/pin", response_model=dict)
async def pin_item(
    data: PinItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pin a page to the dock.

    Adds item to pinned list and removes from recent if present.
    """
    user_id = current_user.id
    organization_id = current_user.organization_id

    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if not dock_prefs:
        dock_prefs = UserDockPreference(
            organization_id=organization_id,
            user_id=user_id,
            pinned_items=[],
            recent_items=[]
        )
        db.add(dock_prefs)

    pinned = dock_prefs.pinned_items or []
    recent = dock_prefs.recent_items or []

    # Check if already pinned
    if any(item.get("path") == data.path for item in pinned):
        return {"status": "success", "message": "Item already pinned"}

    # Check max limit
    if len(pinned) >= dock_prefs.max_pinned:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum pinned items ({dock_prefs.max_pinned}) reached"
        )

    # Add to pinned
    new_item = {
        "id": data.id,
        "path": data.path,
        "label": data.label,
        "icon": data.icon,
        "isPinned": True
    }
    pinned.append(new_item)
    dock_prefs.pinned_items = pinned

    # Remove from recent if present
    dock_prefs.recent_items = [r for r in recent if r.get("path") != data.path]

    await db.commit()

    return {"status": "success", "message": "Item pinned"}


@router.delete("/pin", response_model=dict)
async def unpin_item(
    path: str = Query(..., description="Path of item to unpin"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unpin a page from the dock.
    """
    user_id = current_user.id

    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if not dock_prefs:
        return {"status": "success", "message": "No dock preferences found"}

    pinned = dock_prefs.pinned_items or []
    dock_prefs.pinned_items = [p for p in pinned if p.get("path") != path]

    await db.commit()

    return {"status": "success", "message": "Item unpinned"}


@router.post("/reorder", response_model=dict)
async def reorder_pinned(
    from_index: int = Query(..., description="Source index"),
    to_index: int = Query(..., description="Destination index"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reorder pinned items (drag and drop).
    """
    user_id = current_user.id

    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if not dock_prefs:
        raise HTTPException(status_code=404, detail="No dock preferences found")

    pinned = dock_prefs.pinned_items or []

    if from_index < 0 or from_index >= len(pinned):
        raise HTTPException(status_code=400, detail="Invalid from_index")
    if to_index < 0 or to_index >= len(pinned):
        raise HTTPException(status_code=400, detail="Invalid to_index")

    # Reorder
    item = pinned.pop(from_index)
    pinned.insert(to_index, item)
    dock_prefs.pinned_items = pinned

    await db.commit()

    return {"status": "success", "message": "Items reordered"}


@router.post("/visit", response_model=dict)
async def record_visit(
    data: RecordVisitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a page visit (adds to recent items).

    Does not add if page is already pinned.
    """
    user_id = current_user.id
    organization_id = current_user.organization_id

    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if not dock_prefs:
        dock_prefs = UserDockPreference(
            organization_id=organization_id,
            user_id=user_id,
            pinned_items=[],
            recent_items=[]
        )
        db.add(dock_prefs)

    pinned = dock_prefs.pinned_items or []
    recent = dock_prefs.recent_items or []

    # Don't add to recent if pinned
    if any(p.get("path") == data.path for p in pinned):
        return {"status": "success", "message": "Page is pinned, not added to recent"}

    now = datetime.now(UTC).isoformat()

    # Check if already in recent
    existing_idx = next(
        (i for i, r in enumerate(recent) if r.get("path") == data.path),
        None
    )

    if existing_idx is not None:
        # Update existing and move to front
        existing = recent.pop(existing_idx)
        existing["lastVisited"] = now
        existing["visitCount"] = (existing.get("visitCount") or 0) + 1
        recent.insert(0, existing)
    else:
        # Add new
        new_item = {
            "id": data.id,
            "path": data.path,
            "label": data.label,
            "icon": data.icon,
            "isPinned": False,
            "lastVisited": now,
            "visitCount": 1
        }
        recent.insert(0, new_item)

    # Trim to max
    dock_prefs.recent_items = recent[:dock_prefs.max_recent]

    await db.commit()

    return {"status": "success", "message": "Visit recorded"}


@router.delete("/recent", response_model=dict)
async def clear_recent(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear all recent items.
    """
    user_id = current_user.id

    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if dock_prefs:
        dock_prefs.recent_items = []
        await db.commit()

    return {"status": "success", "message": "Recent items cleared"}


@router.patch("/preferences", response_model=dict)
async def update_preferences(
    data: DockPreferences,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update dock display preferences.
    """
    user_id = current_user.id
    organization_id = current_user.organization_id

    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if not dock_prefs:
        dock_prefs = UserDockPreference(
            organization_id=organization_id,
            user_id=user_id,
            pinned_items=[],
            recent_items=[]
        )
        db.add(dock_prefs)

    dock_prefs.max_pinned = data.maxPinned
    dock_prefs.max_recent = data.maxRecent
    dock_prefs.show_labels = data.showLabels
    dock_prefs.compact_mode = data.compactMode

    await db.commit()

    return {"status": "success", "message": "Preferences updated"}


@router.get("/defaults/{role}", response_model=dict)
async def get_default_dock_for_role(role: str):
    """
    Get default dock items for a specific role.

    Useful for resetting dock to defaults or initializing new users.
    """
    if role not in DEFAULT_DOCKS:
        role = "default"

    items = get_default_dock(role)

    return {
        "status": "success",
        "data": {
            "role": role,
            "items": [
                DockItem(id=item["id"], path=item["path"], label=item["label"],
                        icon=item["icon"], isPinned=True).model_dump()
                for item in items
            ]
        }
    }


@router.post("/reset", response_model=dict)
async def reset_dock_to_defaults(
    role: str = Query("default", description="Role for default dock"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset dock to role-based defaults.

    Clears recent items and replaces pinned with defaults.
    """
    user_id = current_user.id
    organization_id = current_user.organization_id

    result = await db.execute(
        select(UserDockPreference).where(UserDockPreference.user_id == user_id)
    )
    dock_prefs = result.scalar_one_or_none()

    if not dock_prefs:
        dock_prefs = UserDockPreference(
            organization_id=organization_id,
            user_id=user_id
        )
        db.add(dock_prefs)

    # Get defaults for role
    default_items = get_default_dock(role)

    dock_prefs.pinned_items = [
        {"id": item["id"], "path": item["path"], "label": item["label"],
         "icon": item["icon"], "isPinned": True}
        for item in default_items
    ]
    dock_prefs.recent_items = []

    await db.commit()

    # Log activity
    activity = ActivityLog(
        organization_id=organization_id,
        user_id=user_id,
        action="reset_dock",
        details=f"Reset dock to {role} defaults"
    )
    db.add(activity)
    await db.commit()

    return {
        "status": "success",
        "message": f"Dock reset to {role} defaults",
        "data": {
            "pinnedCount": len(dock_prefs.pinned_items)
        }
    }
