from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.robotics.mission_control import MissionControl

router = APIRouter()

class Origin(BaseModel):
    lat: float
    lon: float

class SimulateRequest(BaseModel):
    field_boundary: Dict[str, Any]  # GeoJSON Polygon
    origin: Origin
    obstacles: List[Dict[str, Any]] = []
    path_config: Dict[str, Any] = {}
    vehicle_config: Dict[str, Any] = {}
    simulation_config: Dict[str, Any] = {}

class SimulateResponse(BaseModel):
    mission_status: str
    path: List[Any]
    telemetry: List[Dict[str, Any]]

@router.post("/simulate", response_model=SimulateResponse)
async def simulate_mission(request: SimulateRequest):
    """
    Simulate a robotics mission:
    1. Parse field boundaries
    2. Plan path (Coverage or A*)
    3. Simulate vehicle kinematics and sensors
    4. Return telemetry
    """
    try:
        mc = MissionControl()
        # model_dump() is for Pydantic v2
        result = mc.simulate(request.model_dump())

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
