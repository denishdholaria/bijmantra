"""
Emissions Tracking API Endpoints

Provides REST API for agricultural emissions tracking and carbon footprint analysis.

Endpoints:
    POST   /api/v2/emissions/sources          - Create emission source
    GET    /api/v2/emissions/sources          - List emission sources
    POST   /api/v2/emissions/calculate        - Calculate emissions
    GET    /api/v2/emissions/dashboard        - Overview metrics
    GET    /api/v2/emissions/varieties        - List variety footprints
    GET    /api/v2/emissions/varieties/{id}   - Get variety footprint
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User
from app.models.climate import EmissionSource, EmissionCategory, VarietyFootprint
from app.services.emissions_calculator_service import get_emissions_calculator_service

router = APIRouter(prefix="/emissions", tags=["emissions"])


# Pydantic schemas
class EmissionSourceCreate(BaseModel):
    """Schema for creating emission source"""
    location_id: int = Field(..., description="Location/field ID")
    trial_id: Optional[int] = Field(None, description="Trial ID (optional)")
    study_id: Optional[int] = Field(None, description="Study ID (optional)")
    activity_date: date = Field(..., description="Date of activity")
    category: EmissionCategory = Field(..., description="Emission category")
    source_name: str = Field(..., description="Source name (e.g., 'Urea', 'Diesel')")
    quantity: float = Field(..., description="Quantity of input used")
    unit: str = Field(..., description="Unit of quantity (kg, L, kWh, etc.)")
    notes: Optional[str] = Field(None, description="Additional notes")


class EmissionSourceResponse(BaseModel):
    """Schema for emission source response"""
    id: int
    organization_id: int
    location_id: int
    trial_id: Optional[int]
    study_id: Optional[int]
    activity_date: date
    category: EmissionCategory
    source_name: str
    quantity: float
    unit: str
    co2e_emissions: float
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class EmissionsCalculateRequest(BaseModel):
    """Schema for emissions calculation request"""
    fertilizer: Optional[dict] = Field(None, description="Fertilizer inputs {n_kg, p_kg, k_kg}")
    fuel: Optional[dict] = Field(None, description="Fuel inputs {diesel_liters, petrol_liters}")
    irrigation: Optional[dict] = Field(None, description="Irrigation inputs {kwh, energy_source}")


class EmissionsCalculateResponse(BaseModel):
    """Schema for emissions calculation response"""
    fertilizer_emissions: Optional[dict] = None
    fuel_emissions: Optional[dict] = None
    irrigation_emissions: Optional[dict] = None
    total_emissions: float


class EmissionsDashboardResponse(BaseModel):
    """Schema for emissions dashboard response"""
    total_emissions: float
    emissions_by_category: dict
    total_sources: int
    average_emissions_per_source: float
    top_emission_sources: List[dict]


class VarietyFootprintResponse(BaseModel):
    """Schema for variety footprint response"""
    id: int
    organization_id: int
    germplasm_id: int
    trial_id: Optional[int]
    study_id: Optional[int]
    season_id: Optional[int]
    location_id: int
    total_emissions: float
    total_yield: float
    carbon_intensity: float
    emissions_by_category: Optional[dict]
    measurement_date: date
    notes: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# Endpoints
@router.post("/sources", response_model=EmissionSourceResponse, status_code=201)
async def create_emission_source(
    data: EmissionSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new emission source record.
    
    Automatically calculates CO2e emissions based on category and quantity.
    
    Emission Factors:
        Fertilizer:
            - Urea: 4.5 kg CO2e/kg N
            - Ammonium Nitrate: 3.8 kg CO2e/kg N
            - DAP: 1.2 kg CO2e/kg P2O5
        
        Fuel:
            - Diesel: 2.7 kg CO2e/L
            - Petrol: 2.3 kg CO2e/L
        
        Irrigation:
            - Grid electricity: 0.8 kg CO2e/kWh
    
    Args:
        data: Emission source creation data
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Created emission source record
    
    Raises:
        HTTPException: If creation fails
    """
    service = get_emissions_calculator_service()
    
    try:
        emission_source = await service.create_emission_source(
            db=db,
            organization_id=current_user.organization_id,
            location_id=data.location_id,
            activity_date=data.activity_date,
            category=data.category,
            source_name=data.source_name,
            quantity=data.quantity,
            unit=data.unit,
            trial_id=data.trial_id,
            study_id=data.study_id,
            notes=data.notes
        )
        
        return emission_source
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create emission source: {str(e)}")


