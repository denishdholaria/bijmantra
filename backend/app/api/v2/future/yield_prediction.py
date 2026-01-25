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

from typing import List, Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.future import yield_prediction as prediction_crud
from app.schemas.future.crop_intelligence import (
    YieldPrediction,
    YieldPredictionCreate,
)
from app.models.core import User
from app.services.yield_prediction.ensemble import EnsemblePredictor
from app.services.yield_prediction.attribution import FactorAttribution

router = APIRouter(prefix="/yield-prediction", tags=["Yield Prediction"])


class YieldPredictionRequest(BaseModel):
    """Request schema for generating a new yield prediction."""
    field_id: int
    crop_name: str
    season: str
    target_year: int
    planting_date: date
    features: Optional[Dict[str, Any]] = None


@router.post("/predict", response_model=Dict[str, Any])
async def generate_prediction(
    request: YieldPredictionRequest,
    save: bool = Query(False, description="Whether to save the prediction to database"),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a new yield prediction using the Hybrid Ensemble method.

    This endpoint runs the ensemble of Statistical, Process-Based, and ML models
    to generate a scientifically rigorous yield prediction with uncertainty quantification
    and factor attribution.
    """
    predictor = EnsemblePredictor()

    # Run prediction
    result = await predictor.predict(
        db,
        request.field_id,
        request.crop_name,
        request.planting_date,
        request.target_year,
        org_id,
        request.features
    )

    if result.get("status") != "success":
         # Return partial result with error info or 400
         # Using 400 if it failed completely
         raise HTTPException(status_code=400, detail=result.get("message", "Prediction failed"))

    # Analyze Attribution
    attributor = FactorAttribution()
    attribution = await attributor.analyze(
        db,
        result,
        request.field_id,
        request.crop_name,
        request.features or {}
    )

    result["attribution"] = attribution

    if save:
        # Create YieldPrediction object
        try:
            obj_in = YieldPredictionCreate(
                field_id=request.field_id,
                crop_name=request.crop_name,
                season=request.season,
                predicted_yield=result["predicted_yield"],
                yield_unit="t/ha",
                prediction_date=date.today(),
                lower_bound=result.get("lower_bound"),
                upper_bound=result.get("upper_bound"),
                confidence_level=result.get("confidence_level", 0.95),
                model_name="HybridEnsemble",
                model_version="1.0",
                prediction_method="hybrid",
                weather_factors={"attribution": attribution.get("environmental_contribution")},
                soil_factors={"attribution": attribution.get("environmental_contribution")},
                management_factors={"attribution": attribution.get("management_contribution")},
                notes=f"Generated via API. Methods: {result.get('method_contributions')}"
            )

            prediction = await prediction_crud.yield_prediction.create(
                 db, obj_in=obj_in, org_id=org_id
            )
            await db.commit()
            result["saved_prediction_id"] = prediction.id
        except Exception as e:
            # Don't fail the request if saving fails, but warn
            result["save_error"] = str(e)

    return result


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
    Create a new yield prediction record manually.
    
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
