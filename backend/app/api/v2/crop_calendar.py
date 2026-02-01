"""
Crop Calendar API for Plant Breeding
Planting schedules, growth stages, and activity planning

Endpoints:
- GET /api/v2/crop-calendar/crops - List crop profiles
- POST /api/v2/crop-calendar/crops - Register crop profile
- POST /api/v2/crop-calendar/events - Create planting event
- GET /api/v2/crop-calendar/events - List planting events
- GET /api/v2/crop-calendar/growth-stage/{event_id} - Get growth stage
- POST /api/v2/crop-calendar/gdd - Calculate GDD
- GET /api/v2/crop-calendar/activities - Get upcoming activities
- POST /api/v2/crop-calendar/activities/{id}/complete - Complete activity
- GET /api/v2/crop-calendar/view - Calendar view
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from app.services.crop_calendar import get_crop_calendar_service

router = APIRouter(prefix="/crop-calendar", tags=["Crop Calendar"])


# ============================================
# SCHEMAS
# ============================================

class CropProfileRequest(BaseModel):
    """Request to register a crop profile"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "crop_id": "tomato",
            "name": "Tomato",
            "species": "Solanum lycopersicum",
            "days_to_maturity": 90,
            "base_temperature": 10.0,
            "optimal_temp_min": 20.0,
            "optimal_temp_max": 30.0,
            "growth_stages": {
                "germination": 7,
                "seedling": 21,
                "vegetative": 40,
                "flowering": 55,
                "fruiting": 75,
                "maturity": 90
            }
        }
    })

    crop_id: str = Field(..., description="Unique crop ID")
    name: str = Field(..., description="Crop name")
    species: str = Field(..., description="Species name")
    days_to_maturity: int = Field(..., ge=30, le=365, description="Days to maturity")
    base_temperature: float = Field(..., description="Base temperature for GDD (°C)")
    optimal_temp_min: float = Field(..., description="Optimal min temperature (°C)")
    optimal_temp_max: float = Field(..., description="Optimal max temperature (°C)")
    growth_stages: Dict[str, int] = Field(..., description="Stage name -> days from sowing")


class PlantingEventRequest(BaseModel):
    """Request to create a planting event"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "crop_id": "rice_short",
            "trial_id": "TRIAL-2025-001",
            "sowing_date": "2025-06-15",
            "location": "Field A",
            "area_hectares": 2.5,
            "notes": "Kharif season trial"
        }
    })

    crop_id: str = Field(..., description="Crop profile ID")
    trial_id: str = Field(..., description="Associated trial ID")
    sowing_date: str = Field(..., description="Sowing date (YYYY-MM-DD)")
    location: str = Field(..., description="Field/location name")
    area_hectares: float = Field(..., gt=0, description="Area in hectares")
    notes: str = Field("", description="Additional notes")


class GDDRequest(BaseModel):
    """Request for GDD calculation"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "crop_id": "rice_short",
            "daily_temps": [
                {"date": "2025-06-15", "temp_max": 35.0, "temp_min": 25.0},
                {"date": "2025-06-16", "temp_max": 34.0, "temp_min": 24.0},
                {"date": "2025-06-17", "temp_max": 36.0, "temp_min": 26.0}
            ]
        }
    })

    crop_id: str = Field(..., description="Crop profile ID")
    daily_temps: List[Dict[str, float]] = Field(..., description="List of {date, temp_max, temp_min}")


class CompleteActivityRequest(BaseModel):
    """Request to complete an activity"""
    notes: str = Field("", description="Completion notes")


# ============================================
# ENDPOINTS
# ============================================

@router.get("/crops")
async def list_crops():
    """
    List all crop profiles
    
    Returns pre-configured profiles for common crops plus any custom profiles.
    """
    service = get_crop_calendar_service()
    crops = service.list_crops()
    
    return {
        "success": True,
        "count": len(crops),
        "crops": crops,
    }


