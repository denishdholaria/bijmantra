from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.modules.space.lunar.schemas import (
    LunarEnvironmentProfileCreate, LunarEnvironmentProfileResponse,
    LunarTrialCreate, LunarTrialResponse,
    LunarSimulationRequest, LunarSimulationResponse
)
from app.modules.space.lunar.service import LunarService

router = APIRouter(prefix="/lunar", tags=["Lunar"])

@router.post("/environments", response_model=LunarEnvironmentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_environment(
    profile: LunarEnvironmentProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    service = LunarService(db)
    return await service.create_environment_profile(profile, current_user.organization_id)

@router.get("/environments/{profile_id}", response_model=LunarEnvironmentProfileResponse)
async def get_environment(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    service = LunarService(db)
    profile = await service.get_environment_profile(profile_id, current_user.organization_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Environment profile not found")
    return profile

@router.post("/trials", response_model=LunarTrialResponse, status_code=status.HTTP_201_CREATED)
async def create_trial(
    trial: LunarTrialCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    service = LunarService(db)
    try:
        return await service.create_trial(trial, current_user.organization_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trials/{trial_id}", response_model=LunarTrialResponse)
async def get_trial(
    trial_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    service = LunarService(db)
    trial = await service.get_trial(trial_id, current_user.organization_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return trial

@router.post("/simulate", response_model=LunarSimulationResponse)
async def simulate(
    request: LunarSimulationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    service = LunarService(db)
    try:
        return await service.simulate(request, current_user.organization_id)
    except ValueError as e:
        # Assuming ValueError means profile not found
        raise HTTPException(status_code=404, detail=str(e))
