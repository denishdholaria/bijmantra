"""
Crop Health API
Monitor crop health status across trials and locations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import uuid

from app.core.database import get_db
from app.models.data_management import (
    TrialHealth, HealthAlert,
    DiseaseRiskLevel, AlertType, AlertSeverity
)

router = APIRouter(prefix="/crop-health", tags=["Crop Health"])


# ============ Schemas ============

class TrialHealthResponse(BaseModel):
    id: str
    name: str
    location: str
    crop: str
    health_score: float = Field(..., ge=0, le=100)
    disease_risk: str  # low, medium, high
    stress_level: float = Field(..., ge=0, le=100)
    last_scan: str
    issues: List[str] = []
    plots_scanned: int
    total_plots: int


class HealthAlertResponse(BaseModel):
    id: str
    type: str  # disease, stress, pest, weather
    severity: str  # low, medium, high, critical
    message: str
    location: str
    timestamp: str
    acknowledged: bool = False
    trial_id: Optional[str] = None


class AlertAcknowledge(BaseModel):
    acknowledged: bool = True
    notes: Optional[str] = None


class HealthScan(BaseModel):
    trial_id: str
    plots_scanned: int
    health_score: float
    issues_found: List[str] = []
    notes: Optional[str] = None


def format_time_ago(dt: datetime) -> str:
    """Format datetime as 'X hours/days ago'"""
    if not dt:
        return "Never"
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    
    return "Just now"


# ============ Trial Health Endpoints ============

@router.get("/trials", summary="List trial health status")
async def list_trial_health(
    location: Optional[str] = Query(None, description="Filter by location"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    risk_level: Optional[str] = Query(None, description="Filter by disease risk level"),
    db: AsyncSession = Depends(get_db)
):
    """Get health status for all trials"""
    query = select(TrialHealth)
    
    if location and location != "all":
        query = query.where(TrialHealth.location.ilike(f"%{location}%"))
    if crop and crop != "all":
        query = query.where(TrialHealth.crop.ilike(crop))
    if risk_level and risk_level != "all":
        try:
            risk = DiseaseRiskLevel(risk_level)
            query = query.where(TrialHealth.disease_risk == risk)
        except ValueError:
            pass
    
    result = await db.execute(query.order_by(TrialHealth.created_at.desc()))
    trials = result.scalars().all()
    
    data = []
    for t in trials:
        data.append({
            "id": str(t.id),
            "name": t.trial_name,
            "location": t.location or "",
            "crop": t.crop or "",
            "health_score": t.health_score or 100.0,
            "disease_risk": t.disease_risk.value if t.disease_risk else "low",
            "stress_level": t.stress_level or 0.0,
            "last_scan": format_time_ago(t.last_scan_at),
            "issues": t.issues or [],
            "plots_scanned": t.plots_scanned or 0,
            "total_plots": t.total_plots or 0,
        })
    
    return {
        "status": "success",
        "data": data,
        "count": len(data),
    }


@router.get("/trials/{trial_id}", summary="Get trial health details")
async def get_trial_health(trial_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed health status for a specific trial"""
    try:
        trial_uuid = uuid.UUID(trial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trial ID format")
    
    result = await db.execute(
        select(TrialHealth).where(TrialHealth.id == trial_uuid)
    )
    trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")
    
    data = {
        "id": str(trial.id),
        "name": trial.trial_name,
        "location": trial.location or "",
        "crop": trial.crop or "",
        "health_score": trial.health_score or 100.0,
        "disease_risk": trial.disease_risk.value if trial.disease_risk else "low",
        "stress_level": trial.stress_level or 0.0,
        "last_scan": format_time_ago(trial.last_scan_at),
        "issues": trial.issues or [],
        "plots_scanned": trial.plots_scanned or 0,
        "total_plots": trial.total_plots or 0,
    }
    
    return {"status": "success", "data": data}


@router.post("/trials/{trial_id}/scan", summary="Record health scan")
async def record_health_scan(trial_id: str, data: HealthScan, db: AsyncSession = Depends(get_db)):
    """Record a new health scan for a trial"""
    try:
        trial_uuid = uuid.UUID(trial_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trial ID format")
    
    result = await db.execute(
        select(TrialHealth).where(TrialHealth.id == trial_uuid)
    )
    trial = result.scalar_one_or_none()
    
    if not trial:
        raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")
    
    # Update trial health data
    trial.health_score = data.health_score
    trial.plots_scanned = data.plots_scanned
    trial.issues = data.issues_found
    trial.last_scan_at = datetime.now(timezone.utc)
    
    # Update disease risk based on health score
    if data.health_score >= 80:
        trial.disease_risk = DiseaseRiskLevel.LOW
    elif data.health_score >= 60:
        trial.disease_risk = DiseaseRiskLevel.MEDIUM
    else:
        trial.disease_risk = DiseaseRiskLevel.HIGH
    
    # Create alert if issues found
    if data.issues_found:
        alert_type = AlertType.DISEASE if any(
            "disease" in i.lower() or "rust" in i.lower() or "blight" in i.lower() 
            for i in data.issues_found
        ) else AlertType.STRESS
        
        severity = AlertSeverity.HIGH if data.health_score < 60 else AlertSeverity.MEDIUM
        
        alert = HealthAlert(
            id=uuid.uuid4(),
            organization_id=trial.organization_id,
            trial_health_id=trial.id,
            alert_type=alert_type,
            severity=severity,
            message=f"Issues detected in {trial.trial_name}: {', '.join(data.issues_found)}",
            location=trial.location,
            acknowledged=False,
        )
        db.add(alert)
    
    await db.commit()
    await db.refresh(trial)
    
    response_data = {
        "id": str(trial.id),
        "name": trial.trial_name,
        "health_score": trial.health_score,
        "disease_risk": trial.disease_risk.value if trial.disease_risk else "low",
        "issues": trial.issues or [],
    }
    
    return {"status": "success", "data": response_data, "message": "Health scan recorded"}


# ============ Alert Endpoints ============

@router.get("/alerts", summary="List health alerts")
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    alert_type: Optional[str] = Query(None, description="Filter by type"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    location: Optional[str] = Query(None, description="Filter by location"),
    db: AsyncSession = Depends(get_db)
):
    """Get all health alerts"""
    query = select(HealthAlert)
    
    if severity:
        try:
            sev = AlertSeverity(severity)
            query = query.where(HealthAlert.severity == sev)
        except ValueError:
            pass
    if alert_type:
        try:
            at = AlertType(alert_type)
            query = query.where(HealthAlert.alert_type == at)
        except ValueError:
            pass
    if acknowledged is not None:
        query = query.where(HealthAlert.acknowledged == acknowledged)
    if location:
        query = query.where(HealthAlert.location.ilike(f"%{location}%"))
    
    result = await db.execute(query.order_by(HealthAlert.created_at.desc()))
    alerts = result.scalars().all()
    
    data = []
    for a in alerts:
        data.append({
            "id": str(a.id),
            "type": a.alert_type.value if a.alert_type else "disease",
            "severity": a.severity.value if a.severity else "medium",
            "message": a.message,
            "location": a.location or "",
            "timestamp": a.created_at.isoformat() if a.created_at else "",
            "acknowledged": a.acknowledged or False,
            "trial_id": str(a.trial_health_id) if a.trial_health_id else None,
        })
    
    unacknowledged = len([a for a in alerts if not a.acknowledged])
    
    return {
        "status": "success",
        "data": data,
        "count": len(data),
        "unacknowledged": unacknowledged,
    }


@router.get("/alerts/{alert_id}", summary="Get alert details")
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Get details for a specific alert"""
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID format")
    
    result = await db.execute(
        select(HealthAlert).where(HealthAlert.id == alert_uuid)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    data = {
        "id": str(alert.id),
        "type": alert.alert_type.value if alert.alert_type else "disease",
        "severity": alert.severity.value if alert.severity else "medium",
        "message": alert.message,
        "location": alert.location or "",
        "timestamp": alert.created_at.isoformat() if alert.created_at else "",
        "acknowledged": alert.acknowledged or False,
        "trial_id": str(alert.trial_health_id) if alert.trial_health_id else None,
        "notes": alert.notes,
    }
    
    return {"status": "success", "data": data}


@router.patch("/alerts/{alert_id}/acknowledge", summary="Acknowledge alert")
async def acknowledge_alert(alert_id: str, data: AlertAcknowledge, db: AsyncSession = Depends(get_db)):
    """Acknowledge or unacknowledge an alert"""
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID format")
    
    result = await db.execute(
        select(HealthAlert).where(HealthAlert.id == alert_uuid)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    alert.acknowledged = data.acknowledged
    if data.acknowledged:
        alert.acknowledged_at = datetime.now(timezone.utc)
    if data.notes:
        alert.notes = data.notes
    
    await db.commit()
    await db.refresh(alert)
    
    response_data = {
        "id": str(alert.id),
        "acknowledged": alert.acknowledged,
        "message": alert.message,
    }
    
    return {"status": "success", "data": response_data, "message": "Alert updated"}


# ============ Statistics Endpoints ============

@router.get("/summary", summary="Get health summary")
async def get_health_summary(db: AsyncSession = Depends(get_db)):
    """Get overall crop health summary statistics"""
    trials_result = await db.execute(select(TrialHealth))
    trials = trials_result.scalars().all()
    
    alerts_result = await db.execute(select(HealthAlert))
    alerts = alerts_result.scalars().all()
    
    if not trials:
        return {
            "status": "success",
            "data": {
                "avg_health_score": 0,
                "total_trials": 0,
                "high_risk_trials": 0,
                "active_alerts": 0,
                "by_crop": {},
                "by_location": {},
            }
        }
    
    avg_health = sum(t.health_score or 0 for t in trials) / len(trials)
    high_risk = len([t for t in trials if t.disease_risk == DiseaseRiskLevel.HIGH])
    active_alerts = len([a for a in alerts if not a.acknowledged])
    
    # Group by crop
    by_crop = {}
    for t in trials:
        crop = t.crop or "Unknown"
        if crop not in by_crop:
            by_crop[crop] = {"count": 0, "avg_health": 0, "total_health": 0}
        by_crop[crop]["count"] += 1
        by_crop[crop]["total_health"] += t.health_score or 0
    for crop in by_crop:
        by_crop[crop]["avg_health"] = round(by_crop[crop]["total_health"] / by_crop[crop]["count"], 1)
        del by_crop[crop]["total_health"]
    
    # Group by location
    by_location = {}
    for t in trials:
        loc = t.location or "Unknown"
        if loc not in by_location:
            by_location[loc] = {"count": 0, "avg_health": 0, "total_health": 0}
        by_location[loc]["count"] += 1
        by_location[loc]["total_health"] += t.health_score or 0
    for loc in by_location:
        by_location[loc]["avg_health"] = round(by_location[loc]["total_health"] / by_location[loc]["count"], 1)
        del by_location[loc]["total_health"]
    
    return {
        "status": "success",
        "data": {
            "avg_health_score": round(avg_health, 1),
            "total_trials": len(trials),
            "high_risk_trials": high_risk,
            "active_alerts": active_alerts,
            "by_crop": by_crop,
            "by_location": by_location,
        }
    }


@router.get("/trends", summary="Get health trends")
async def get_health_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days for trend data"),
    db: AsyncSession = Depends(get_db)
):
    """Get health score trends over time"""
    # Generate simulated trend data (in production, this would query historical data)
    trends = []
    base_score = 82
    for i in range(days):
        date = (datetime.now(timezone.utc) - timedelta(days=days - i - 1)).strftime("%Y-%m-%d")
        variation = (i % 5) - 2
        trends.append({
            "date": date,
            "avg_health_score": base_score + variation,
            "scans_completed": 5 + (i % 3),
            "alerts_generated": 1 if i % 3 == 0 else 0,
        })
    
    return {
        "status": "success",
        "data": trends,
        "period_days": days,
    }


@router.get("/locations", summary="List locations")
async def list_locations(db: AsyncSession = Depends(get_db)):
    """Get list of all locations with trials"""
    result = await db.execute(
        select(TrialHealth.location).distinct().where(TrialHealth.location.isnot(None))
    )
    locations = [row[0] for row in result.all() if row[0]]
    
    return {
        "status": "success",
        "data": sorted(locations),
        "count": len(locations),
    }


@router.get("/crops", summary="List crops")
async def list_crops(db: AsyncSession = Depends(get_db)):
    """Get list of all crops being monitored"""
    result = await db.execute(
        select(TrialHealth.crop).distinct().where(TrialHealth.crop.isnot(None))
    )
    crops = [row[0] for row in result.all() if row[0]]
    
    return {
        "status": "success",
        "data": sorted(crops),
        "count": len(crops),
    }
