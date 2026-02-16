"""
Weather Intelligence API
Agricultural weather analysis for Veena AI

Endpoints for weather forecasts, impact analysis, and activity planning.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.weather_service import (
    weather_service,
    WeatherForecast,
    ActivityType
)
from sqlalchemy import select, func
from app.models.core import Location

router = APIRouter(prefix="/weather", tags=["Weather Intelligence"])


@router.get("/forecast/{location_id}", response_model=WeatherForecast)
async def get_weather_forecast(
    location_id: str,
    location_name: str = Query("Location", description="Location display name"),
    days: int = Query(14, ge=1, le=30, description="Forecast days"),
    crop: str = Query("wheat", description="Crop for GDD calculation"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get comprehensive weather forecast with agricultural analysis.
    
    Returns:
    - Daily weather data
    - Impact analysis for breeding activities
    - Optimal activity windows
    - Growing degree days
    - Weather alerts
    """
    # Fetch location coordinates
    stmt = select(func.ST_X(Location.coordinates).label('lon'), func.ST_Y(Location.coordinates).label('lat')).where(Location.location_db_id == location_id)
    result = await db.execute(stmt)
    coords = result.first()

    lat = coords.lat if coords else None
    lon = coords.lon if coords else None

    return await weather_service.get_forecast(
        location_id=location_id,
        location_name=location_name,
        days=days,
        crop=crop,
        lat=lat,
        lon=lon
    )


@router.get("/impacts/{location_id}")
async def get_weather_impacts(
    location_id: str,
    location_name: str = Query("Location"),
    days: int = Query(7, ge=1, le=14),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get weather impact analysis for breeding activities.
    
    Analyzes upcoming weather and identifies potential impacts on:
    - Planting
    - Pollination
    - Spraying
    - Harvesting
    - Field observations
    """
    forecast = await weather_service.get_forecast(
        location_id=location_id,
        location_name=location_name,
        days=days
    )

    return {
        "location_id": location_id,
        "location_name": location_name,
        "analysis_period": f"{days} days",
        "impacts": [
            {
                "date": impact.date.isoformat(),
                "event": impact.event,
                "probability": impact.probability,
                "severity": impact.severity.value,
                "affected_activities": [a.value for a in impact.affected_activities],
                "recommendation": impact.recommendation
            }
            for impact in forecast.impacts
        ],
        "alerts": forecast.alerts,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/activity-windows/{location_id}")
async def get_activity_windows(
    location_id: str,
    location_name: str = Query("Location"),
    activity: Optional[ActivityType] = Query(None, description="Filter by activity type"),
    days: int = Query(14, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Find optimal windows for field activities.
    
    Activities:
    - planting
    - pollination
    - spraying
    - harvesting
    - observation
    - irrigation
    """
    forecast = await weather_service.get_forecast(
        location_id=location_id,
        location_name=location_name,
        days=days
    )

    windows = forecast.optimal_windows
    if activity:
        windows = [w for w in windows if w.activity == activity]

    return {
        "location_id": location_id,
        "location_name": location_name,
        "activity_filter": activity.value if activity else "all",
        "windows": [
            {
                "activity": w.activity.value,
                "start": w.start.isoformat(),
                "end": w.end.isoformat(),
                "confidence": w.confidence,
                "conditions": w.conditions
            }
            for w in windows
        ],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/gdd/{location_id}")
async def get_growing_degree_days(
    location_id: str,
    location_name: str = Query("Location"),
    crop: str = Query("wheat", description="Crop type"),
    days: int = Query(14, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Calculate growing degree days (GDD) forecast.
    
    GDD is used to predict crop development stages.
    Base temperatures vary by crop:
    - Wheat/Barley: 0°C
    - Rice/Maize/Soybean: 10°C
    - Cotton: 15.5°C
    """
    forecast = await weather_service.get_forecast(
        location_id=location_id,
        location_name=location_name,
        days=days,
        crop=crop
    )

    return {
        "location_id": location_id,
        "location_name": location_name,
        "crop": crop,
        "base_temperature": forecast.gdd_forecast[0].base_temp if forecast.gdd_forecast else None,
        "gdd_data": [
            {
                "date": gdd.date.isoformat(),
                "daily_gdd": gdd.gdd_daily,
                "cumulative_gdd": gdd.gdd_cumulative
            }
            for gdd in forecast.gdd_forecast
        ],
        "total_gdd": forecast.gdd_forecast[-1].gdd_cumulative if forecast.gdd_forecast else 0,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/veena/summary/{location_id}")
async def get_veena_weather_summary(
    location_id: str,
    location_name: str = Query("Location"),
    days: int = Query(7, ge=1, le=14),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get natural language weather summary for Veena AI.
    
    Returns a formatted summary that Veena can use to answer
    weather-related questions about breeding activities.
    """
    forecast = await weather_service.get_forecast(
        location_id=location_id,
        location_name=location_name,
        days=days
    )

    summary = weather_service.get_veena_summary(forecast)

    return {
        "location_id": location_id,
        "location_name": location_name,
        "summary": summary,
        "alerts_count": len(forecast.alerts),
        "impacts_count": len(forecast.impacts),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/alerts")
async def get_all_weather_alerts(
    location_ids: str = Query(..., description="Comma-separated location IDs"),
    days: int = Query(7, ge=1, le=14),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get weather alerts for multiple locations.
    
    Useful for monitoring all trial locations at once.
    """
    locations = [loc.strip() for loc in location_ids.split(",")]

    all_alerts = []
    for loc_id in locations:
        forecast = await weather_service.get_forecast(
            location_id=loc_id,
            location_name=f"Location {loc_id}",
            days=days
        )

        for alert in forecast.alerts:
            all_alerts.append({
                "location_id": loc_id,
                "alert": alert
            })

    return {
        "locations_checked": len(locations),
        "total_alerts": len(all_alerts),
        "alerts": all_alerts,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
