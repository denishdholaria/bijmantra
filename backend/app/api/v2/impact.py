"""
Impact Metrics & Reporting API Endpoints

Provides REST API for sustainability impact tracking and reporting.

Endpoints:
    POST   /api/v2/impact/metrics             - Create metric
    GET    /api/v2/impact/metrics             - List metrics
    GET    /api/v2/impact/dashboard           - Sustainability dashboard
    GET    /api/v2/impact/sdg                 - List SDG indicators
    POST   /api/v2/impact/releases            - Create release
    GET    /api/v2/impact/releases            - List releases
    POST   /api/v2/impact/reports/generate    - Generate report
    GET    /api/v2/impact/reports             - List reports
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User
from app.models.climate import (
    ImpactMetric, SDGIndicator, VarietyRelease, ImpactReport,
    MetricType, SDGGoal, ReleaseStatus
)
from app.services.sustainability_metrics_service import get_sustainability_metrics_service

router = APIRouter(prefix="/impact", tags=["impact"])


# Pydantic schemas
class ImpactMetricCreate(BaseModel):
    """Schema for creating impact metric"""
    program_id: Optional[int] = Field(None, description="Program ID (optional)")
    metric_type: MetricType = Field(..., description="Type of metric")
    metric_name: str = Field(..., description="Metric name")
    metric_value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    baseline_value: Optional[float] = Field(None, description="Baseline value")
    measurement_date: date = Field(..., description="Date of measurement")
    geographic_scope: Optional[str] = Field(None, description="Geographic scope")
    beneficiaries: Optional[int] = Field(None, description="Number of beneficiaries")
    notes: Optional[str] = Field(None, description="Additional notes")


class ImpactMetricResponse(BaseModel):
    """Schema for impact metric response"""
    id: int
    organization_id: int
    program_id: Optional[int]
    metric_type: MetricType
    metric_name: str
    metric_value: float
    unit: str
    baseline_value: Optional[float]
    measurement_date: date
    geographic_scope: Optional[str]
    beneficiaries: Optional[int]
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SDGIndicatorResponse(BaseModel):
    """Schema for SDG indicator response"""
    sdg_goal: str
    indicator_code: str
    indicator_name: str
    contribution_value: float
    unit: str


class ImpactDashboardResponse(BaseModel):
    """Schema for impact dashboard response"""
    hectares_impacted: dict
    farmers_reached: dict
    carbon_sequestered: dict
    emissions_reduced: dict
    sdg_indicators: List[SDGIndicatorResponse]


class VarietyReleaseCreate(BaseModel):
    """Schema for creating variety release"""
    germplasm_id: int = Field(..., description="Variety/germplasm ID")
    program_id: Optional[int] = Field(None, description="Program ID (optional)")
    release_name: str = Field(..., description="Official release name")
    release_date: date = Field(..., description="Date of release")
    release_status: ReleaseStatus = Field(ReleaseStatus.PENDING, description="Release status")
    country: str = Field(..., description="Country of release")
    region: Optional[str] = Field(None, description="Region/state")
    releasing_authority: str = Field(..., description="Government body or organization")
    registration_number: Optional[str] = Field(None, description="Official registration number")
    target_environment: Optional[str] = Field(None, description="Target production environment")
    expected_adoption_ha: Optional[float] = Field(None, description="Expected adoption (hectares)")
    actual_adoption_ha: Optional[float] = Field(None, description="Actual adoption (hectares)")
    documentation_url: Optional[str] = Field(None, description="Link to documentation")
    notes: Optional[str] = Field(None, description="Additional notes")


class VarietyReleaseResponse(BaseModel):
    """Schema for variety release response"""
    id: int
    organization_id: int
    germplasm_id: int
    program_id: Optional[int]
    release_name: str
    release_date: date
    release_status: ReleaseStatus
    country: str
    region: Optional[str]
    releasing_authority: str
    registration_number: Optional[str]
    target_environment: Optional[str]
    expected_adoption_ha: Optional[float]
    actual_adoption_ha: Optional[float]
    documentation_url: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ImpactReportGenerateRequest(BaseModel):
    """Schema for impact report generation request"""
    program_id: int = Field(..., description="Program ID")
    report_title: str = Field(..., description="Report title")
    report_type: str = Field(..., description="Report type (annual, donor, gee_partner, custom)")
    reporting_period_start: date = Field(..., description="Start date")
    reporting_period_end: date = Field(..., description="End date")
    format: str = Field("PDF", description="Report format (PDF, DOCX, HTML)")


class ImpactReportResponse(BaseModel):
    """Schema for impact report response"""
    id: int
    organization_id: int
    program_id: Optional[int]
    report_title: str
    report_type: str
    reporting_period_start: date
    reporting_period_end: date
    generated_date: date
    generated_by_user_id: int
    report_data: dict
    file_url: Optional[str]
    format: str
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# Endpoints
@router.post("/metrics", response_model=ImpactMetricResponse, status_code=201)
async def create_impact_metric(
    data: ImpactMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new impact metric record.
    
    Impact Metrics:
        - Hectares impacted: Area under improved varieties
        - Farmers reached: Direct + indirect beneficiaries
        - Yield improvement: % increase over baseline
        - Climate resilience: Stress tolerance indicators
        - Carbon sequestered: Total carbon sequestered (tonnes C)
        - Emissions reduced: Total emissions reduced (kg CO2e)
    
    Args:
        data: Impact metric creation data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created impact metric record
    
    Raises:
        HTTPException: If creation fails
    """
    try:
        metric = ImpactMetric(
            organization_id=current_user.organization_id,
            program_id=data.program_id,
            metric_type=data.metric_type,
            metric_name=data.metric_name,
            metric_value=data.metric_value,
            unit=data.unit,
            baseline_value=data.baseline_value,
            measurement_date=data.measurement_date,
            geographic_scope=data.geographic_scope,
            beneficiaries=data.beneficiaries,
            notes=data.notes
        )
        
        db.add(metric)
        await db.commit()
        await db.refresh(metric)
        
        return metric
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create impact metric: {str(e)}")