@router.get("/sources", response_model=List[EmissionSourceResponse])
async def list_emission_sources(
    location_id: Optional[int] = Query(None, description="Filter by location"),
    trial_id: Optional[int] = Query(None, description="Filter by trial"),
    study_id: Optional[int] = Query(None, description="Filter by study"),
    category: Optional[EmissionCategory] = Query(None, description="Filter by category"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List emission sources with optional filters.
    
    Args:
        location_id: Filter by location (optional)
        trial_id: Filter by trial (optional)
        study_id: Filter by study (optional)
        category: Filter by category (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        limit: Maximum results
        offset: Results offset
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of emission source records
    """
    service = get_emissions_calculator_service()
    
    try:
        sources = await service.get_emission_sources(
            db=db,
            organization_id=current_user.organization_id,
            location_id=location_id,
            trial_id=trial_id,
            study_id=study_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return sources
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list emission sources: {str(e)}")


@router.post("/calculate", response_model=EmissionsCalculateResponse)
async def calculate_emissions(
    data: EmissionsCalculateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate emissions from agricultural inputs.
    
    Provides instant emissions calculations without creating database records.
    Useful for planning and scenario analysis.
    
    Calculation Methods:
        Fertilizer Emissions:
            Total = Production + N2O from soil
            N2O = N applied × 0.015 × 298 (GWP)
        
        Fuel Emissions:
            Diesel: 2.7 kg CO2e/L
            Petrol: 2.3 kg CO2e/L
        
        Irrigation Emissions:
            Electricity: 0.8 kg CO2e/kWh (grid average)
    
    Args:
        data: Emissions calculation request
        current_user: Authenticated user
    
    Returns:
        Calculated emissions by category
    
    Example:
        Request:
        {
            "fertilizer": {"n_kg": 100, "p_kg": 50, "k_kg": 30},
            "fuel": {"diesel_liters": 50},
            "irrigation": {"kwh": 1000, "energy_source": "grid"}
        }
        
        Response:
        {
            "fertilizer_emissions": {
                "n_emissions": 400.0,
                "p_emissions": 50.0,
                "k_emissions": 15.0,
                "n2o_emissions": 447.0,
                "total_emissions": 912.0
            },
            "fuel_emissions": {
                "diesel_emissions": 135.0,
                "total_emissions": 135.0
            },
            "irrigation_emissions": {
                "emissions": 800.0
            },
            "total_emissions": 1847.0
        }
    """
    service = get_emissions_calculator_service()
    
    try:
        result = {
            "fertilizer_emissions": None,
            "fuel_emissions": None,
            "irrigation_emissions": None,
            "total_emissions": 0.0
        }
        
        # Calculate fertilizer emissions
        if data.fertilizer:
            fert_result = service.calculate_fertilizer_emissions(
                n_kg=data.fertilizer.get('n_kg', 0),
                p_kg=data.fertilizer.get('p_kg', 0),
                k_kg=data.fertilizer.get('k_kg', 0)
            )
            result["fertilizer_emissions"] = fert_result
            result["total_emissions"] += fert_result['total_emissions']
        
        # Calculate fuel emissions
        if data.fuel:
            fuel_result = service.calculate_fuel_emissions(
                diesel_liters=data.fuel.get('diesel_liters', 0),
                petrol_liters=data.fuel.get('petrol_liters', 0)
            )
            result["fuel_emissions"] = fuel_result
            result["total_emissions"] += fuel_result['total_emissions']
        
        # Calculate irrigation emissions
        if data.irrigation:
            irrig_result = service.calculate_irrigation_emissions(
                kwh=data.irrigation.get('kwh', 0),
                energy_source=data.irrigation.get('energy_source', 'grid')
            )
            result["irrigation_emissions"] = irrig_result
            result["total_emissions"] += irrig_result['emissions']
        
        result["total_emissions"] = round(result["total_emissions"], 2)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate emissions: {str(e)}")


@router.get("/dashboard", response_model=EmissionsDashboardResponse)
async def get_emissions_dashboard(
    start_date: Optional[date] = Query(None, description="Start date for metrics"),
    end_date: Optional[date] = Query(None, description="End date for metrics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get emissions tracking dashboard metrics.
    
    Provides overview of emissions across all sources.
    
    Args:
        start_date: Start date for metrics (optional)
        end_date: End date for metrics (optional)
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Dashboard metrics
    """
    service = get_emissions_calculator_service()
    
    try:
        # Get all emission sources
        sources = await service.get_emission_sources(
            db=db,
            organization_id=current_user.organization_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if not sources:
            return EmissionsDashboardResponse(
                total_emissions=0.0,
                emissions_by_category={},
                total_sources=0,
                average_emissions_per_source=0.0,
                top_emission_sources=[]
            )
        
        # Calculate metrics
        total_emissions = sum(s.co2e_emissions for s in sources)
        
        # Emissions by category
        emissions_by_category = {}
        for source in sources:
            category = source.category.value
            if category not in emissions_by_category:
                emissions_by_category[category] = 0.0
            emissions_by_category[category] += source.co2e_emissions
        
        # Round category emissions
        emissions_by_category = {
            k: round(v, 2) for k, v in emissions_by_category.items()
        }
        
        # Average per source
        average_per_source = total_emissions / len(sources) if sources else 0
        
        # Top emission sources
        sorted_sources = sorted(sources, key=lambda x: x.co2e_emissions, reverse=True)
        top_sources = [
            {
                "source_name": s.source_name,
                "category": s.category.value,
                "emissions": round(s.co2e_emissions, 2),
                "date": s.activity_date.isoformat()
            }
            for s in sorted_sources[:10]
        ]
        
        return EmissionsDashboardResponse(
            total_emissions=round(total_emissions, 2),
            emissions_by_category=emissions_by_category,
            total_sources=len(sources),
            average_emissions_per_source=round(average_per_source, 2),
            top_emission_sources=top_sources
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard metrics: {str(e)}")


@router.get("/varieties", response_model=List[VarietyFootprintResponse])
async def list_variety_footprints(
    germplasm_id: Optional[int] = Query(None, description="Filter by germplasm"),
    trial_id: Optional[int] = Query(None, description="Filter by trial"),
    location_id: Optional[int] = Query(None, description="Filter by location"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List variety carbon footprints.
    
    Carbon Intensity:
        CI (kg CO2e/kg yield) = Total Emissions / Total Yield
        
        Typical ranges:
        - Rice: 2-4 kg CO2e/kg grain
        - Wheat: 0.4-0.8 kg CO2e/kg grain
        - Maize: 0.3-0.6 kg CO2e/kg grain
    
    Args:
        germplasm_id: Filter by germplasm (optional)
        trial_id: Filter by trial (optional)
        location_id: Filter by location (optional)
        limit: Maximum results
        offset: Results offset
        db: Database session
        current_user: Authenticated user
    
    Returns:
        List of variety footprint records
    """
    from sqlalchemy import select
    
    try:
        query = select(VarietyFootprint).where(
            VarietyFootprint.organization_id == current_user.organization_id
        )
        
        if germplasm_id:
            query = query.where(VarietyFootprint.germplasm_id == germplasm_id)
        
        if trial_id:
            query = query.where(VarietyFootprint.trial_id == trial_id)
        
        if location_id:
            query = query.where(VarietyFootprint.location_id == location_id)
        
        query = query.order_by(VarietyFootprint.carbon_intensity.asc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        footprints = result.scalars().all()
        
        return footprints
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list variety footprints: {str(e)}")


@router.get("/varieties/{footprint_id}", response_model=VarietyFootprintResponse)
async def get_variety_footprint(
    footprint_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific variety footprint by ID.
    
    Args:
        footprint_id: Variety footprint ID
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Variety footprint record
    
    Raises:
        HTTPException: If footprint not found
    """
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(VarietyFootprint).where(
                VarietyFootprint.id == footprint_id,
                VarietyFootprint.organization_id == current_user.organization_id
            )
        )
        footprint = result.scalar_one_or_none()
        
        if not footprint:
            raise HTTPException(status_code=404, detail="Variety footprint not found")
        
        return footprint
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get variety footprint: {str(e)}")
