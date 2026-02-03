"""
Field Scanner API
Endpoints for field scanning operations and scan result management
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.field_scanner import field_scanner_service


router = APIRouter(prefix="/field-scanner", tags=["Field Scanner"])


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
    results: list[ScanResult] = []
    thumbnail: Optional[str] = None
    notes: Optional[str] = ""
    weather: Optional[WeatherData] = None


class UpdateScanRequest(BaseModel):
    plot_id: Optional[str] = None
    notes: Optional[str] = None
    results: Optional[list[ScanResult]] = None


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
):
    """Get scan results with optional filters."""
    return field_scanner_service.get_scans(
        study_id=study_id,
        plot_id=plot_id,
        crop=crop,
        has_issues=has_issues,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/stats")
async def get_scan_stats(
    study_id: Optional[str] = Query(None, description="Filter by study ID"),
):
    """Get scanning statistics."""
    return field_scanner_service.get_stats(study_id=study_id)


@router.get("/export")
async def export_scans(
    study_id: Optional[str] = Query(None, description="Filter by study ID"),
    format: str = Query("json", description="Export format: json or csv"),
):
    """Export scan data."""
    return field_scanner_service.export_scans(study_id=study_id, format=format)


@router.get("/plot/{plot_id}/history")
async def get_plot_history(plot_id: str):
    """Get scan history for a specific plot."""
    history = field_scanner_service.get_plot_history(plot_id)
    return {"plot_id": plot_id, "scans": history, "total": len(history)}


@router.get("/{scan_id}")
async def get_scan(scan_id: str):
    """Get a single scan by ID."""
    scan = field_scanner_service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.post("")
async def create_scan(request: CreateScanRequest):
    """Create a new scan result."""
    data = request.model_dump()
    if data.get("location"):
        data["location"] = {"lat": data["location"]["lat"], "lng": data["location"]["lng"]}
    if data.get("weather"):
        data["weather"] = {
            "temp": data["weather"].get("temp"),
            "humidity": data["weather"].get("humidity"),
            "conditions": data["weather"].get("conditions"),
        }
    data["results"] = [r.model_dump() for r in request.results] if request.results else []
    
    scan = field_scanner_service.create_scan(data)
    return scan


@router.patch("/{scan_id}")
async def update_scan(scan_id: str, request: UpdateScanRequest):
    """Update an existing scan."""
    data = {}
    if request.plot_id is not None:
        data["plot_id"] = request.plot_id
    if request.notes is not None:
        data["notes"] = request.notes
    if request.results is not None:
        data["results"] = [r.model_dump() for r in request.results]
    
    scan = field_scanner_service.update_scan(scan_id, data)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.delete("/{scan_id}")
async def delete_scan(scan_id: str):
    """Delete a scan."""
    success = field_scanner_service.delete_scan(scan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"success": True, "message": "Scan deleted"}
