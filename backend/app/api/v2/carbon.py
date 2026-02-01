"""
Carbon Monitoring API Endpoints

Provides REST API for carbon stock tracking and monitoring.

Endpoints:
    POST   /api/v2/carbon/stocks              - Create carbon stock
    GET    /api/v2/carbon/stocks              - List carbon stocks
    GET    /api/v2/carbon/stocks/{id}         - Get carbon stock
    PUT    /api/v2/carbon/stocks/{id}         - Update carbon stock
    DELETE /api/v2/carbon/stocks/{id}         - Delete carbon stock
    POST   /api/v2/carbon/measurements        - Create measurement
    GET    /api/v2/carbon/measurements        - List measurements
    GET    /api/v2/carbon/dashboard           - Overview metrics
    GET    /api/v2/carbon/time-series         - Time series data
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User
from app.models.climate import CarbonStock, CarbonMeasurement, CarbonMeasurementType
from app.services.carbon_monitoring_service import get_carbon_monitoring_service

router = APIRouter(prefix="/carbon", tags=["carbon"])


# Pydantic schemas
class CarbonStockCreate(BaseModel):
    """Schema for creating carbon stock"""
    location_id: int = Field(..., description="Location/field ID")
    measurement_date: date = Field(..., description="Date of measurement")
    measurement_type: CarbonMeasurementType = Field(..., description="Type of measurement")
    soil_carbon_stock: Optional[float] = Field(None, description="Soil carbon (t/ha)")
    vegetation_carbon_stock: Optional[float] = Field(None, description="Vegetation carbon (t/ha)")
    measurement_depth_cm: int = Field(30, description="Soil sampling depth (cm)")
    confidence_level: float = Field(0.8, description="Confidence level (0-1)")
    gee_image_id: Optional[str] = Field(None, description="Google Earth Engine image ID")
    additional_data: Optional[dict] = Field(None, description="Additional metadata")


class CarbonStockUpdate(BaseModel):
    """Schema for updating carbon stock"""
    soil_carbon_stock: Optional[float] = None
    vegetation_carbon_stock: Optional[float] = None
    confidence_level: Optional[float] = None
    additional_data: Optional[dict] = None


class CarbonStockResponse(BaseModel):
    """Schema for carbon stock response"""
    id: int
    organization_id: int
    location_id: int
    measurement_date: date
    soil_carbon_stock: Optional[float]
    vegetation_carbon_stock: Optional[float]
    total_carbon_stock: float
    measurement_depth_cm: int
    measurement_type: CarbonMeasurementType
    confidence_level: float
    gee_image_id: Optional[str]
    additional_data: Optional[dict]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CarbonMeasurementCreate(BaseModel):
    """Schema for creating carbon measurement"""
    location_id: int = Field(..., description="Location/field ID")
    carbon_stock_id: Optional[int] = Field(None, description="Associated carbon stock ID")
    measurement_date: date = Field(..., description="Date of measurement")
    measurement_type: CarbonMeasurementType = Field(..., description="Type of measurement")
    carbon_value: float = Field(..., description="Carbon value")
    unit: str = Field(..., description="Unit of measurement")
    depth_from_cm: Optional[int] = Field(None, description="Depth from (cm)")
    depth_to_cm: Optional[int] = Field(None, description="Depth to (cm)")
    bulk_density: Optional[float] = Field(None, description="Bulk density (g/cm³)")
    sample_id: Optional[str] = Field(None, description="Sample ID")
    method: Optional[str] = Field(None, description="Measurement method")
    notes: Optional[str] = Field(None, description="Additional notes")


class CarbonMeasurementResponse(BaseModel):
    """Schema for carbon measurement response"""
    id: int
    organization_id: int
    location_id: int
    carbon_stock_id: Optional[int]
    measurement_date: date
    measurement_type: CarbonMeasurementType
    carbon_value: float
    unit: str
    depth_from_cm: Optional[int]
    depth_to_cm: Optional[int]
    bulk_density: Optional[float]
    sample_id: Optional[str]
    method: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CarbonDashboardResponse(BaseModel):
    """Schema for carbon dashboard response"""
    total_locations: int
    total_carbon_stock: float
    average_carbon_per_location: float
    soil_carbon_total: float
    vegetation_carbon_total: float
    recent_measurements: int
    sequestration_rate: Optional[float]


class CarbonTimeSeriesResponse(BaseModel):
    """Schema for carbon time series response"""
    date: str
    soil_carbon: Optional[float]
    vegetation_carbon: Optional[float]
    total_carbon: float
    measurement_type: str
    confidence: float


# Endpoints
@router.post("/stocks", response_model=CarbonStockResponse, status_code=201)
async def create_carbon_stock(
    data: CarbonStockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new carbon stock record.
    
    Calculates total carbon stock from soil and vegetation components.
    
    Args:
        data: Carbon stock creation data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created carbon stock record
    
    Raises:
        HTTPException: If creation fails
    """
    service = get_carbon_monitoring_service()
    
    try:
        carbon_stock = await service.create_carbon_stock(
            db=db,
            organization_id=current_user.organization_id,
            location_id=data.location_id,
            measurement_date=data.measurement_date,
            measurement_type=data.measurement_type,
            soil_carbon_stock=data.soil_carbon_stock,
            vegetation_carbon_stock=data.vegetation_carbon_stock,
            measurement_depth_cm=data.measurement_depth_cm,
            confidence_level=data.confidence_level,
            gee_image_id=data.gee_image_id,
            additional_data=data.additional_data
        )
        
        return carbon_stock
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create carbon stock: {str(e)}")


