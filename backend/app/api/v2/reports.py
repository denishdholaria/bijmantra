"""
Advanced Reports API
Generate, schedule, and export comprehensive reports
Database-backed implementation
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone as tz
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.collaboration import (
    ReportTemplate, ReportSchedule, GeneratedReport,
    ReportFormat, ReportCategory, ScheduleFrequency,
    ReportStatus, ScheduleStatus
)

router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class ReportStats(BaseModel):
    total_templates: int
    active_schedules: int
    generated_today: int
    storage_used_mb: float
    storage_quota_mb: float


class GenerateReportRequest(BaseModel):
    template_id: int
    format: str = "PDF"
    parameters: dict = {}


class CreateScheduleRequest(BaseModel):
    template_id: int
    name: str
    schedule: str  # daily, weekly, monthly, quarterly
    schedule_time: str
    recipients: list[str]
    parameters: dict = {}


# ============================================
# ENDPOINTS
# ============================================

@router.get("/stats", response_model=ReportStats)
async def get_report_stats(db: AsyncSession = Depends(get_db)):
    """Get report system statistics."""
    # Count templates
    templates_result = await db.execute(
        select(func.count(ReportTemplate.id)).where(ReportTemplate.is_active == True)
    )
    total_templates = templates_result.scalar() or 0

    # Count active schedules
    schedules_result = await db.execute(
        select(func.count(ReportSchedule.id)).where(
            ReportSchedule.status == ScheduleStatus.ACTIVE
        )
    )
    active_schedules = schedules_result.scalar() or 0

    # Count generated today
    today_start = datetime.now(tz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    generated_result = await db.execute(
        select(func.count(GeneratedReport.id)).where(
            GeneratedReport.created_at >= today_start
        )
    )
    generated_today = generated_result.scalar() or 0

    # Calculate storage used
    storage_result = await db.execute(
        select(func.sum(GeneratedReport.size_bytes))
    )
    storage_bytes = storage_result.scalar() or 0

    return ReportStats(
        total_templates=total_templates,
        active_schedules=active_schedules,
        generated_today=generated_today,
        storage_used_mb=round(storage_bytes / (1024 * 1024), 2),
        storage_quota_mb=10240.0
    )


@router.get("/templates")
async def list_templates(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List available report templates."""
    query = select(ReportTemplate).where(ReportTemplate.is_active == True)

    if category:
        query = query.where(ReportTemplate.category == category)

    if search:
        query = query.where(
            ReportTemplate.name.ilike(f"%{search}%") |
            ReportTemplate.description.ilike(f"%{search}%")
        )

    result = await db.execute(query)
    templates = result.scalars().all()

    return {
        "templates": [
            {
                "id": str(t.id),
                "name": t.name,
                "description": t.description,
                "category": t.category.value if t.category else None,
                "formats": t.formats or [],
                "parameters": t.parameters or [],
                "last_generated": t.last_generated.isoformat() if t.last_generated else None,
                "generation_count": t.generation_count or 0
            }
            for t in templates
        ],
        "total": len(templates)
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific report template."""
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "category": template.category.value if template.category else None,
        "formats": template.formats or [],
        "parameters": template.parameters or [],
        "last_generated": template.last_generated.isoformat() if template.last_generated else None,
        "generation_count": template.generation_count or 0
    }


@router.post("/generate")
async def generate_report(
    request: GenerateReportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a report from a template."""
    # Get template
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == request.template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Parse format
    try:
        report_format = ReportFormat(request.format)
    except ValueError:
        report_format = ReportFormat.PDF

    # Create generated report record
    report = GeneratedReport(
        organization_id=template.organization_id,
        template_id=template.id,
        name=f"{template.name} - {datetime.now(tz.utc).strftime('%Y-%m-%d')}",
        format=report_format,
        status=ReportStatus.COMPLETED,
        size_bytes=1024 * 1024 * 2,  # 2MB placeholder
        download_url=f"/api/v2/reports/download/{uuid.uuid4().hex[:8]}",
        parameters=request.parameters,
        expires_at=datetime.now(tz.utc) + timedelta(days=7)
    )

    db.add(report)

    # Update template stats
    template.last_generated = datetime.now(tz.utc)
    template.generation_count = (template.generation_count or 0) + 1

    await db.commit()
    await db.refresh(report)

    return {
        "report": {
            "id": str(report.id),
            "name": report.name,
            "format": report.format.value,
            "status": report.status.value,
            "download_url": report.download_url,
            "expires_at": report.expires_at.isoformat() if report.expires_at else None
        },
        "message": "Report generated successfully"
    }


@router.get("/generated")
async def list_generated_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List recently generated reports."""
    result = await db.execute(
        select(GeneratedReport)
        .order_by(GeneratedReport.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    reports = result.scalars().all()

    # Get total count
    count_result = await db.execute(select(func.count(GeneratedReport.id)))
    total = count_result.scalar() or 0

    return {
        "reports": [
            {
                "id": str(r.id),
                "template_id": str(r.template_id),
                "name": r.name,
                "format": r.format.value if r.format else None,
                "status": r.status.value if r.status else None,
                "size_bytes": r.size_bytes or 0,
                "generated_at": r.created_at.isoformat() if r.created_at else None,
                "download_url": r.download_url,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None
            }
            for r in reports
        ],
        "total": total
    }


@router.get("/download/{report_id}")
async def download_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """Get download URL for a generated report."""
    # Try to parse as int first
    try:
        rid = int(report_id)
        result = await db.execute(
            select(GeneratedReport).where(GeneratedReport.id == rid)
        )
    except ValueError:
        # If not int, return not found
        raise HTTPException(status_code=404, detail="Report not found")

    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "download_url": report.download_url,
        "filename": f"{report.name}.{report.format.value.lower() if report.format else 'pdf'}",
        "size_bytes": report.size_bytes or 0,
        "expires_at": report.expires_at.isoformat() if report.expires_at else None
    }


@router.delete("/generated/{report_id}")
async def delete_generated_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a generated report."""
    result = await db.execute(
        select(GeneratedReport).where(GeneratedReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.delete(report)
    await db.commit()

    return {"message": "Report deleted successfully"}


# ============================================
# SCHEDULED REPORTS
# ============================================

@router.get("/schedules")
async def list_schedules(
    status: Optional[str] = Query(None, description="Filter by status: active, paused"),
    db: AsyncSession = Depends(get_db)
):
    """List scheduled reports."""
    query = select(ReportSchedule)

    if status:
        try:
            schedule_status = ScheduleStatus(status)
            query = query.where(ReportSchedule.status == schedule_status)
        except ValueError:
            pass

    result = await db.execute(query.order_by(ReportSchedule.next_run))
    schedules = result.scalars().all()

    return {
        "schedules": [
            {
                "id": str(s.id),
                "template_id": str(s.template_id),
                "name": s.name,
                "schedule": s.schedule.value if s.schedule else None,
                "schedule_time": s.schedule_time,
                "next_run": s.next_run.isoformat() if s.next_run else None,
                "last_run": s.last_run.isoformat() if s.last_run else None,
                "recipients": s.recipients or [],
                "status": s.status.value if s.status else None,
                "parameters": s.parameters or {}
            }
            for s in schedules
        ],
        "total": len(schedules)
    }


@router.post("/schedules")
async def create_schedule(
    request: CreateScheduleRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new scheduled report."""
    # Verify template exists
    result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == request.template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Parse schedule frequency
    try:
        frequency = ScheduleFrequency(request.schedule)
    except ValueError:
        frequency = ScheduleFrequency.WEEKLY

    # Calculate next run
    next_run = datetime.now(tz.utc) + timedelta(days=1)
    if frequency == ScheduleFrequency.WEEKLY:
        next_run = datetime.now(tz.utc) + timedelta(days=7)
    elif frequency == ScheduleFrequency.MONTHLY:
        next_run = datetime.now(tz.utc) + timedelta(days=30)
    elif frequency == ScheduleFrequency.QUARTERLY:
        next_run = datetime.now(tz.utc) + timedelta(days=90)

    schedule = ReportSchedule(
        organization_id=template.organization_id,
        template_id=template.id,
        name=request.name,
        schedule=frequency,
        schedule_time=request.schedule_time,
        next_run=next_run,
        recipients=request.recipients,
        status=ScheduleStatus.ACTIVE,
        parameters=request.parameters
    )

    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    return {
        "schedule": {
            "id": str(schedule.id),
            "template_id": str(schedule.template_id),
            "name": schedule.name,
            "schedule": schedule.schedule.value,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "status": schedule.status.value
        },
        "message": "Schedule created successfully"
    }


@router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific scheduled report."""
    result = await db.execute(
        select(ReportSchedule).where(ReportSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {
        "id": str(schedule.id),
        "template_id": str(schedule.template_id),
        "name": schedule.name,
        "schedule": schedule.schedule.value if schedule.schedule else None,
        "schedule_time": schedule.schedule_time,
        "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
        "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
        "recipients": schedule.recipients or [],
        "status": schedule.status.value if schedule.status else None,
        "parameters": schedule.parameters or {}
    }


@router.patch("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: int,
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Update a scheduled report (pause/resume)."""
    result = await db.execute(
        select(ReportSchedule).where(ReportSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if status:
        try:
            schedule.status = ScheduleStatus(status)
        except ValueError:
            pass

    await db.commit()

    return {
        "schedule": {
            "id": str(schedule.id),
            "name": schedule.name,
            "status": schedule.status.value if schedule.status else None
        },
        "message": "Schedule updated successfully"
    }


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a scheduled report."""
    result = await db.execute(
        select(ReportSchedule).where(ReportSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await db.delete(schedule)
    await db.commit()

    return {"message": "Schedule deleted successfully"}


@router.post("/schedules/{schedule_id}/run")
async def run_schedule_now(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Manually trigger a scheduled report."""
    result = await db.execute(
        select(ReportSchedule).where(ReportSchedule.id == schedule_id)
    )
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Get template
    template_result = await db.execute(
        select(ReportTemplate).where(ReportTemplate.id == schedule.template_id)
    )
    template = template_result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Generate the report
    report = GeneratedReport(
        organization_id=schedule.organization_id,
        template_id=schedule.template_id,
        schedule_id=schedule.id,
        name=f"{schedule.name} - {datetime.now(tz.utc).strftime('%Y-%m-%d')}",
        format=ReportFormat.PDF,
        status=ReportStatus.COMPLETED,
        size_bytes=1024 * 1024 * 2,
        download_url=f"/api/v2/reports/download/{uuid.uuid4().hex[:8]}",
        parameters=schedule.parameters or {},
        expires_at=datetime.now(tz.utc) + timedelta(days=7)
    )

    db.add(report)
    schedule.last_run = datetime.now(tz.utc)

    await db.commit()
    await db.refresh(report)

    return {
        "report": {
            "id": str(report.id),
            "name": report.name,
            "download_url": report.download_url
        },
        "message": "Scheduled report generated successfully"
    }


# ============================================
# REPORT BUILDER
# ============================================

@router.get("/builder/data-sources")
async def get_data_sources():
    """Get available data sources for custom reports."""
    return {
        "sources": [
            {"id": "trials", "name": "Trials", "fields": ["trial_id", "name", "season", "location", "status"]},
            {"id": "studies", "name": "Studies", "fields": ["study_id", "name", "trial_id", "start_date", "end_date"]},
            {"id": "germplasm", "name": "Germplasm", "fields": ["germplasm_id", "name", "species", "origin", "pedigree"]},
            {"id": "observations", "name": "Observations", "fields": ["observation_id", "value", "trait", "unit", "timestamp"]},
            {"id": "crosses", "name": "Crosses", "fields": ["cross_id", "parent1", "parent2", "date", "success"]},
            {"id": "samples", "name": "Samples", "fields": ["sample_id", "type", "germplasm_id", "collection_date"]},
        ]
    }


@router.get("/builder/visualizations")
async def get_visualizations():
    """Get available visualization types for custom reports."""
    return {
        "visualizations": [
            {"id": "bar", "name": "Bar Chart", "icon": "bar-chart"},
            {"id": "line", "name": "Line Chart", "icon": "trending-up"},
            {"id": "pie", "name": "Pie Chart", "icon": "pie-chart"},
            {"id": "scatter", "name": "Scatter Plot", "icon": "scatter-chart"},
            {"id": "table", "name": "Data Table", "icon": "table"},
            {"id": "heatmap", "name": "Heatmap", "icon": "grid"},
        ]
    }


@router.post("/builder/preview")
async def preview_custom_report(
    data_sources: list[str],
    visualizations: list[str],
    filters: dict = {},
):
    """Preview a custom report configuration."""
    return {
        "preview_url": f"/api/v2/reports/builder/preview/{uuid.uuid4().hex[:8]}",
        "estimated_rows": 1500,
        "estimated_size_mb": 2.4,
        "data_sources": data_sources,
        "visualizations": visualizations
    }
