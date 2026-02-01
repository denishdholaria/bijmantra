"""
Space Research API

Endpoints for interplanetary agriculture research data and calculations.
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.space_research import get_space_research_service

router = APIRouter(tags=["Space Research"])


class RadiationRequest(BaseModel):
    mission_type: str = Field(..., description="LEO, lunar, mars, or deep_space")
    duration_days: int = Field(..., ge=1, le=1000)
    shielding_gcm2: float = Field(20, ge=0, le=100)


class LifeSupportRequest(BaseModel):
    crew_size: int = Field(..., ge=1, le=20)
    mission_days: int = Field(..., ge=1, le=1000)
    crop_area_m2: float = Field(..., ge=0, le=1000)


@router.get("/crops")
async def get_space_crops():
    """Get list of crops suitable for space agriculture."""
    service = get_space_research_service()
    return {
        "success": True,
        "data": service.get_space_crops(),
        "count": len(service.get_space_crops()),
    }


@router.get("/crops/{crop_id}")
async def get_space_crop(crop_id: str):
    """Get details of a specific space crop."""
    service = get_space_research_service()
    crop = service.get_space_crop(crop_id)
    if not crop:
        return {"success": False, "error": "Crop not found"}
    return {"success": True, "data": crop}


@router.get("/crops/{crop_id}/environment")
async def get_crop_environment(crop_id: str):
    """Get optimal controlled environment parameters for a space crop."""
    service = get_space_research_service()
    params = service.get_controlled_environment_params(crop_id)
    return {"success": True, "data": params}


@router.get("/experiments")
async def get_experiments(
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """Get list of space agriculture experiments."""
    service = get_space_research_service()
    experiments = service.get_experiments(status)
    return {
        "success": True,
        "data": experiments,
        "count": len(experiments),
    }


@router.get("/experiments/{exp_id}")
async def get_experiment(exp_id: str):
    """Get details of a specific experiment."""
    service = get_space_research_service()
    exp = service.get_experiment(exp_id)
    if not exp:
        return {"success": False, "error": "Experiment not found"}
    return {"success": True, "data": exp}


@router.post("/radiation")
async def calculate_radiation(request: RadiationRequest):
    """Calculate radiation exposure for a space mission."""
    service = get_space_research_service()
    result = service.calculate_radiation_exposure(
        request.mission_type,
        request.duration_days,
        request.shielding_gcm2,
    )
    return {"success": True, "data": result}


@router.get("/radiation")
async def get_radiation(
    mission_type: str = Query(..., description="LEO, lunar, mars, deep_space"),
    duration_days: int = Query(..., ge=1, le=1000),
    shielding_gcm2: float = Query(20, ge=0, le=100),
):
    """Calculate radiation exposure for a space mission."""
    service = get_space_research_service()
    result = service.calculate_radiation_exposure(
        mission_type, duration_days, shielding_gcm2
    )
    return {"success": True, "data": result}


@router.post("/life-support")
async def calculate_life_support(request: LifeSupportRequest):
    """Calculate life support requirements with crop contributions."""
    service = get_space_research_service()
    result = service.calculate_life_support_requirements(
        request.crew_size,
        request.mission_days,
        request.crop_area_m2,
    )
    return {"success": True, "data": result}


@router.get("/life-support")
async def get_life_support(
    crew_size: int = Query(..., ge=1, le=20),
    mission_days: int = Query(..., ge=1, le=1000),
    crop_area_m2: float = Query(..., ge=0, le=1000),
):
    """Calculate life support requirements with crop contributions."""
    service = get_space_research_service()
    result = service.calculate_life_support_requirements(
        crew_size, mission_days, crop_area_m2
    )
    return {"success": True, "data": result}


@router.get("/missions")
async def get_mission_profiles():
    """Get predefined space mission profiles."""
    service = get_space_research_service()
    return {
        "success": True,
        "data": service.get_mission_profiles(),
    }


@router.get("/agencies")
async def get_space_agencies():
    """Get list of space agencies with agriculture programs."""
    return {
        "success": True,
        "data": [
            {
                "id": "NASA",
                "name": "National Aeronautics and Space Administration",
                "country": "USA",
                "programs": ["Veggie", "APH (Advanced Plant Habitat)", "PONDS"],
                "website": "https://www.nasa.gov/exploration-research/space-biology",
            },
            {
                "id": "ESA",
                "name": "European Space Agency",
                "country": "Europe",
                "programs": ["MELiSSA", "EDEN ISS"],
                "website": "https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/Research/MELiSSA",
            },
            {
                "id": "ISRO",
                "name": "Indian Space Research Organisation",
                "country": "India",
                "programs": ["Gaganyaan Life Support"],
                "website": "https://www.isro.gov.in",
            },
            {
                "id": "CNSA",
                "name": "China National Space Administration",
                "country": "China",
                "programs": ["Tiangong Plant Experiments"],
                "website": "http://www.cnsa.gov.cn",
            },
            {
                "id": "JAXA",
                "name": "Japan Aerospace Exploration Agency",
                "country": "Japan",
                "programs": ["Space Seed", "Kibo Plant Experiments"],
                "website": "https://www.jaxa.jp",
            },
        ],
    }