@router.get("/metrics", response_model=List[ImpactMetricResponse])
async def list_impact_metrics(
    program_id: Optional[int] = Query(None, description="Filter by program"),
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List impact metrics with optional filters.
    
    Args:
        program_id: Filter by program (optional)
        metric_type: Filter by metric type (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        limit: Maximum results
        offset: Results offset
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of impact metric records
    """
    from sqlalchemy import select
    
    try:
        query = select(ImpactMetric).where(
            ImpactMetric.organization_id == current_user.organization_id
        )
        
        if program_id:
            query = query.where(ImpactMetric.program_id == program_id)
        
        if metric_type:
            query = query.where(ImpactMetric.metric_type == metric_type)
        
        if start_date:
            query = query.where(ImpactMetric.measurement_date >= start_date)
        
        if end_date:
            query = query.where(ImpactMetric.measurement_date <= end_date)
        
        query = query.order_by(ImpactMetric.measurement_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        metrics = result.scalars().all()
        
        return metrics
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list impact metrics: {str(e)}")


@router.get("/dashboard", response_model=ImpactDashboardResponse)
async def get_impact_dashboard(
    program_id: int = Query(..., description="Program ID"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sustainability impact dashboard metrics.
    
    Provides comprehensive overview of program impact across multiple dimensions:
    - Hectares impacted
    - Farmers reached
    - Carbon sequestered
    - Emissions reduced
    - UN SDG alignment
    
    UN Sustainable Development Goals (SDGs):
        - SDG 2: Zero Hunger (food security, nutrition)
        - SDG 13: Climate Action (mitigation, adaptation)
        - SDG 15: Life on Land (biodiversity, ecosystems)
        - SDG 17: Partnerships (collaboration, knowledge sharing)
    
    Args:
        program_id: Program ID
        start_date: Start date for metrics
        end_date: End date for metrics
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Dashboard metrics
    """
    service = get_sustainability_metrics_service()
    
    try:
        # Calculate hectares impacted
        hectares_data = await service.calculate_hectares_impacted(
            db=db,
            organization_id=current_user.organization_id,
            program_id=program_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate farmers reached
        farmers_data = await service.calculate_farmers_reached(
            db=db,
            organization_id=current_user.organization_id,
            program_id=program_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate carbon sequestered
        carbon_data = await service.calculate_carbon_sequestered(
            db=db,
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            program_id=program_id
        )
        
        # Calculate emissions reduced
        emissions_data = await service.calculate_emissions_reduced(
            db=db,
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            program_id=program_id
        )
        
        # Generate SDG indicators
        sdg_indicators_data = await service.generate_sdg_indicators(
            db=db,
            organization_id=current_user.organization_id,
            program_id=program_id,
            start_date=start_date,
            end_date=end_date
        )
        
        sdg_indicators = [
            SDGIndicatorResponse(**indicator)
            for indicator in sdg_indicators_data
        ]
        
        return ImpactDashboardResponse(
            hectares_impacted=hectares_data,
            farmers_reached=farmers_data,
            carbon_sequestered=carbon_data,
            emissions_reduced=emissions_data,
            sdg_indicators=sdg_indicators
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard metrics: {str(e)}")


@router.get("/sdg", response_model=List[SDGIndicatorResponse])
async def list_sdg_indicators(
    program_id: int = Query(..., description="Program ID"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List UN SDG indicators for a program.
    
    Maps program outcomes to UN Sustainable Development Goals:
    - SDG 2: Zero Hunger
    - SDG 13: Climate Action
    - SDG 15: Life on Land
    - SDG 17: Partnerships
    
    Args:
        program_id: Program ID
        start_date: Start date
        end_date: End date
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of SDG indicators
    """
    service = get_sustainability_metrics_service()
    
    try:
        indicators_data = await service.generate_sdg_indicators(
            db=db,
            organization_id=current_user.organization_id,
            program_id=program_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return [SDGIndicatorResponse(**indicator) for indicator in indicators_data]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list SDG indicators: {str(e)}")


@router.post("/releases", response_model=VarietyReleaseResponse, status_code=201)
async def create_variety_release(
    data: VarietyReleaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new variety release record.
    
    Tracks official variety releases through government or seed company channels.
    
    Args:
        data: Variety release creation data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created variety release record
    
    Raises:
        HTTPException: If creation fails
    """
    try:
        release = VarietyRelease(
            organization_id=current_user.organization_id,
            germplasm_id=data.germplasm_id,
            program_id=data.program_id,
            release_name=data.release_name,
            release_date=data.release_date,
            release_status=data.release_status,
            country=data.country,
            region=data.region,
            releasing_authority=data.releasing_authority,
            registration_number=data.registration_number,
            target_environment=data.target_environment,
            expected_adoption_ha=data.expected_adoption_ha,
            actual_adoption_ha=data.actual_adoption_ha,
            documentation_url=data.documentation_url,
            notes=data.notes
        )
        
        db.add(release)
        await db.commit()
        await db.refresh(release)
        
        return release
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create variety release: {str(e)}")


@router.get("/releases", response_model=List[VarietyReleaseResponse])
async def list_variety_releases(
    program_id: Optional[int] = Query(None, description="Filter by program"),
    germplasm_id: Optional[int] = Query(None, description="Filter by germplasm"),
    country: Optional[str] = Query(None, description="Filter by country"),
    release_status: Optional[ReleaseStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List variety releases with optional filters.
    
    Args:
        program_id: Filter by program (optional)
        germplasm_id: Filter by germplasm (optional)
        country: Filter by country (optional)
        release_status: Filter by status (optional)
        limit: Maximum results
        offset: Results offset
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of variety release records
    """
    from sqlalchemy import select
    
    try:
        query = select(VarietyRelease).where(
            VarietyRelease.organization_id == current_user.organization_id
        )
        
        if program_id:
            query = query.where(VarietyRelease.program_id == program_id)
        
        if germplasm_id:
            query = query.where(VarietyRelease.germplasm_id == germplasm_id)
        
        if country:
            query = query.where(VarietyRelease.country == country)
        
        if release_status:
            query = query.where(VarietyRelease.release_status == release_status)
        
        query = query.order_by(VarietyRelease.release_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        releases = result.scalars().all()
        
        return releases
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list variety releases: {str(e)}")


@router.post("/reports/generate", response_model=ImpactReportResponse, status_code=201)
async def generate_impact_report(
    data: ImpactReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a comprehensive impact report.
    
    Aggregates all sustainability metrics into a structured report:
    - Hectares impacted
    - Farmers reached
    - Carbon sequestered
    - Emissions reduced
    - UN SDG indicators
    
    Report Types:
        - annual: Annual impact report
        - donor: Donor report
        - gee_partner: Google Earth Engine Partner Tier application
        - custom: Custom report
    
    Args:
        data: Report generation request
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Generated impact report
    
    Raises:
        HTTPException: If generation fails
    """
    service = get_sustainability_metrics_service()
    
    try:
        report = await service.create_impact_report(
            db=db,
            organization_id=current_user.organization_id,
            program_id=data.program_id,
            report_title=data.report_title,
            report_type=data.report_type,
            reporting_period_start=data.reporting_period_start,
            reporting_period_end=data.reporting_period_end,
            generated_by_user_id=current_user.id,
            format=data.format
        )
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate impact report: {str(e)}")


@router.get("/reports", response_model=List[ImpactReportResponse])
async def list_impact_reports(
    program_id: Optional[int] = Query(None, description="Filter by program"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List impact reports with optional filters.
    
    Args:
        program_id: Filter by program (optional)
        report_type: Filter by report type (optional)
        limit: Maximum results
        offset: Results offset
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of impact report records
    """
    from sqlalchemy import select
    
    try:
        query = select(ImpactReport).where(
            ImpactReport.organization_id == current_user.organization_id
        )
        
        if program_id:
            query = query.where(ImpactReport.program_id == program_id)
        
        if report_type:
            query = query.where(ImpactReport.report_type == report_type)
        
        query = query.order_by(ImpactReport.generated_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return reports
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list impact reports: {str(e)}")
