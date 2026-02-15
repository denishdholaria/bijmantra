from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.mars import MarsEnvironmentProfile, MarsTrial, MarsClosedLoopMetric
from app.modules.space.mars.schemas import MarsEnvironmentProfileCreate, SimulationRequest
from app.modules.space.mars.optimizer import MarsOptimizer

class MarsService:
    @staticmethod
    async def create_environment(db: AsyncSession, profile: MarsEnvironmentProfileCreate, organization_id: int) -> MarsEnvironmentProfile:
        db_profile = MarsEnvironmentProfile(
            organization_id=organization_id,
            **profile.model_dump()
        )
        db.add(db_profile)
        await db.commit()
        await db.refresh(db_profile)
        return db_profile

    @staticmethod
    async def get_environment(db: AsyncSession, environment_id: UUID, organization_id: int) -> MarsEnvironmentProfile:
        result = await db.execute(select(MarsEnvironmentProfile).filter(
            MarsEnvironmentProfile.id == environment_id,
            MarsEnvironmentProfile.organization_id == organization_id
        ))
        profile = result.scalars().first()
        if not profile:
            raise HTTPException(status_code=404, detail="Environment profile not found")
        return profile

    @staticmethod
    async def simulate_trial(db: AsyncSession, request: SimulationRequest, organization_id: int) -> MarsTrial:
        # 1. Fetch Environment
        profile = await MarsService.get_environment(db, request.environment_profile_id, organization_id)

        # 2. Run Optimizer (Deterministic)
        result = MarsOptimizer.simulate_trial(profile, request.generation)

        # 3. Create Trial Record
        trial = MarsTrial(
            organization_id=organization_id,
            environment_profile_id=request.environment_profile_id,
            germplasm_id=request.germplasm_id,
            generation=request.generation,
            survival_score=result["survival_score"],
            biomass_yield=result["biomass_yield"],
            failure_mode=result["failure_mode"],
            notes="Automated Simulation Phase 1"
        )
        db.add(trial)
        await db.flush() # Get ID

        # 4. Create Metrics Record
        metrics_data = result["closed_loop_metrics"]
        metrics = MarsClosedLoopMetric(
            trial_id=trial.id,
            water_recycling_pct=metrics_data["water_recycling_pct"],
            nutrient_loss_pct=metrics_data["nutrient_loss_pct"],
            energy_input_kwh=metrics_data["energy_input_kwh"],
            oxygen_output=metrics_data["oxygen_output"]
        )
        db.add(metrics)

        await db.commit()
        await db.refresh(trial)

        # Explicitly set relationship for return
        trial.closed_loop_metrics = metrics

        return trial

    @staticmethod
    async def get_trial(db: AsyncSession, trial_id: UUID, organization_id: int) -> MarsTrial:
        stmt = select(MarsTrial).options(selectinload(MarsTrial.closed_loop_metrics)).filter(
            MarsTrial.id == trial_id,
            MarsTrial.organization_id == organization_id
        )
        result = await db.execute(stmt)
        trial = result.scalars().first()
        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found")
        return trial
