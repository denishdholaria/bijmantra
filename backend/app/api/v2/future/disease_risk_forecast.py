"""
Disease Risk Forecast API

Endpoints for disease risk prediction and forecasting.

Scientific Framework (preserved per scientific-documentation.md):
    Disease Risk Models:
        - Late Blight (Blitecast, SIMCAST): Temperature + humidity + leaf wetness
        - Powdery Mildew: Temperature + relative humidity
        - Rust diseases: Degree-day accumulation models
    
    Risk Factors:
        - Weather conditions (temperature, humidity, precipitation)
        - Crop growth stage (susceptibility varies)
        - Historical disease pressure
        - Inoculum presence (spore counts, nearby infections)
        - Variety resistance level
    
    Risk Levels:
        - LOW: Conditions unfavorable for disease development
        - MEDIUM: Some favorable conditions, monitor closely
        - HIGH: Highly favorable conditions, preventive action recommended
    
    Disease Triangle:
        Disease = Susceptible Host × Virulent Pathogen × Favorable Environment
        All three must be present for disease outbreak
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import disease_risk_forecast as disease_crud
from app.schemas.future.crop_protection import (
    DiseaseRiskForecast,
    DiseaseRiskForecastCreate,
)
from app.models.core import User

router = APIRouter(prefix="/disease-risk-forecasts", tags=["Disease Risk Forecasts"])


@router.get("/", response_model=List[DiseaseRiskForecast])
async def list_disease_forecasts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all disease risk forecasts for the organization."""
    records, _ = await disease_crud.disease_risk_forecast.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return records


@router.get("/active", response_model=List[DiseaseRiskForecast])
async def get_active_forecasts(
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get all active (current and future) disease risk forecasts.
    
    Returns forecasts with forecast_date >= today, sorted by risk level.
    """
    records = await disease_crud.disease_risk_forecast.get_active_forecasts(
        db, org_id=org_id
    )
    return records


@router.get("/high-risk", response_model=List[DiseaseRiskForecast])
async def get_high_risk_forecasts(
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get all HIGH risk disease forecasts.
    
    These require immediate attention and preventive action.
    """
    records = await disease_crud.disease_risk_forecast.get_high_risk(
        db, org_id=org_id
    )
    return records


@router.get("/{id}", response_model=DiseaseRiskForecast)
async def get_disease_forecast(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single disease risk forecast by ID."""
    record = await disease_crud.disease_risk_forecast.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Disease forecast not found")
    return record


@router.post("/", response_model=DiseaseRiskForecast, status_code=201)
async def create_disease_forecast(
    record_in: DiseaseRiskForecastCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new disease risk forecast.
    
    Disease Triangle: Host × Pathogen × Environment
    All three factors must be considered for accurate forecasting.
    """
    record = await disease_crud.disease_risk_forecast.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{id}", status_code=204)
async def delete_disease_forecast(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a disease risk forecast."""
    record = await disease_crud.disease_risk_forecast.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Disease forecast not found")
    
    await disease_crud.disease_risk_forecast.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}", response_model=List[DiseaseRiskForecast])
async def get_field_disease_forecasts(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all disease risk forecasts for a field."""
    records = await disease_crud.disease_risk_forecast.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return records
