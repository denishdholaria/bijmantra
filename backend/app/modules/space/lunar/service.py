from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.space.lunar.models import LunarEnvironmentProfile, LunarTrial
from app.modules.space.lunar.schemas import LunarEnvironmentProfileCreate, LunarTrialCreate, LunarSimulationRequest, LunarSimulationResponse
from app.modules.space.lunar.gravity_model import FractionalGravityEnvironmentEngine

class LunarService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gravity_engine = FractionalGravityEnvironmentEngine()

    async def create_environment_profile(self, profile: LunarEnvironmentProfileCreate, organization_id: int) -> LunarEnvironmentProfile:
        db_profile = LunarEnvironmentProfile(
            **profile.model_dump(),
            organization_id=organization_id
        )
        self.db.add(db_profile)
        await self.db.commit()
        await self.db.refresh(db_profile)
        return db_profile

    async def get_environment_profile(self, profile_id: UUID, organization_id: int) -> LunarEnvironmentProfile | None:
        query = select(LunarEnvironmentProfile).where(
            LunarEnvironmentProfile.id == profile_id,
            LunarEnvironmentProfile.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_trial(self, trial: LunarTrialCreate, organization_id: int) -> LunarTrial:
        # Verify environment exists and belongs to org
        env = await self.get_environment_profile(trial.environment_profile_id, organization_id)
        if not env:
            raise ValueError("Environment profile not found")

        db_trial = LunarTrial(
            **trial.model_dump(),
            organization_id=organization_id
        )
        self.db.add(db_trial)
        await self.db.commit()
        await self.db.refresh(db_trial)
        return db_trial

    async def get_trial(self, trial_id: UUID, organization_id: int) -> LunarTrial | None:
        query = select(LunarTrial).where(
            LunarTrial.id == trial_id,
            LunarTrial.organization_id == organization_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def simulate(self, request: LunarSimulationRequest, organization_id: int) -> LunarSimulationResponse:
        # Fetch environment
        env = await self.get_environment_profile(request.environment_profile_id, organization_id)
        if not env:
            # We can't simulate without environment
            raise ValueError("Environment profile not found")

        # Convert DB model to Schema for engine (or just access attributes)
        # The engine expects an object with the required attributes.
        # The SQLAlchemy model has them.

        result = self.gravity_engine.simulate(env, request.generation, request.germplasm_id)

        return LunarSimulationResponse(**result)