@router.get("/stocks", response_model=List[CarbonStockResponse])
async def list_carbon_stocks(
    location_id: Optional[int] = Query(None, description="Filter by location"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    measurement_type: Optional[CarbonMeasurementType] = Query(None, description="Filter by measurement type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List carbon stocks with optional filters.
    
    Args:
        location_id: Filter by location (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        measurement_type: Filter by measurement type (optional)
        limit: Maximum results
        offset: Results offset
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of carbon stock records
    """
    service = get_carbon_monitoring_service()
    
    try:
        stocks = await service.get_carbon_stocks(
            db=db,
            organization_id=current_user.organization_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date,
            measurement_type=measurement_type,
            limit=limit,
            offset=offset
        )
        
        return stocks
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list carbon stocks: {str(e)}")


@router.get("/stocks/{stock_id}", response_model=CarbonStockResponse)
async def get_carbon_stock(
    stock_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific carbon stock by ID.
    
    Args:
        stock_id: Carbon stock ID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Carbon stock record
    
    Raises:
        HTTPException: If stock not found
    """
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(CarbonStock).where(
                CarbonStock.id == stock_id,
                CarbonStock.organization_id == current_user.organization_id
            )
        )
        stock = result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail="Carbon stock not found")
        
        return stock
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get carbon stock: {str(e)}")


@router.put("/stocks/{stock_id}", response_model=CarbonStockResponse)
async def update_carbon_stock(
    stock_id: int,
    data: CarbonStockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a carbon stock record.
    
    Args:
        stock_id: Carbon stock ID
        data: Update data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Updated carbon stock record
    
    Raises:
        HTTPException: If stock not found or update fails
    """
    from sqlalchemy import select
    
    try:
        # Get existing stock
        result = await db.execute(
            select(CarbonStock).where(
                CarbonStock.id == stock_id,
                CarbonStock.organization_id == current_user.organization_id
            )
        )
        stock = result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail="Carbon stock not found")
        
        # Update fields
        if data.soil_carbon_stock is not None:
            stock.soil_carbon_stock = data.soil_carbon_stock
        if data.vegetation_carbon_stock is not None:
            stock.vegetation_carbon_stock = data.vegetation_carbon_stock
        if data.confidence_level is not None:
            stock.confidence_level = data.confidence_level
        if data.additional_data is not None:
            stock.additional_data = data.additional_data
        
        # Recalculate total
        stock.total_carbon_stock = (
            (stock.soil_carbon_stock or 0) + 
            (stock.vegetation_carbon_stock or 0)
        )
        
        await db.commit()
        await db.refresh(stock)
        
        return stock
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update carbon stock: {str(e)}")


@router.delete("/stocks/{stock_id}", status_code=204)
async def delete_carbon_stock(
    stock_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a carbon stock record.
    
    Args:
        stock_id: Carbon stock ID
        db: Database session
        current_user: Authenticated user
    
    Raises:
        HTTPException: If stock not found or deletion fails
    """
    from sqlalchemy import select, delete
    
    try:
        # Check if stock exists
        result = await db.execute(
            select(CarbonStock).where(
                CarbonStock.id == stock_id,
                CarbonStock.organization_id == current_user.organization_id
            )
        )
        stock = result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail="Carbon stock not found")
        
        # Delete stock
        await db.execute(
            delete(CarbonStock).where(CarbonStock.id == stock_id)
        )
        await db.commit()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete carbon stock: {str(e)}")


@router.post("/measurements", response_model=CarbonMeasurementResponse, status_code=201)
async def create_carbon_measurement(
    data: CarbonMeasurementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new carbon measurement record.
    
    Args:
        data: Carbon measurement creation data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created carbon measurement record
    
    Raises:
        HTTPException: If creation fails
    """
    try:
        measurement = CarbonMeasurement(
            organization_id=current_user.organization_id,
            location_id=data.location_id,
            carbon_stock_id=data.carbon_stock_id,
            measurement_date=data.measurement_date,
            measurement_type=data.measurement_type,
            carbon_value=data.carbon_value,
            unit=data.unit,
            depth_from_cm=data.depth_from_cm,
            depth_to_cm=data.depth_to_cm,
            bulk_density=data.bulk_density,
            sample_id=data.sample_id,
            method=data.method,
            notes=data.notes
        )
        
        db.add(measurement)
        await db.commit()
        await db.refresh(measurement)
        
        return measurement
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create carbon measurement: {str(e)}")


@router.get("/measurements", response_model=List[CarbonMeasurementResponse])
async def list_carbon_measurements(
    location_id: Optional[int] = Query(None, description="Filter by location"),
    carbon_stock_id: Optional[int] = Query(None, description="Filter by carbon stock"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List carbon measurements with optional filters.
    
    Args:
        location_id: Filter by location (optional)
        carbon_stock_id: Filter by carbon stock (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        limit: Maximum results
        offset: Results offset
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of carbon measurement records
    """
    from sqlalchemy import select
    
    try:
        query = select(CarbonMeasurement).where(
            CarbonMeasurement.organization_id == current_user.organization_id
        )
        
        if location_id:
            query = query.where(CarbonMeasurement.location_id == location_id)
        
        if carbon_stock_id:
            query = query.where(CarbonMeasurement.carbon_stock_id == carbon_stock_id)
        
        if start_date:
            query = query.where(CarbonMeasurement.measurement_date >= start_date)
        
        if end_date:
            query = query.where(CarbonMeasurement.measurement_date <= end_date)
        
        query = query.order_by(CarbonMeasurement.measurement_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        measurements = result.scalars().all()
        
        return measurements
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list carbon measurements: {str(e)}")


@router.get("/dashboard", response_model=CarbonDashboardResponse)
async def get_carbon_dashboard(
    start_date: Optional[date] = Query(None, description="Start date for metrics"),
    end_date: Optional[date] = Query(None, description="End date for metrics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get carbon monitoring dashboard metrics.
    
    Provides overview of carbon stocks across all locations.
    
    Args:
        start_date: Start date for metrics (optional)
        end_date: End date for metrics (optional)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Dashboard metrics
    """
    from sqlalchemy import select, func
    
    service = get_carbon_monitoring_service()
    
    try:
        # Get all stocks for organization
        stocks = await service.get_carbon_stocks(
            db=db,
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if not stocks:
            return CarbonDashboardResponse(
                total_locations=0,
                total_carbon_stock=0.0,
                average_carbon_per_location=0.0,
                soil_carbon_total=0.0,
                vegetation_carbon_total=0.0,
                recent_measurements=0,
                sequestration_rate=None
            )
        
        # Calculate metrics
        unique_locations = len(set(s.location_id for s in stocks))
        total_carbon = sum(s.total_carbon_stock for s in stocks)
        soil_carbon = sum(s.soil_carbon_stock or 0 for s in stocks)
        vegetation_carbon = sum(s.vegetation_carbon_stock or 0 for s in stocks)
        average_per_location = total_carbon / unique_locations if unique_locations > 0 else 0
        
        # Count recent measurements (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_count = sum(1 for s in stocks if s.measurement_date >= thirty_days_ago)
        
        # Calculate sequestration rate if we have date range
        sequestration_rate = None
        if start_date and end_date and len(stocks) >= 2:
            # Get first location with multiple measurements
            location_stocks = {}
            for stock in stocks:
                if stock.location_id not in location_stocks:
                    location_stocks[stock.location_id] = []
                location_stocks[stock.location_id].append(stock)
            
            # Find location with most measurements
            for loc_id, loc_stocks in location_stocks.items():
                if len(loc_stocks) >= 2:
                    rate_data = await service.calculate_carbon_sequestration_rate(
                        db=db,
                        organization_id=current_user.organization_id,
                        location_id=loc_id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    if rate_data:
                        sequestration_rate = rate_data['rate_per_year']
                        break
        
        return CarbonDashboardResponse(
            total_locations=unique_locations,
            total_carbon_stock=round(total_carbon, 2),
            average_carbon_per_location=round(average_per_location, 2),
            soil_carbon_total=round(soil_carbon, 2),
            vegetation_carbon_total=round(vegetation_carbon, 2),
            recent_measurements=recent_count,
            sequestration_rate=sequestration_rate
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard metrics: {str(e)}")


@router.get("/time-series", response_model=List[CarbonTimeSeriesResponse])
async def get_carbon_time_series(
    location_id: int = Query(..., description="Location ID"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get carbon stock time series for a location.
    
    Args:
        location_id: Location ID
        start_date: Start date
        end_date: End date
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Time series data
    """
    service = get_carbon_monitoring_service()
    
    try:
        time_series = await service.get_carbon_time_series(
            db=db,
            organization_id=current_user.organization_id,
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return [CarbonTimeSeriesResponse(**item) for item in time_series]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get time series: {str(e)}")
