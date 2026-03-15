"""
Field Environment API
Soil profiles, input logs, irrigation, and field history
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.modules.environment.services.field_environment_service import (
    InputType,
    IrrigationType,
    SoilTexture,
    field_environment,
)


router = APIRouter(prefix="/field-environment", tags=["Field Environment"], dependencies=[Depends(get_current_user)])


# Request/Response Models
class SoilProfileCreate(BaseModel):
    field_id: str
    sample_date: str | None = None
    depth_cm: int = 30
    texture: str = "loam"
    ph: float
    organic_matter: float = 0
    nitrogen: float = 0
    phosphorus: float = 0
    potassium: float = 0
    calcium: float | None = None
    magnesium: float | None = None
    notes: str = ""


class SoilProfileResponse(BaseModel):
    id: str
    field_id: str
    sample_date: str
    depth_cm: int
    texture: str
    ph: float
    organic_matter: float
    nitrogen: float
    phosphorus: float
    potassium: float
    calcium: float | None
    magnesium: float | None
    notes: str


class InputLogCreate(BaseModel):
    field_id: str
    input_type: str
    product_name: str
    application_date: str | None = None
    quantity: float
    unit: str
    area_applied: float = 1.0
    method: str = ""
    applicator: str | None = None
    cost: float | None = None
    notes: str = ""


class InputLogResponse(BaseModel):
    id: str
    field_id: str
    input_type: str
    product_name: str
    application_date: str
    quantity: float
    unit: str
    area_applied: float
    method: str
    cost: float | None
    notes: str


class IrrigationEventCreate(BaseModel):
    field_id: str
    irrigation_type: str = "drip"
    event_date: str | None = None
    duration_hours: float
    water_volume: float
    source: str = ""
    cost: float | None = None
    notes: str = ""


class IrrigationEventResponse(BaseModel):
    id: str
    field_id: str
    irrigation_type: str
    event_date: str
    duration_hours: float
    water_volume: float
    source: str
    cost: float | None
    notes: str


class FieldHistoryCreate(BaseModel):
    field_id: str
    season: str
    crop: str
    variety: str | None = None
    planting_date: str | None = None
    harvest_date: str | None = None
    yield_amount: float | None = None
    yield_unit: str = "kg/ha"
    notes: str = ""


class FieldHistoryResponse(BaseModel):
    id: str
    field_id: str
    season: str
    crop: str
    variety: str | None
    planting_date: str | None
    harvest_date: str | None
    yield_amount: float | None
    yield_unit: str
    notes: str


# Helper functions
def _profile_to_response(p) -> SoilProfileResponse:
    return SoilProfileResponse(
        id=p.id, field_id=p.field_id, sample_date=str(p.sample_date),
        depth_cm=p.depth_cm, texture=p.texture.value, ph=p.ph,
        organic_matter=p.organic_matter, nitrogen=p.nitrogen,
        phosphorus=p.phosphorus, potassium=p.potassium,
        calcium=p.calcium, magnesium=p.magnesium, notes=p.notes
    )


def _input_to_response(i) -> InputLogResponse:
    return InputLogResponse(
        id=i.id, field_id=i.field_id, input_type=i.input_type.value,
        product_name=i.product_name, application_date=str(i.application_date),
        quantity=i.quantity, unit=i.unit, area_applied=i.area_applied,
        method=i.method, cost=i.cost, notes=i.notes
    )


def _irrigation_to_response(e) -> IrrigationEventResponse:
    return IrrigationEventResponse(
        id=e.id, field_id=e.field_id, irrigation_type=e.irrigation_type.value,
        event_date=str(e.event_date), duration_hours=e.duration_hours,
        water_volume=e.water_volume, source=e.source, cost=e.cost, notes=e.notes
    )


def _history_to_response(h) -> FieldHistoryResponse:
    return FieldHistoryResponse(
        id=h.id, field_id=h.field_id, season=h.season, crop=h.crop,
        variety=h.variety, planting_date=str(h.planting_date) if h.planting_date else None,
        harvest_date=str(h.harvest_date) if h.harvest_date else None,
        yield_amount=h.yield_amount, yield_unit=h.yield_unit, notes=h.notes
    )


# Soil Profile Endpoints
@router.get("/soil-profiles", response_model=list[SoilProfileResponse])
async def get_soil_profiles(field_id: str | None = None):
    """Get soil profiles, optionally filtered by field"""
    profiles = field_environment.get_soil_profiles(field_id)
    return [_profile_to_response(p) for p in profiles]


@router.get("/soil-profiles/{profile_id}", response_model=SoilProfileResponse)
async def get_soil_profile(profile_id: str):
    """Get a specific soil profile"""
    profile = field_environment.get_soil_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Soil profile not found")
    return _profile_to_response(profile)


@router.post("/soil-profiles", response_model=SoilProfileResponse)
async def create_soil_profile(data: SoilProfileCreate):
    """Create a new soil profile"""
    profile = field_environment.add_soil_profile(data.model_dump())
    return _profile_to_response(profile)


@router.get("/soil-profiles/{profile_id}/recommendations")
async def get_fertilizer_recommendations(profile_id: str):
    """Get fertilizer recommendations based on soil profile"""
    recommendations = field_environment.get_fertilizer_recommendations(profile_id)
    if not recommendations and not field_environment.get_soil_profile(profile_id):
        raise HTTPException(status_code=404, detail="Soil profile not found")
    return {"recommendations": recommendations}


# Input Log Endpoints
@router.get("/input-logs", response_model=list[InputLogResponse])
async def get_input_logs(field_id: str | None = None, input_type: str | None = None):
    """Get input logs with optional filters"""
    parsed_type = InputType(input_type) if input_type else None
    logs = field_environment.get_input_logs(field_id, parsed_type)
    return [_input_to_response(i) for i in logs]


@router.post("/input-logs", response_model=InputLogResponse)
async def create_input_log(data: InputLogCreate):
    """Create a new input log"""
    log = field_environment.add_input_log(data.model_dump())
    return _input_to_response(log)


@router.get("/input-types")
async def get_input_types():
    """Get available input types"""
    return {"input_types": [{"value": t.value, "name": t.name} for t in InputType]}


# Irrigation Endpoints
@router.get("/irrigation", response_model=list[IrrigationEventResponse])
async def get_irrigation_events(field_id: str | None = None):
    """Get irrigation events"""
    events = field_environment.get_irrigation_events(field_id)
    return [_irrigation_to_response(e) for e in events]


@router.post("/irrigation", response_model=IrrigationEventResponse)
async def create_irrigation_event(data: IrrigationEventCreate):
    """Create a new irrigation event"""
    event = field_environment.add_irrigation_event(data.model_dump())
    return _irrigation_to_response(event)


@router.get("/irrigation/summary/{field_id}")
async def get_water_usage_summary(field_id: str, year: int | None = None):
    """Get water usage summary for a field"""
    return field_environment.get_water_usage_summary(field_id, year)


@router.get("/irrigation-types")
async def get_irrigation_types():
    """Get available irrigation types"""
    return {"irrigation_types": [{"value": t.value, "name": t.name} for t in IrrigationType]}


# Field History Endpoints
@router.get("/history/{field_id}", response_model=list[FieldHistoryResponse])
async def get_field_history(field_id: str):
    """Get field history (crop rotation)"""
    history = field_environment.get_field_history(field_id)
    return [_history_to_response(h) for h in history]


@router.post("/history", response_model=FieldHistoryResponse)
async def create_field_history(data: FieldHistoryCreate):
    """Add a field history entry"""
    history = field_environment.add_field_history(data.model_dump())
    return _history_to_response(history)


# Soil Texture Types
@router.get("/soil-textures")
async def get_soil_textures():
    """Get available soil texture types"""
    return {"soil_textures": [{"value": t.value, "name": t.name.replace("_", " ").title()} for t in SoilTexture]}
