"""
Yield Prediction API

Endpoints for crop yield prediction and forecasting.

Scientific Methods (preserved per scientific-documentation.md):
    Prediction Methods:
    - Statistical: Historical yield regression, trend analysis
    - Process-based: Crop simulation models (DSSAT, APSIM, WOFOST)
    - ML-based: Remote sensing + weather ML models
    - Hybrid: Combination of process-based and ML approaches

    Key factors affecting yield:
    - Weather: temperature, precipitation, solar radiation
    - Soil: fertility, water holding capacity, drainage
    - Management: planting date, variety, fertilization, irrigation
    - Genetics: variety potential, stress tolerance
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import yield_prediction as prediction_crud
from app.schemas.future.crop_intelligence import (
    YieldPrediction,
    YieldPredictionCreate,
)
from app.models.core import User

router = APIRouter(prefix="/yield-prediction", tags=["Yield Prediction"])


@router.get("/", response_model=List[YieldPrediction])
async def list_yield_predictions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List all yield predictions for the organization."""
    predictions, _ = await prediction_crud.yield_prediction.get_multi(
        db, skip=skip, limit=limit, org_id=org_id
    )
    return predictions


@router.get("/{id}", response_model=YieldPrediction)
async def get_yield_prediction(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single yield prediction by ID."""
    prediction = await prediction_crud.yield_prediction.get(db, id=id)
    if not prediction or prediction.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Yield prediction not found")
    return prediction


@router.post("/", response_model=YieldPrediction, status_code=201)
async def create_yield_prediction(
    prediction_in: YieldPredictionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new yield prediction record.
    
    Prediction methods:
    - statistical: Historical regression
    - process_based: Crop simulation (DSSAT, APSIM)
    - ml_based: Machine learning models
    - hybrid: Combined approaches
    """
    prediction = await prediction_crud.yield_prediction.create(
        db, obj_in=prediction_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(prediction)
    return prediction


@router.delete("/{id}", status_code=204)
async def delete_yield_prediction(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a yield prediction."""
    prediction = await prediction_crud.yield_prediction.get(db, id=id)
    if not prediction or prediction.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Yield prediction not found")
    
    await prediction_crud.yield_prediction.delete(db, id=id)
    await db.commit()
    return None


@router.get("/field/{field_id}", response_model=List[YieldPrediction])
async def get_predictions_by_field(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all yield predictions for a field."""
    predictions = await prediction_crud.yield_prediction.get_by_field(
        db, field_id=field_id, org_id=org_id
    )
    return predictions


@router.get("/field/{field_id}/latest", response_model=YieldPrediction)
async def get_latest_prediction(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get the most recent yield prediction for a field."""
    prediction = await prediction_crud.yield_prediction.get_latest_by_field(
        db, field_id=field_id, org_id=org_id
    )
    if not prediction:
        raise HTTPException(status_code=404, detail="No predictions found for this field")
    return prediction


@router.get("/trial/{trial_id}", response_model=List[YieldPrediction])
async def get_predictions_by_trial(
    trial_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get all yield predictions for a trial."""
    predictions = await prediction_crud.yield_prediction.get_by_trial(
        db, trial_id=trial_id, org_id=org_id
    )
    return predictions
