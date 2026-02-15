"""
Field Scanner API
Endpoints for field scanning operations and scan result management

Endpoints:
- GET /field-scanner - List scans with filters
- GET /field-scanner/stats - Scan statistics
- GET /field-scanner/export - Export scan data
- GET /field-scanner/plot/{plot_id}/history - Plot scan history
- GET /field-scanner/{scan_id} - Get single scan
- POST /field-scanner - Create new scan
- PATCH /field-scanner/{scan_id} - Update scan
- DELETE /field-scanner/{scan_id} - Delete scan

Refactored: Session 94 — migrated from in-memory singleton to real DB queries.
"""

from typing import Optional, List as TypingList
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.api.deps import get_current_user, get_organization_id
from app.models.core import User
from app.models.field_scanner import FieldScan

router = APIRouter(prefix="/field-scanner", tags=["Field Scanner"])


# ============================================================================
# Schemas
# ============================================================================

class ScanResult(BaseModel):
    type: str
    label: str
    confidence: float
    value: Optional[float] = None
    unit: Optional[str] = None
    severity: Optional[str] = None
    affected_area: Optional[float] = None
    stage_code: Optional[str] = None


class LocationData(BaseModel):
    lat: float
    lng: float


class WeatherData(BaseModel):
    temp: Optional[float] = None
    humidity: Optional[float] = None
    conditions: Optional[str] = None


class CreateScanRequest(BaseModel):
    plot_id: Optional[str] = None
    study_id: Optional[str] = None
    crop: Optional[str] = "rice"
    location: Optional[LocationData] = None
    results: TypingList[ScanResult] = []
    thumbnail: Optional[str] = None
    notes: Optional[str] = ""
    weather: Optional[WeatherData] = None


class UpdateScanRequest(BaseModel):
    plot_id: Optional[str] = None
    notes: Optional[str] = None
    results: Optional[TypingList[ScanResult]] = None


# ============================================================================
# Helpers
# ============================================================================

def _to_response(scan: FieldScan) -> dict:
    return {
        "id": scan.id,
        "plot_id": scan.plot_id,
        "study_id": scan.study_id,
        "timestamp": scan.created_at.isoformat() if scan.created_at else "",
        "location": {"lat": scan.latitude, "lng": scan.longitude}
        if scan.latitude is not None and scan.longitude is not None
        else None,
        "crop": scan.crop,
        "results": scan.results or [],
        "thumbnail": scan.thumbnail_url,
        "notes": scan.notes or "",
        "weather": scan.weather,
        "created_by": scan.created_by,
        "created_at": scan.created_at.isoformat() if scan.created_at else "",
        "updated_at": scan.updated_at.isoformat() if scan.updated_at else "",
    }


