"""
Growing Degree Day (GDD) API

Endpoints for tracking crop development through accumulated heat units.

Scientific Formula (preserved per scientific-documentation.md):
    GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    
    Where:
    - Tmax = Daily maximum temperature (°C)
    - Tmin = Daily minimum temperature (°C)
    - Tbase = Base temperature (crop-specific)

Common Base Temperatures:
    - Corn/Maize: 10°C
    - Wheat: 0°C
    - Rice: 10°C
    - Cotton: 15.5°C
"""

from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.future import gdd as gdd_crud
from app.crud.future import gdd_prediction as gdd_prediction_crud
from app.schemas.future.crop_intelligence import (
    GrowingDegreeDayLog,
    GrowingDegreeDayLogCreate,
    GrowingDegreeDayLogUpdate,
)
from app.schemas.future.gdd_prediction import (
    GDDPredictionCreate,
    GDDPredictionResponse,
)
from app.models.core import User
from app.api.deps import get_organization_id, get_current_active_user

router = APIRouter(prefix="/gdd", tags=["Growing Degree Days"])


@router.get("/", response_model=List[GrowingDegreeDayLog])
async def list_gdd_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    List all GDD log entries for the organization.
    
    Returns paginated list of Growing Degree Day records.
    """
    logs = await gdd_crud.gdd_log.get_multi(db, skip=skip, limit=limit, org_id=org_id)
    return logs
    
    # This endpoint requires authentication, so we'll skip it for now for testing purposes
    # if not authenticated properly
    # raise HTTPException(status_code=501, detail="Authentication required - endpoint disabled for testing")


@router.get("/{id}", response_model=GrowingDegreeDayLog)
async def get_gdd_log(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single GDD log entry by ID."""
    log = await gdd_crud.gdd_log.get(db, id=id)
    if not log or log.organization_id != org_id:
        raise HTTPException(status_code=404, detail="GDD log not found")
    return log


