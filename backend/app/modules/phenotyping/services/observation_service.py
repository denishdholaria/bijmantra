import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable
from app.schemas.brapi.observations import ObservationCreate


class ObservationService:
    async def create_observation(
        self, db: AsyncSession, observation: ObservationCreate, organization_id: int
    ) -> Observation:
        obs_db_id = f"obs_{uuid.uuid4().hex[:12]}"

        # Look up related entities
        obs_unit_id = None
        obs_var_id = None

        if observation.observationUnitDbId:
            query = select(ObservationUnit).where(
                ObservationUnit.observation_unit_db_id == observation.observationUnitDbId
            )
            result = await db.execute(query)
            unit = result.scalar_one_or_none()
            if unit:
                obs_unit_id = unit.id

        if observation.observationVariableDbId:
            query = select(ObservationVariable).where(
                ObservationVariable.observation_variable_db_id
                == observation.observationVariableDbId
            )
            result = await db.execute(query)
            var = result.scalar_one_or_none()
            if var:
                obs_var_id = var.id

        new_obs = Observation(
            organization_id=organization_id,
            observation_db_id=obs_db_id,
            observation_unit_id=obs_unit_id,
            observation_variable_id=obs_var_id,
            value=observation.value,
            observation_time_stamp=observation.observationTimeStamp
            or datetime.now(UTC).isoformat() + "Z",
            collector=observation.collector,
            season_db_id=observation.seasonDbId,
        )

        db.add(new_obs)
        await db.commit()
        await db.refresh(new_obs)

        # Reload with relationships
        query = (
            select(Observation)
            .options(
                selectinload(Observation.observation_unit),
                selectinload(Observation.observation_variable),
                selectinload(Observation.germplasm),
            )
            .where(Observation.id == new_obs.id)
        )
        result = await db.execute(query)
        return result.scalar_one()

    def model_to_brapi(self, obs: Observation) -> dict:
        return {
            "observationDbId": obs.observation_db_id,
            "observationUnitDbId": obs.observation_unit.observation_unit_db_id
            if obs.observation_unit
            else None,
            "observationVariableDbId": obs.observation_variable.observation_variable_db_id
            if obs.observation_variable
            else None,
            "observationVariableName": obs.observation_variable.observation_variable_name
            if obs.observation_variable
            else None,
            "value": obs.value,
            "observationTimeStamp": obs.observation_time_stamp,
            "collector": obs.collector,
            "studyDbId": str(obs.study_id) if obs.study_id else None,
            "germplasmDbId": str(obs.germplasm_id) if obs.germplasm_id else None,
            "seasonDbId": obs.season_db_id,
            "additionalInfo": obs.additional_info,
            "externalReferences": obs.external_references,
        }


observation_service = ObservationService()