def _has_issues(results: list) -> bool:
    """Check if scan results contain disease or stress detections"""
    return any(
        r.get("type") in ("disease", "stress") and r.get("confidence", 0) > 0.5
        for r in (results or [])
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("")
async def get_scans(
    study_id: Optional[str] = Query(None, description="Filter by study ID"),
    plot_id: Optional[str] = Query(None, description="Filter by plot ID"),
    crop: Optional[str] = Query(None, description="Filter by crop type"),
    has_issues: Optional[bool] = Query(None, description="Filter by issue presence"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get scan results with optional filters."""
    query = select(FieldScan).where(FieldScan.organization_id == organization_id)

    if study_id:
        query = query.where(FieldScan.study_id == study_id)
    if plot_id:
        query = query.where(FieldScan.plot_id == plot_id)
    if crop:
        query = query.where(func.lower(FieldScan.crop) == crop.lower())
    if start_date:
        query = query.where(FieldScan.created_at >= start_date)
    if end_date:
        query = query.where(FieldScan.created_at <= end_date)

    # Count total before pagination
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(desc(FieldScan.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    scans = result.scalars().all()

    # Post-filter has_issues (JSON field, can't do in SQL easily)
    scan_list = [_to_response(s) for s in scans]
    if has_issues is not None:
        scan_list = [s for s in scan_list if _has_issues(s["results"]) == has_issues]

    return {
        "scans": scan_list,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_scan_stats(
    study_id: Optional[str] = Query(None, description="Filter by study ID"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get scanning statistics."""
    query = select(FieldScan).where(FieldScan.organization_id == organization_id)
    if study_id:
        query = query.where(FieldScan.study_id == study_id)

    result = await db.execute(query)
    scans = result.scalars().all()

    total_scans = len(scans)
    plots_scanned = len(set(s.plot_id for s in scans if s.plot_id))

    issues_found = sum(1 for s in scans if _has_issues(s.results))
    healthy_plots = total_scans - issues_found

    diseases: dict = {}
    stresses: dict = {}
    crops: dict = {}

    for scan in scans:
        # Crop breakdown
        c = scan.crop or "unknown"
        crops[c] = crops.get(c, 0) + 1

        for r in (scan.results or []):
            conf = r.get("confidence", 0)
            if conf <= 0.5:
                continue
            label = r.get("label", "Unknown")
            if r.get("type") == "disease":
                diseases[label] = diseases.get(label, 0) + 1
            elif r.get("type") == "stress":
                stresses[label] = stresses.get(label, 0) + 1

    last_scan = None
    if scans:
        latest = max(scans, key=lambda s: s.created_at or datetime.min.replace(tzinfo=timezone.utc))
        last_scan = latest.created_at.isoformat() if latest.created_at else None

    return {
        "total_scans": total_scans,
        "plots_scanned": plots_scanned,
        "healthy_plots": healthy_plots,
        "issues_found": issues_found,
        "diseases": diseases,
        "stresses": stresses,
        "crops": crops,
        "last_scan": last_scan,
    }


@router.get("/export")
async def export_scans(
    study_id: Optional[str] = Query(None, description="Filter by study ID"),
    format: str = Query("json", description="Export format: json or csv"),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Export scan data."""
    query = select(FieldScan).where(FieldScan.organization_id == organization_id)
    if study_id:
        query = query.where(FieldScan.study_id == study_id)
    query = query.order_by(desc(FieldScan.created_at)).limit(10000)

    result = await db.execute(query)
    scans = result.scalars().all()
    scan_list = [_to_response(s) for s in scans]

    if format == "csv":
        rows = []
        for scan in scan_list:
            base = {
                "scan_id": scan["id"],
                "plot_id": scan["plot_id"],
                "timestamp": scan["timestamp"],
                "crop": scan.get("crop", ""),
                "lat": scan["location"]["lat"] if scan.get("location") else None,
                "lng": scan["location"]["lng"] if scan.get("location") else None,
                "notes": scan.get("notes", ""),
            }
            for i, r in enumerate(scan.get("results", [])[:5]):
                base[f"result_{i+1}_type"] = r.get("type", "")
                base[f"result_{i+1}_label"] = r.get("label", "")
                base[f"result_{i+1}_confidence"] = r.get("confidence", 0)
            rows.append(base)
        return {"format": "csv", "data": rows, "count": len(rows)}

    return {"format": "json", "data": scan_list, "count": len(scan_list)}


@router.get("/plot/{plot_id}/history")
async def get_plot_history(
    plot_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get scan history for a specific plot."""
    result = await db.execute(
        select(FieldScan)
        .where(FieldScan.organization_id == organization_id, FieldScan.plot_id == plot_id)
        .order_by(desc(FieldScan.created_at))
    )
    scans = result.scalars().all()
    return {"plot_id": plot_id, "scans": [_to_response(s) for s in scans], "total": len(scans)}


@router.get("/{scan_id}")
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get a single scan by ID."""
    result = await db.execute(
        select(FieldScan).where(
            FieldScan.id == scan_id,
            FieldScan.organization_id == organization_id,
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _to_response(scan)


@router.post("")
async def create_scan(
    request: CreateScanRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_user),
):
    """Create a new scan result."""
    scan = FieldScan(
        organization_id=organization_id,
        plot_id=request.plot_id,
        study_id=request.study_id,
        crop=request.crop,
        latitude=request.location.lat if request.location else None,
        longitude=request.location.lng if request.location else None,
        results=[r.model_dump() for r in request.results] if request.results else [],
        thumbnail_url=request.thumbnail,
        notes=request.notes or "",
        weather=request.weather.model_dump() if request.weather else None,
        created_by=current_user.email if hasattr(current_user, "email") else str(current_user.id),
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return _to_response(scan)


@router.patch("/{scan_id}")
async def update_scan(
    scan_id: int,
    request: UpdateScanRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Update an existing scan."""
    result = await db.execute(
        select(FieldScan).where(
            FieldScan.id == scan_id,
            FieldScan.organization_id == organization_id,
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if request.plot_id is not None:
        scan.plot_id = request.plot_id
    if request.notes is not None:
        scan.notes = request.notes
    if request.results is not None:
        scan.results = [r.model_dump() for r in request.results]

    await db.commit()
    await db.refresh(scan)
    return _to_response(scan)


@router.delete("/{scan_id}")
async def delete_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Delete a scan."""
    result = await db.execute(
        select(FieldScan).where(
            FieldScan.id == scan_id,
            FieldScan.organization_id == organization_id,
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    await db.delete(scan)
    await db.commit()
    return {"success": True, "message": "Scan deleted", "id": scan_id}