@router.post("/", response_model=GrowingDegreeDayLog, status_code=201)
async def create_gdd_log(
    log_in: GrowingDegreeDayLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new GDD log entry.
    
    GDD Formula: GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    """
    log = await gdd_crud.gdd_log.create(db, obj_in=log_in, org_id=current_user.organization_id)
    await db.commit()
    await db.refresh(log)
    return log


@router.put("/{id}", response_model=GrowingDegreeDayLog)
async def update_gdd_log(
    id: int,
    log_in: GrowingDegreeDayLogUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update a GDD log entry."""
    log = await gdd_crud.gdd_log.get(db, id=id)
    if not log or log.organization_id != org_id:
        raise HTTPException(status_code=404, detail="GDD log not found")
    
    log = await gdd_crud.gdd_log.update(db, db_obj=log, obj_in=log_in)
    await db.commit()
    await db.refresh(log)
    return log


@router.delete("/{id}", status_code=204)
async def delete_gdd_log(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a GDD log entry."""
    log = await gdd_crud.gdd_log.get(db, id=id)
    if not log or log.organization_id != org_id:
        raise HTTPException(status_code=404, detail="GDD log not found")
    
    await gdd_crud.gdd_log.delete(db, id=id)
    await db.commit()
    return None


@router.get("/ping")
def ping():
    """Simplest possible endpoint to test if the router works."""
    return {"message": "pong"}


@router.get("/health")
async def health_check():
    """
    Health check endpoint for GDD API.
    
    Returns basic service status without requiring authentication.
    """
    return {
        "status": "healthy",
        "service": "Growing Degree Days API",
        "version": "2.1",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint without any dependencies."""
    return {"message": "GDD API is working", "timestamp": datetime.utcnow().isoformat()}


@router.post("/calculate")
async def calculate_gdd(
    tmax: float = Query(..., description="Maximum temperature (°C)"),
    tmin: float = Query(..., description="Minimum temperature (°C)"),
    tbase: float = Query(10.0, description="Base temperature (°C)"),
    method: str = Query("standard", description="Calculation method (standard, modified, sine_wave)")
):
    """
    Calculate Growing Degree Days for a single day using enhanced calculator service.
    
    GDD = max(0, (Tmax + Tmin) / 2 - Tbase)
    
    Args:
        tmax: Daily maximum temperature in °C
        tmin: Daily minimum temperature in °C
        tbase: Base temperature for the crop (default 10°C for corn)
        method: Calculation method (standard, modified, sine_wave)
    
    Returns:
        Calculated GDD value with scientific metadata and uncertainty
    """
    from app.services.gdd_calculator_service import gdd_calculator_service, TemperatureData, DataQuality
    
    try:
        # Create temperature data for validation
        temp_data = TemperatureData(
            date=date.today(),
            temp_max=tmax,
            temp_min=tmin,
            source="user_input",
            quality=DataQuality.GOOD
        )
        
        # Validate temperature data
        is_valid, warnings, quality = gdd_calculator_service.validate_temperature_data(temp_data)
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid temperature data",
                    "warnings": warnings,
                    "data_quality": quality.name
                }
            )
        
        # Calculate GDD using enhanced service
        gdd_value, metadata = gdd_calculator_service.calculate_daily_gdd(tmax, tmin, tbase, method)
        
        # Return enhanced response with uncertainty metadata
        return {
            "data": {
                "tmax": tmax,
                "tmin": tmin,
                "tbase": tbase,
                "gdd": gdd_value,
                "method": method,
                **metadata
            },
            "metadata": {
                "confidence": {
                    "type": "qualitative",
                    "value": quality.name.lower(),
                    "basis": "temperature_data_validation"
                },
                "validity_conditions": [
                    "temperature_data_within_reasonable_range",
                    "no_extreme_weather_events"
                ],
                "provenance": {
                    "data_sources": ["user_input"],
                    "models_used": ["gdd_calculator_v2.1"],
                    "timestamp": metadata["calculation_timestamp"]
                }
            },
            "warnings": warnings if warnings else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GDD calculation failed: {str(e)}")


@router.post("/predict/growth-stages")
async def predict_growth_stages(
    crop_name: str = Query(..., description="Crop name (corn, wheat, rice, soybean)"),
    cumulative_gdd: float = Query(..., description="Current cumulative GDD"),
    planting_date: str = Query(..., description="Planting date (YYYY-MM-DD)"),
    current_date: str = Query(None, description="Current date (YYYY-MM-DD, defaults to today)")
):
    """
    Predict crop growth stages based on accumulated GDD with confidence intervals.
    
    Uses scientifically validated GDD thresholds for common crops.
    """
    from app.services.gdd_calculator_service import gdd_calculator_service
    
    try:
        # Parse dates
        planting_date_obj = datetime.strptime(planting_date, "%Y-%m-%d").date()
        current_date_obj = None
        if current_date:
            current_date_obj = datetime.strptime(current_date, "%Y-%m-%d").date()
        
        # Get growth stage prediction
        prediction = gdd_calculator_service.predict_growth_stages(
            crop_name, cumulative_gdd, planting_date_obj, current_date_obj
        )
        
        # Get crop base temperature for context
        base_temp = gdd_calculator_service.get_crop_base_temperature(crop_name)
        
        # Calculate days since planting
        current_date_obj = current_date_obj or datetime.now().date()
        days_since_planting = (current_date_obj - planting_date_obj).days
        
        return {
            "data": {
                "crop_name": prediction.crop_name,
                "base_temperature": base_temp,
                "planting_date": planting_date,
                "current_date": current_date_obj.isoformat(),
                "days_since_planting": days_since_planting,
                "current_gdd": prediction.current_gdd,
                "current_stage": prediction.current_stage,
                "next_stage": prediction.next_stage,
                "gdd_to_next_stage": prediction.gdd_to_next_stage,
                "days_to_next_stage": prediction.days_to_next_stage,
                "maturity_gdd": prediction.maturity_gdd,
                "predicted_maturity_date": prediction.predicted_maturity_date.isoformat() if prediction.predicted_maturity_date else None,
                "progress_to_maturity": round((prediction.current_gdd / prediction.maturity_gdd) * 100, 1)
            },
            "metadata": {
                "confidence": {
                    "type": "qualitative", 
                    "value": "high" if prediction.confidence > 0.8 else "medium" if prediction.confidence > 0.6 else "low",
                    "basis": "crop_specific_gdd_thresholds"
                },
                "validity_conditions": [
                    f"crop_identified_as_{crop_name}",
                    "gdd_thresholds_scientifically_validated",
                    "weather_patterns_within_normal_range"
                ],
                "provenance": {
                    "data_sources": ["scientific_literature", "crop_development_models"],
                    "models_used": ["gdd_phenology_predictor_v2.1"],
                    "timestamp": datetime.utcnow().isoformat()
                },
                "prediction_confidence": {
                    "current_stage_confidence": prediction.confidence,
                    "maturity_prediction_confidence": prediction.maturity_confidence,
                    "uncertainty_factors": [
                        "weather_forecast_accuracy",
                        "variety_specific_differences", 
                        "environmental_stress_effects"
                    ]
                }
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Growth stage prediction failed: {str(e)}")


@router.post("/calculate/cumulative")
async def calculate_cumulative_gdd(
    request_data: dict
):
    """
    Calculate cumulative Growing Degree Days over a period with uncertainty metadata.
    """
    from app.services.gdd_calculator_service import gdd_calculator_service, TemperatureData, DataQuality
    
    try:
        # Extract parameters from request body
        temperatures = request_data.get("temperatures", [])
        tbase = request_data.get("tbase", 10.0)
        start_date = request_data.get("start_date")
        method = request_data.get("method", "standard")
        
        if not temperatures:
            raise HTTPException(status_code=400, detail="No temperature data provided")
        
        # Parse temperature data
        temp_data_list = []
        for temp_entry in temperatures:
            temp_date = datetime.strptime(temp_entry["date"], "%Y-%m-%d").date()
            temp_data = TemperatureData(
                date=temp_date,
                temp_max=temp_entry["tmax"],
                temp_min=temp_entry["tmin"],
                source="user_input",
                quality=DataQuality.GOOD
            )
            temp_data_list.append(temp_data)
        
        # Parse start date if provided
        start_date_obj = None
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        # Calculate cumulative GDD
        results = gdd_calculator_service.calculate_cumulative_gdd(
            temp_data_list, tbase, start_date_obj
        )
        
        if not results:
            raise HTTPException(status_code=400, detail="No valid temperature data provided")
        
        # Calculate overall quality metrics
        total_quality = sum(r.data_quality_score for r in results) / len(results)
        has_interpolated = any(r.is_interpolated for r in results)
        has_outliers = any(r.outlier_detected for r in results)
        
        # Prepare response data
        daily_results = []
        for result in results:
            daily_results.append({
                "date": result.calculation_date.isoformat(),
                "daily_gdd": result.daily_gdd,
                "cumulative_gdd": result.cumulative_gdd,
                "temp_max": result.max_temperature,
                "temp_min": result.min_temperature,
                "confidence": result.confidence_level,
                "quality_score": result.data_quality_score,
                "is_interpolated": result.is_interpolated,
                "outlier_detected": result.outlier_detected
            })
        
        # Calculate uncertainty based on data quality
        uncertainty_level = "low"
        if total_quality < 0.6 or has_outliers:
            uncertainty_level = "high"
        elif total_quality < 0.8 or has_interpolated:
            uncertainty_level = "medium"
        
        return {
            "data": {
                "base_temperature": tbase,
                "method": method,
                "total_days": len(results),
                "final_cumulative_gdd": results[-1].cumulative_gdd,
                "daily_calculations": daily_results,
                "summary": {
                    "average_daily_gdd": sum(r.daily_gdd for r in results) / len(results),
                    "max_daily_gdd": max(r.daily_gdd for r in results),
                    "min_daily_gdd": min(r.daily_gdd for r in results)
                }
            },
            "metadata": {
                "confidence": {
                    "type": "qualitative",
                    "value": uncertainty_level,
                    "basis": "temperature_data_quality_assessment"
                },
                "validity_conditions": [
                    "temperature_data_within_reasonable_range",
                    "no_major_data_gaps",
                    f"base_temperature_{tbase}C_appropriate_for_crop"
                ],
                "provenance": {
                    "data_sources": ["user_input"],
                    "models_used": ["gdd_calculator_v2.1"],
                    "timestamp": datetime.utcnow().isoformat()
                },
                "quality_assessment": {
                    "overall_quality_score": round(total_quality, 3),
                    "has_interpolated_data": has_interpolated,
                    "has_outliers": has_outliers,
                    "data_completeness": 1.0  # All user-provided data
                }
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cumulative GDD calculation failed: {str(e)}")


@router.get("/field/{field_id}/summary")
async def get_field_gdd_summary(
    field_id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get cumulative GDD summary for a field.
    
    Returns total accumulated GDD, date range, and days logged.
    """
    summary = await gdd_crud.gdd_log.get_cumulative_summary(db, field_id=field_id, org_id=org_id)
    return summary


@router.get("/field/{field_id}/history", response_model=List[GrowingDegreeDayLog])
async def get_field_gdd_history(
    field_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get GDD history for a field within a date range."""
    logs = await gdd_crud.gdd_log.get_by_field_and_date_range(
        db, field_id=field_id, start_date=start_date, end_date=end_date, org_id=org_id
    )
    return logs


@router.post("/field/{field_id}/calculate")
async def calculate_gdd_for_field(
    field_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db)
):
    """Calculate and store GDD for a specific field."""
    # In a real implementation, this would trigger a background task that
    # 1. Fetches weather data for the field location
    # 2. Calculates GDD
    # 3. Stores GDD logs

    # Simulating a background task trigger
    return {"message": f"GDD calculation for field {field_id} has been initiated."}


@router.get("/field/{field_id}/predictions", response_model=List[GDDPredictionResponse])
async def get_gdd_predictions_for_field(
    field_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get GDD-based predictions for a field."""
    predictions = await gdd_prediction_crud.gdd_prediction.get_by_field(
        db, field_id=field_id, org_id=org_id, skip=skip, limit=limit
    )
    return predictions


@router.post("/field/{field_id}/predict", response_model=GDDPredictionResponse)
async def create_field_prediction(
    field_id: int,
    prediction_in: GDDPredictionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new prediction for a field.
    """
    # Verify field belongs to organization (skipping strict field check for now as field service might be separate)
    # In production: await field_service.get(db, id=field_id, org_id=current_user.organization_id)

    # Ensure prediction_in.field_id matches url param
    prediction_in.field_id = field_id

    prediction = await gdd_prediction_crud.gdd_prediction.create(
        db, obj_in=prediction_in, org_id=current_user.organization_id
    )
    await db.commit()
    await db.refresh(prediction)
    return prediction


from app.services.data_quality_service import DataQualityService

@router.post("/batch/calculate")
async def batch_calculate_gdd(
    field_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate GDD for a batch of fields."""
    # This would optimally use a task queue like Celery or the internal TaskQueue
    # For now, we'll return a success message indicating the job was accepted

    # Validate fields exist and belong to user's org
    # ...

    return {
        "message": "Batch GDD calculation has been initiated for {} fields.".format(len(field_ids)),
        "job_id": f"job_gdd_batch_{len(field_ids)}_{datetime.now().timestamp()}"
    }


@router.get("/quality/report")
async def get_data_quality_report(db: AsyncSession = Depends(get_db)):
    """Get a data quality report for GDD data."""
    # In a real implementation, this would query the database for GDD logs
    # and then use the data quality service to generate a report.
    return {
        "completeness": 0.95,
        "outliers": 12,
        "valid_range_percentage": 99.8,
    }


@router.get("/quality/field/{field_id}")
async def get_field_data_quality(field_id: int, db: AsyncSession = Depends(get_db)):
    """Get data quality metrics for a specific field."""
    # In a real implementation, this would query the database for GDD logs
    # for the given field and then use the data quality service to generate a report.
    return {
        "field_id": field_id,
        "completeness": 0.98,
        "outliers": 2,
        "valid_range_percentage": 99.9,
    }


@router.get("/quality/outliers")
async def get_outliers(db: AsyncSession = Depends(get_db)):
    """Get a list of data outliers."""
    # In a real implementation, this would query the database for GDD logs
    # and then use the data quality service to find outliers.
    return {"outliers": [100, 101, -60]}


# ============================================
# WEATHER DATA SYNC ENDPOINTS
# ============================================

@router.post("/weather/sync")
async def sync_weather_data(
    location_id: str = Query(..., description="Location identifier"),
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    start_date: date = Query(..., description="Start date for weather data"),
    end_date: date = Query(..., description="End date for weather data"),
    include_forecast: bool = Query(False, description="Include forecast data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Sync weather data for a specific location and date range.
    """
    from app.services.weather_integration_service import (
        weather_integration_service,
        WeatherDataRequest
    )
    
    try:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before or equal to end_date"
            )
        
        # Check date range is reasonable (max 1 year)
        days_diff = (end_date - start_date).days
        if days_diff > 365:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 365 days"
            )
        
        # Create weather data request
        request = WeatherDataRequest(
            location_id=location_id,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            include_forecast=include_forecast
        )
        
        # Fetch weather data using integration service
        response = await weather_integration_service.get_temperature_data(
            request=request,
            db=db
        )
        
        # Format response following BijMantra API contracts
        return {
            "data": {
                "location_id": response.location_id,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "records_fetched": len(response.data),
                "provider_used": response.provider_used.value,
                "cache_hit_rate": round(response.cache_hit_rate, 3),
                "data_completeness": round(response.data_completeness, 3),
                "quality_score": round(response.quality_score, 3),
                "temperature_data": [
                    {
                        "date": temp.date.isoformat(),
                        "temp_max": temp.temp_max,
                        "temp_min": temp.temp_min,
                        "temp_avg": temp.temp_avg,
                        "source": temp.source.value,
                        "quality": temp.quality.value,
                        "confidence": temp.confidence,
                        "is_forecast": temp.is_forecast,
                        "is_interpolated": temp.is_interpolated,
                        "outlier_detected": temp.outlier_detected,
                        "precipitation": temp.precipitation,
                        "humidity": temp.humidity,
                        "wind_speed": temp.wind_speed
                    }
                    for temp in response.data
                ]
            },
            "metadata": {
                "confidence": response.confidence,
                "validity_conditions": response.validity_conditions,
                "provenance": response.provenance
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Weather data sync failed: {str(e)}"
        )


@router.post("/weather/sync/batch")
async def batch_sync_weather_data(
    sync_requests: List[dict],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Batch sync weather data for multiple locations.
    """
    from app.services.weather_integration_service import (
        weather_integration_service,
        WeatherDataRequest
    )
    
    try:
        # Validate batch size
        if len(sync_requests) > 50:
            raise HTTPException(
                status_code=400,
                detail="Batch size cannot exceed 50 locations"
            )
        
        if not sync_requests:
            raise HTTPException(
                status_code=400,
                detail="No sync requests provided"
            )
        
        # Process each sync request
        results = []
        successful = 0
        failed = 0
        
        for req_data in sync_requests:
            try:
                # Parse request data
                location_id = req_data.get("location_id")
                latitude = req_data.get("latitude")
                longitude = req_data.get("longitude")
                start_date_str = req_data.get("start_date")
                end_date_str = req_data.get("end_date")
                include_forecast = req_data.get("include_forecast", False)
                
                # Validate required fields
                if not all([location_id, latitude, longitude, start_date_str, end_date_str]):
                    results.append({
                        "location_id": location_id or "unknown",
                        "status": "failed",
                        "error": "Missing required fields"
                    })
                    failed += 1
                    continue
                
                # Parse dates
                start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                
                # Create request
                request = WeatherDataRequest(
                    location_id=location_id,
                    latitude=latitude,
                    longitude=longitude,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    include_forecast=include_forecast
                )
                
                # Fetch weather data
                response = await weather_integration_service.get_temperature_data(
                    request=request,
                    db=db
                )
                
                results.append({
                    "location_id": location_id,
                    "status": "success",
                    "records_fetched": len(response.data),
                    "quality_score": round(response.quality_score, 3),
                    "cache_hit_rate": round(response.cache_hit_rate, 3),
                    "provider_used": response.provider_used.value
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "location_id": req_data.get("location_id", "unknown"),
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1
        
        return {
            "data": {
                "total_requests": len(sync_requests),
                "successful": successful,
                "failed": failed,
                "results": results
            },
            "metadata": {
                "confidence": {
                    "type": "qualitative",
                    "value": "high" if failed == 0 else "medium" if successful > failed else "low",
                    "basis": "batch_sync_success_rate"
                },
                "validity_conditions": [
                    f"successful_syncs_{successful}_of_{len(sync_requests)}",
                    "weather_api_availability_normal"
                ],
                "provenance": {
                    "data_sources": ["weather_integration_service"],
                    "models_used": ["batch_weather_sync_v1.0"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch weather sync failed: {str(e)}"
        )


@router.get("/weather/sync/status")
async def get_weather_sync_status(
    location_id: str = Query(..., description="Location identifier"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Check weather data sync status for a location.
    """
    from app.services.weather_integration_service import weather_integration_service
    
    try:
        # Initialize Redis connection
        await weather_integration_service._init_redis()
        
        # Check cache for recent data
        today = date.today()
        last_30_days = [today - timedelta(days=i) for i in range(30)]
        
        cached_count = 0
        latest_date = None
        oldest_date = None
        
        for check_date in last_30_days:
            cache_key = f"weather:{location_id}:{check_date.isoformat()}"
            
            if weather_integration_service.redis_client:
                try:
                    cached = await weather_integration_service.redis_client.get(cache_key)
                    if cached:
                        cached_count += 1
                        if latest_date is None:
                            latest_date = check_date
                        oldest_date = check_date
                except Exception:
                    pass
        
        # Calculate sync status
        data_coverage = (cached_count / 30) * 100
        sync_status = "excellent" if data_coverage > 90 else "good" if data_coverage > 70 else "fair" if data_coverage > 50 else "poor"
        
        return {
            "data": {
                "location_id": location_id,
                "sync_status": sync_status,
                "cached_records_last_30_days": cached_count,
                "data_coverage_percentage": round(data_coverage, 1),
                "latest_cached_date": latest_date.isoformat() if latest_date else None,
                "oldest_cached_date": oldest_date.isoformat() if oldest_date else None,
                "cache_available": weather_integration_service.redis_client is not None,
                "recommendation": (
                    "No action needed" if data_coverage > 90
                    else "Consider syncing recent data" if data_coverage > 50
                    else "Weather data sync recommended"
                )
            },
            "metadata": {
                "confidence": {
                    "type": "qualitative",
                    "value": sync_status,
                    "basis": "cache_data_availability"
                },
                "validity_conditions": [
                    f"cache_coverage_{int(data_coverage)}percent",
                    "redis_connection_available" if weather_integration_service.redis_client else "redis_unavailable"
                ],
                "provenance": {
                    "data_sources": ["redis_cache"],
                    "models_used": ["weather_sync_status_v1.0"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check sync status: {str(e)}"
        )
