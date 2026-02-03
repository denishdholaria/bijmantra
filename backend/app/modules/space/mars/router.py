from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.models.core import User
from app.modules.space.mars.schemas import (
    MarsEnvironmentProfileCreate,
    MarsEnvironmentProfileRead,
    MarsTrialRead,
    SimulationRequest,
    SimulationResponse
)
from app.modules.space.mars.service import MarsService

router = APIRouter()

@router.post("/environments", response_model=MarsEnvironmentProfileRead)
async def create_environment(
    profile: MarsEnvironmentProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await MarsService.create_environment(db, profile, current_user.organization_id)

@router.get("/environments/{environment_id}", response_model=MarsEnvironmentProfileRead)
async def get_environment(
    environment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await MarsService.get_environment(db, environment_id, current_user.organization_id)

@router.post("/simulate", response_model=SimulationResponse)
async def simulate_trial(
    request: SimulationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trial = await MarsService.simulate_trial(db, request, current_user.organization_id)
    return SimulationResponse(
        trial_id=trial.id,
        survival_score=trial.survival_score,
        biomass_yield=trial.biomass_yield,
        failure_mode=trial.failure_mode,
        closed_loop_metrics=trial.closed_loop_metrics
    )

@router.get("/trials/{trial_id}", response_model=MarsTrialRead)
async def get_trial(
    trial_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await MarsService.get_trial(db, trial_id, current_user.organization_id)
