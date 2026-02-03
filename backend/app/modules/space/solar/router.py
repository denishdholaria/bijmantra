"""
Solar & Sun-Earth Systems API

Endpoints for solar radiation, photoperiod, UV index, and space weather data.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.solar import get_solar_service

router = APIRouter(tags=["Sun-Earth Systems"])


class PhotoperiodRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    date: Optional[str] = Field(None, description="Date (YYYY-MM-DD), defaults to today")


class RadiationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    date: Optional[str] = None
    cloud_cover: float = Field(0.3, ge=0, le=1, description="Cloud cover fraction (0-1)")


class UVIndexRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    date: Optional[str] = None
    elevation: float = Field(0, ge=0, description="Elevation in meters")
    cloud_cover: float = Field(0.3, ge=0, le=1)


@router.get("/current")
async def get_current_conditions():
    """Get current solar and space weather conditions."""
    service = get_solar_service()
    return {
        "success": True,
        "data": service.get_current_solar_conditions(),
    }


@router.get("/forecast")
async def get_solar_forecast(
    days: int = Query(7, ge=1, le=30, description="Number of days to forecast"),
):
    """Get solar activity forecast."""
    service = get_solar_service()
    return {
        "success": True,
        "data": service.get_solar_forecast(days),
    }


@router.get("/magnetic")
async def get_geomagnetic_data():
    """Get current geomagnetic field data."""
    service = get_solar_service()
    return {
        "success": True,
        "data": service.get_geomagnetic_data(),
    }


@router.post("/photoperiod")
async def calculate_photoperiod(request: PhotoperiodRequest):
    """Calculate day length (photoperiod) for a location and date."""
    service = get_solar_service()
    target_date = date.fromisoformat(request.date) if request.date else None
    return {
        "success": True,
        "data": service.calculate_photoperiod(request.latitude, target_date),
    }


@router.get("/photoperiod")
async def get_photoperiod(
    latitude: float = Query(..., ge=-90, le=90),
    target_date: Optional[str] = Query(None, alias="date"),
):
    """Calculate day length (photoperiod) for a location and date."""
    service = get_solar_service()
    d = date.fromisoformat(target_date) if target_date else None
    return {
        "success": True,
        "data": service.calculate_photoperiod(latitude, d),
    }


@router.get("/photoperiod/series")
async def get_photoperiod_series(
    latitude: float = Query(..., ge=-90, le=90),
    days: int = Query(365, ge=1, le=730),
):
    """Get photoperiod data for a series of dates (annual cycle)."""
    service = get_solar_service()
    return {
        "success": True,
        "data": service.get_photoperiod_series(latitude, days=days),
    }


@router.post("/radiation")
async def calculate_radiation(request: RadiationRequest):
    """Estimate daily solar radiation for a location."""
    service = get_solar_service()
    target_date = date.fromisoformat(request.date) if request.date else None
    return {
        "success": True,
        "data": service.calculate_solar_radiation(
            request.latitude, target_date, request.cloud_cover
        ),
    }


@router.get("/radiation")
async def get_radiation(
    latitude: float = Query(..., ge=-90, le=90),
    target_date: Optional[str] = Query(None, alias="date"),
    cloud_cover: float = Query(0.3, ge=0, le=1),
):
    """Estimate daily solar radiation for a location."""
    service = get_solar_service()
    d = date.fromisoformat(target_date) if target_date else None
    return {
        "success": True,
        "data": service.calculate_solar_radiation(latitude, d, cloud_cover),
    }


@router.post("/uv-index")
async def calculate_uv_index(request: UVIndexRequest):
    """Estimate UV index for a location."""
    service = get_solar_service()
    target_date = date.fromisoformat(request.date) if request.date else None
    return {
        "success": True,
        "data": service.get_uv_index(
            request.latitude, target_date, request.elevation, request.cloud_cover
        ),
    }


@router.get("/uv-index")
async def get_uv_index(
    latitude: float = Query(..., ge=-90, le=90),
    target_date: Optional[str] = Query(None, alias="date"),
    elevation: float = Query(0, ge=0),
    cloud_cover: float = Query(0.3, ge=0, le=1),
):
    """Estimate UV index for a location."""
    service = get_solar_service()
    d = date.fromisoformat(target_date) if target_date else None
    return {
        "success": True,
        "data": service.get_uv_index(latitude, d, elevation, cloud_cover),
    }


@router.get("/agricultural-impacts")
async def get_agricultural_impacts():
    """Get information about solar impacts on agriculture."""
    return {
        "success": True,
        "data": {
            "photoperiod_effects": [
                {
                    "category": "Short-Day Plants",
                    "examples": ["Rice", "Soybean", "Chrysanthemum"],
                    "flowering_trigger": "Day length < 12-14 hours",
                    "description": "Flower when nights are long",
                },
                {
                    "category": "Long-Day Plants",
                    "examples": ["Wheat", "Barley", "Spinach", "Lettuce"],
                    "flowering_trigger": "Day length > 14-16 hours",
                    "description": "Flower when days are long",
                },
                {
                    "category": "Day-Neutral Plants",
                    "examples": ["Tomato", "Corn", "Cucumber"],
                    "flowering_trigger": "Independent of day length",
                    "description": "Flower based on age/size",
                },
            ],
            "solar_radiation_effects": [
                {
                    "factor": "PAR (Photosynthetically Active Radiation)",
                    "impact": "Direct driver of photosynthesis",
                    "optimal_range": "400-700 nm wavelength",
                },
                {
                    "factor": "UV-B Radiation",
                    "impact": "Can damage DNA, affects secondary metabolites",
                    "plant_response": "Increased flavonoids, anthocyanins",
                },
                {
                    "factor": "Total Solar Irradiance",
                    "impact": "Affects temperature, evapotranspiration",
                    "consideration": "Varies with solar cycle (~0.1%)",
                },
            ],
            "geomagnetic_effects": [
                {
                    "phenomenon": "Geomagnetic Storms",
                    "potential_impact": "May affect plant growth orientation",
                    "research_status": "Under investigation",
                },
                {
                    "phenomenon": "Cosmic Ray Flux",
                    "potential_impact": "Natural mutation source",
                    "research_status": "Documented in space biology",
                },
            ],
        },
    }
