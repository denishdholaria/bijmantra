"""
Base CRUD operations
"""

from typing import Generic, TypeVar, Type, Optional, List, Any
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import BaseModel as DBBaseModel

ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD operations"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_by_db_id(self, db: AsyncSession, db_id: str, org_id: int) -> Optional[ModelType]:
        """Get a single record by BrAPI DbId and organization"""
        # Assumes model has a {model}_db_id field
        db_id_field = getattr(self.model, f"{self.model.__tablename__[:-1]}_db_id", None)
        if db_id_field is None:
            return None

        result = await db.execute(
            select(self.model).where(
                db_id_field == db_id,
                self.model.organization_id == org_id
            )
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        org_id: Optional[int] = None,
        filters: Optional[dict] = None
    ) -> tuple[List[ModelType], int]:
        """
        Get multiple records with pagination
        Returns: (records, total_count)
        """
        # Base query
        query = select(self.model)

        # Apply organization filter if provided
        if org_id is not None and hasattr(self.model, 'organization_id'):
            query = query.where(self.model.organization_id == org_id)

        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        records = result.scalars().all()

        return list(records), total_count

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        org_id: Optional[int] = None
    ) -> ModelType:
        """Create a new record"""
        obj_data = obj_in.model_dump(exclude_unset=True)

        # Add organization_id if model supports it
        if org_id is not None and hasattr(self.model, 'organization_id'):
            obj_data['organization_id'] = org_id

        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update an existing record"""
        obj_data = obj_in.model_dump(exclude_unset=True)

        for field, value in obj_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> ModelType:
        """Delete a record"""
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.flush()
        return obj
