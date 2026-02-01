from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import uuid

from app.models.phenotyping import ObservationUnit
from app.schemas.brapi.observation_units import ObservationUnitCreate, ObservationUnitUpdate

class ObservationUnitService:
    async def list_observation_units(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        study_db_id: Optional[str] = None,
        germplasm_db_id: Optional[str] = None,
        observation_level: Optional[str] = None,
        observation_unit_db_id: Optional[str] = None,
        organization_id: Optional[int] = None,
    ) -> Tuple[List[ObservationUnit], int]:
        # Build base statement with eager loading
        stmt = select(ObservationUnit).options(
            selectinload(ObservationUnit.study),
            selectinload(ObservationUnit.germplasm),
        )

        # Filter by user's organization (multi-tenant isolation)
        if organization_id:
            stmt = stmt.where(ObservationUnit.organization_id == organization_id)

        # Apply filters
        if study_db_id:
            stmt = stmt.where(ObservationUnit.study_id == int(study_db_id))
        if germplasm_db_id:
            stmt = stmt.where(ObservationUnit.germplasm_id == int(germplasm_db_id))
        if observation_level:
            stmt = stmt.where(ObservationUnit.observation_level == observation_level)
        if observation_unit_db_id:
            stmt = stmt.where(ObservationUnit.observation_unit_db_id == observation_unit_db_id)

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination and execute
        stmt = stmt.offset(page * page_size).limit(page_size)
        result = await db.execute(stmt)
        results = result.scalars().all()

        return results, total

    async def create_observation_unit(
        self,
        db: AsyncSession,
        unit: ObservationUnitCreate,
        organization_id: int
    ) -> ObservationUnit:
        unit_db_id = f"ou_{uuid.uuid4().hex[:12]}"

        new_unit = ObservationUnit(
            organization_id=organization_id,
            observation_unit_db_id=unit_db_id,
            observation_unit_name=unit.observationUnitName,
            observation_unit_pui=unit.observationUnitPUI,
            study_id=int(unit.studyDbId) if unit.studyDbId else None,
            germplasm_id=int(unit.germplasmDbId) if unit.germplasmDbId else None,
            cross_db_id=unit.crossDbId,
            seedlot_db_id=unit.seedLotDbId,
            observation_level=unit.observationLevel,
            observation_level_code=unit.observationLevelCode,
            observation_level_order=unit.observationLevelOrder,
            position_coordinate_x=unit.positionCoordinateX,
            position_coordinate_x_type=unit.positionCoordinateXType,
            position_coordinate_y=unit.positionCoordinateY,
            position_coordinate_y_type=unit.positionCoordinateYType,
            entry_type=unit.entryType,
            treatments=unit.treatments,
        )

        db.add(new_unit)
        await db.commit()
        await db.refresh(new_unit)

        return new_unit

    async def get_observation_unit(
        self,
        db: AsyncSession,
        observation_unit_db_id: str
    ) -> Optional[ObservationUnit]:
        stmt = select(ObservationUnit).options(
            selectinload(ObservationUnit.study),
            selectinload(ObservationUnit.germplasm),
        ).where(ObservationUnit.observation_unit_db_id == observation_unit_db_id)

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_observation_units_bulk(
        self,
        db: AsyncSession,
        units: List[ObservationUnitUpdate]
    ) -> List[ObservationUnit]:
        updated = []

        for unit_data in units:
            if not unit_data.observationUnitDbId:
                continue

            stmt = select(ObservationUnit).options(
                selectinload(ObservationUnit.study),
                selectinload(ObservationUnit.germplasm),
            ).where(ObservationUnit.observation_unit_db_id == unit_data.observationUnitDbId)

            result = await db.execute(stmt)
            unit = result.scalar_one_or_none()

            if unit:
                if unit_data.observationUnitName:
                    unit.observation_unit_name = unit_data.observationUnitName
                if unit_data.observationLevel:
                    unit.observation_level = unit_data.observationLevel
                if unit_data.positionCoordinateX:
                    unit.position_coordinate_x = unit_data.positionCoordinateX
                if unit_data.positionCoordinateY:
                    unit.position_coordinate_y = unit_data.positionCoordinateY
                if unit_data.treatments:
                    unit.treatments = unit_data.treatments

                updated.append(unit)

        await db.commit()
        return updated

    async def update_observation_unit(
        self,
        db: AsyncSession,
        observation_unit_db_id: str,
        unit_data: ObservationUnitUpdate
    ) -> Optional[ObservationUnit]:
        stmt = select(ObservationUnit).options(
            selectinload(ObservationUnit.study),
            selectinload(ObservationUnit.germplasm),
        ).where(ObservationUnit.observation_unit_db_id == observation_unit_db_id)

        result = await db.execute(stmt)
        unit = result.scalar_one_or_none()

        if not unit:
            return None

        if unit_data.observationUnitName:
            unit.observation_unit_name = unit_data.observationUnitName
        if unit_data.observationLevel:
            unit.observation_level = unit_data.observationLevel
        if unit_data.positionCoordinateX:
            unit.position_coordinate_x = unit_data.positionCoordinateX
        if unit_data.positionCoordinateY:
            unit.position_coordinate_y = unit_data.positionCoordinateY
        if unit_data.treatments:
            unit.treatments = unit_data.treatments

        await db.commit()
        await db.refresh(unit)
        return unit

observation_unit_service = ObservationUnitService()
