"""
Performance Optimization Services
"""


from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.performance import (
    AssetOptimization,
    DatabaseIndex,
    FrontendBundle,
    QueryCache,
    ServerResponse,
)
from app.schemas.performance import (
    AssetOptimizationCreate,
    AssetOptimizationUpdate,
    DatabaseIndexCreate,
    DatabaseIndexUpdate,
    FrontendBundleCreate,
    FrontendBundleUpdate,
    QueryCacheCreate,
    QueryCacheUpdate,
    ServerResponseCreate,
)


class PerformanceService:

    # ============= DatabaseIndex Operations =============

    async def create_database_index(self, db: AsyncSession, index_in: DatabaseIndexCreate) -> DatabaseIndex:
        db_obj = DatabaseIndex(**index_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_database_index(self, db: AsyncSession, index_id: int) -> DatabaseIndex | None:
        return await db.get(DatabaseIndex, index_id)

    async def update_database_index(self, db: AsyncSession, index_id: int, index_in: DatabaseIndexUpdate) -> DatabaseIndex | None:
        db_obj = await self.get_database_index(db, index_id)
        if not db_obj:
            return None

        update_data = index_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete_database_index(self, db: AsyncSession, index_id: int) -> bool:
        db_obj = await self.get_database_index(db, index_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True

    async def list_database_indexes(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[DatabaseIndex]:
        stmt = select(DatabaseIndex).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ============= QueryCache Operations =============

    async def create_query_cache(self, db: AsyncSession, cache_in: QueryCacheCreate) -> QueryCache:
        db_obj = QueryCache(**cache_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_query_cache(self, db: AsyncSession, cache_id: int) -> QueryCache | None:
        return await db.get(QueryCache, cache_id)

    async def update_query_cache(self, db: AsyncSession, cache_id: int, cache_in: QueryCacheUpdate) -> QueryCache | None:
        db_obj = await self.get_query_cache(db, cache_id)
        if not db_obj:
            return None

        update_data = cache_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete_query_cache(self, db: AsyncSession, cache_id: int) -> bool:
        db_obj = await self.get_query_cache(db, cache_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True

    async def list_query_caches(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[QueryCache]:
        stmt = select(QueryCache).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ============= FrontendBundle Operations =============

    async def create_frontend_bundle(self, db: AsyncSession, bundle_in: FrontendBundleCreate) -> FrontendBundle:
        db_obj = FrontendBundle(**bundle_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_frontend_bundle(self, db: AsyncSession, bundle_id: int) -> FrontendBundle | None:
        return await db.get(FrontendBundle, bundle_id)

    async def update_frontend_bundle(self, db: AsyncSession, bundle_id: int, bundle_in: FrontendBundleUpdate) -> FrontendBundle | None:
        db_obj = await self.get_frontend_bundle(db, bundle_id)
        if not db_obj:
            return None

        update_data = bundle_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete_frontend_bundle(self, db: AsyncSession, bundle_id: int) -> bool:
        db_obj = await self.get_frontend_bundle(db, bundle_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True

    async def list_frontend_bundles(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[FrontendBundle]:
        stmt = select(FrontendBundle).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ============= AssetOptimization Operations =============

    async def create_asset_optimization(self, db: AsyncSession, asset_in: AssetOptimizationCreate) -> AssetOptimization:
        db_obj = AssetOptimization(**asset_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_asset_optimization(self, db: AsyncSession, asset_id: int) -> AssetOptimization | None:
        return await db.get(AssetOptimization, asset_id)

    async def update_asset_optimization(self, db: AsyncSession, asset_id: int, asset_in: AssetOptimizationUpdate) -> AssetOptimization | None:
        db_obj = await self.get_asset_optimization(db, asset_id)
        if not db_obj:
            return None

        update_data = asset_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete_asset_optimization(self, db: AsyncSession, asset_id: int) -> bool:
        db_obj = await self.get_asset_optimization(db, asset_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True

    async def list_asset_optimizations(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[AssetOptimization]:
        stmt = select(AssetOptimization).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ============= ServerResponse Operations =============

    async def create_server_response(self, db: AsyncSession, response_in: ServerResponseCreate) -> ServerResponse:
        db_obj = ServerResponse(**response_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_server_response(self, db: AsyncSession, response_id: int) -> ServerResponse | None:
        return await db.get(ServerResponse, response_id)

    # Usually no update for server logs

    async def delete_server_response(self, db: AsyncSession, response_id: int) -> bool:
        db_obj = await self.get_server_response(db, response_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True

    async def list_server_responses(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[ServerResponse]:
        stmt = select(ServerResponse).order_by(desc(ServerResponse.created_at)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

performance_service = PerformanceService()
