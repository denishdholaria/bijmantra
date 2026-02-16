from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
import uuid

from app.models.brapi_phenotyping import Scale
from app.schemas.brapi_scales import ScaleCreate, ScaleUpdate

class ScalesService:
    @staticmethod
    async def get_all(
        db: AsyncSession,
        page: int = 0,
        page_size: int = 1000,
        scale_db_id: Optional[str] = None,
        scale_name: Optional[str] = None,
        data_type: Optional[str] = None,
        ontology_db_id: Optional[str] = None
    ) -> Tuple[List[Scale], int]:
        query = select(Scale)

        if scale_db_id:
            query = query.where(Scale.scale_db_id == scale_db_id)
        if scale_name:
            query = query.where(Scale.scale_name.ilike(f"%{scale_name}%"))
        if data_type:
            query = query.where(Scale.data_type == data_type)
        if ontology_db_id:
            query = query.where(Scale.ontology_db_id == ontology_db_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Pagination
        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        scales = result.scalars().all()

        return list(scales), total

    @staticmethod
    async def get_by_id(db: AsyncSession, scale_db_id: str) -> Optional[Scale]:
        query = select(Scale).where(Scale.scale_db_id == scale_db_id)
        result = await db.execute(query)
        scale = result.scalar_one_or_none()

        if not scale:
            # Try by numeric ID for compatibility
            try:
                scale_id = int(scale_db_id)
                query = select(Scale).where(Scale.id == scale_id)
                result = await db.execute(query)
                scale = result.scalar_one_or_none()
            except ValueError:
                pass

        return scale

    @staticmethod
    async def create(db: AsyncSession, scale_in: ScaleCreate, organization_id: int) -> Scale:
        scale_data = scale_in.model_dump(exclude_unset=True, by_alias=True)

        # Extract nested fields
        valid_values = scale_data.pop("validValues", {}) or {}
        ontology_ref = scale_data.pop("ontologyReference", {}) or {}

        new_scale = Scale(
            organization_id=organization_id,
            scale_db_id=scale_data.get("scaleDbId") or str(uuid.uuid4()),
            scale_name=scale_data.get("scaleName"),
            scale_pui=scale_data.get("scalePUI"),
            data_type=scale_data.get("dataType"),
            decimal_places=scale_data.get("decimalPlaces"),
            valid_values_min=valid_values.get("min"),
            valid_values_max=valid_values.get("max"),
            valid_values_categories=valid_values.get("categories"),
            ontology_db_id=ontology_ref.get("ontologyDbId"),
            ontology_name=ontology_ref.get("ontologyName"),
            ontology_version=ontology_ref.get("version"),
            external_references=scale_data.get("externalReferences"),
            additional_info=scale_data.get("additionalInfo")
        )

        db.add(new_scale)
        await db.flush() # flush to get ID if needed, but we mostly use scale_db_id
        return new_scale

    @staticmethod
    async def update(db: AsyncSession, scale_db_id: str, scale_in: ScaleUpdate) -> Optional[Scale]:
        scale = await ScalesService.get_by_id(db, scale_db_id)
        if not scale:
            return None

        update_data = scale_in.model_dump(exclude_unset=True, by_alias=True)

        if "scaleName" in update_data:
            scale.scale_name = update_data["scaleName"]
        if "scalePUI" in update_data:
            scale.scale_pui = update_data["scalePUI"]
        if "dataType" in update_data:
            scale.data_type = update_data["dataType"]
        if "decimalPlaces" in update_data:
            scale.decimal_places = update_data["decimalPlaces"]

        if "validValues" in update_data and update_data["validValues"]:
            valid_values = update_data["validValues"]
            scale.valid_values_min = valid_values.get("min")
            scale.valid_values_max = valid_values.get("max")
            scale.valid_values_categories = valid_values.get("categories")

        if "ontologyReference" in update_data and update_data["ontologyReference"]:
            ontology_ref = update_data["ontologyReference"]
            scale.ontology_db_id = ontology_ref.get("ontologyDbId")
            scale.ontology_name = ontology_ref.get("ontologyName")
            scale.ontology_version = ontology_ref.get("version")

        if "externalReferences" in update_data:
            scale.external_references = update_data["externalReferences"]
        if "additionalInfo" in update_data:
            scale.additional_info = update_data["additionalInfo"]

        await db.refresh(scale)
        return scale

    @staticmethod
    async def delete(db: AsyncSession, scale_db_id: str) -> bool:
        scale = await ScalesService.get_by_id(db, scale_db_id)
        if not scale:
            return False

        await db.delete(scale)
        return True
