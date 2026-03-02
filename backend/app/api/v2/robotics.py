from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.services.robotics.mission_control import MissionControl


router = APIRouter(dependencies=[Depends(get_current_user)])

class Origin(BaseModel):
    lat: float
    lon: float

class SimulateRequest(BaseModel):
    field_boundary: dict[str, Any]  # GeoJSON Polygon
    origin: Origin
    obstacles: list[dict[str, Any]] = []
    path_config: dict[str, Any] = {}
    vehicle_config: dict[str, Any] = {}
    simulation_config: dict[str, Any] = {}

class SimulateResponse(BaseModel):
    mission_status: str
    path: list[Any]
    telemetry: list[dict[str, Any]]

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