@router.post("/crops")
async def register_crop(request: CropProfileRequest):
    """
    Register a new crop profile
    
    Define growth stages and temperature requirements for a crop.
    """
    service = get_crop_calendar_service()
    
    try:
        profile = service.register_crop(
            crop_id=request.crop_id,
            name=request.name,
            species=request.species,
            days_to_maturity=request.days_to_maturity,
            base_temperature=request.base_temperature,
            optimal_temp_min=request.optimal_temp_min,
            optimal_temp_max=request.optimal_temp_max,
            growth_stages=request.growth_stages,
        )
        
        return {
            "success": True,
            "message": f"Crop profile {request.crop_id} registered",
            **profile.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register crop: {str(e)}")


@router.post("/events")
async def create_planting_event(request: PlantingEventRequest):
    """
    Create a planting event
    
    Automatically:
    - Calculates expected harvest date
    - Generates scheduled activities (observations, fertilization, harvest)
    """
    service = get_crop_calendar_service()
    
    try:
        event = service.create_planting_event(
            crop_id=request.crop_id,
            trial_id=request.trial_id,
            sowing_date=request.sowing_date,
            location=request.location,
            area_hectares=request.area_hectares,
            notes=request.notes,
        )
        
        return {
            "success": True,
            "message": f"Planting event {event.event_id} created",
            **event.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to create event: {str(e)}")


@router.get("/events")
async def list_events(
    crop_id: Optional[str] = Query(None, description="Filter by crop"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """List planting events with optional filters"""
    service = get_crop_calendar_service()
    
    events = service.list_events(crop_id=crop_id, location=location)
    
    return {
        "success": True,
        "count": len(events),
        "filters": {"crop_id": crop_id, "location": location},
        "events": events,
    }


@router.get("/growth-stage/{event_id}")
async def get_growth_stage(
    event_id: str,
    check_date: Optional[str] = Query(None, description="Date to check (default: today)")
):
    """
    Get current growth stage for a planting event
    
    Returns:
    - Current growth stage
    - Days after sowing
    - Progress percentage
    - Days to expected harvest
    """
    service = get_crop_calendar_service()
    
    try:
        result = service.get_growth_stage(event_id, check_date)
        return {
            "success": True,
            **result,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/gdd")
async def calculate_gdd(request: GDDRequest):
    """
    Calculate Growing Degree Days (GDD)
    
    GDD = max(0, (Tmax + Tmin)/2 - Tbase)
    
    Used to predict crop development based on accumulated heat units.
    """
    service = get_crop_calendar_service()
    
    try:
        result = service.calculate_gdd(request.crop_id, request.daily_temps)
        return {
            "success": True,
            **result,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/activities")
async def get_upcoming_activities(
    days_ahead: int = Query(14, ge=1, le=90, description="Days to look ahead"),
    event_id: Optional[str] = Query(None, description="Filter by planting event")
):
    """
    Get upcoming scheduled activities
    
    Returns activities within the specified number of days.
    """
    service = get_crop_calendar_service()
    
    activities = service.get_upcoming_activities(days_ahead, event_id)
    
    return {
        "success": True,
        "days_ahead": days_ahead,
        "count": len(activities),
        "activities": activities,
    }


@router.post("/activities/{activity_id}/complete")
async def complete_activity(activity_id: str, request: CompleteActivityRequest):
    """Mark an activity as completed"""
    service = get_crop_calendar_service()
    
    try:
        activity = service.complete_activity(activity_id, request.notes)
        return {
            "success": True,
            "message": f"Activity {activity_id} completed",
            **activity.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/view")
async def get_calendar_view(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Get calendar view of events and activities
    
    Returns a day-by-day view of all planting events and scheduled activities.
    """
    service = get_crop_calendar_service()
    
    try:
        result = service.get_calendar_view(start_date, end_date)
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to generate calendar: {str(e)}")


@router.get("/growth-stages")
async def list_growth_stages():
    """List standard growth stages"""
    return {
        "growth_stages": [
            {"id": "germination", "name": "Germination", "description": "Seed emergence"},
            {"id": "seedling", "name": "Seedling", "description": "Early plant establishment"},
            {"id": "vegetative", "name": "Vegetative", "description": "Leaf and stem growth"},
            {"id": "flowering", "name": "Flowering", "description": "Reproductive stage"},
            {"id": "grain_filling", "name": "Grain Filling", "description": "Seed development"},
            {"id": "maturity", "name": "Maturity", "description": "Physiological maturity"},
            {"id": "harvest", "name": "Harvest", "description": "Ready for harvest"},
        ]
    }
