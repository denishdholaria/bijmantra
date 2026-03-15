"""
Performance Optimization API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser
from app.core.database import get_db
from app.schemas.performance import (
    AssetOptimization,
    AssetOptimizationCreate,
    AssetOptimizationUpdate,
    DatabaseIndex,
    DatabaseIndexCreate,
    DatabaseIndexUpdate,
    FrontendBundle,
    FrontendBundleCreate,
    FrontendBundleUpdate,
    QueryCache,
    QueryCacheCreate,
    QueryCacheUpdate,
    ServerResponse,
    ServerResponseCreate,
)
from app.modules.breeding.services.performance_service import performance_service


router = APIRouter(tags=["Performance Optimization"], dependencies=[Depends(get_current_superuser)])

# ============= DatabaseIndex Endpoints =============

@router.post("/database-indexes", response_model=DatabaseIndex)
async def create_database_index(
    index_in: DatabaseIndexCreate,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.create_database_index(db, index_in)

@router.get("/database-indexes", response_model=list[DatabaseIndex])
async def list_database_indexes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.list_database_indexes(db, skip=skip, limit=limit)

@router.get("/database-indexes/{index_id}", response_model=DatabaseIndex)
async def get_database_index(
    index_id: int,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.get_database_index(db, index_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Database Index not found")
    return db_obj

@router.put("/database-indexes/{index_id}", response_model=DatabaseIndex)
async def update_database_index(
    index_id: int,
    index_in: DatabaseIndexUpdate,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.update_database_index(db, index_id, index_in)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Database Index not found")
    return db_obj

@router.delete("/database-indexes/{index_id}", response_model=bool)
async def delete_database_index(
    index_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await performance_service.delete_database_index(db, index_id)
    if not success:
        raise HTTPException(status_code=404, detail="Database Index not found")
    return True

# ============= QueryCache Endpoints =============

@router.post("/query-caches", response_model=QueryCache)
async def create_query_cache(
    cache_in: QueryCacheCreate,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.create_query_cache(db, cache_in)

@router.get("/query-caches", response_model=list[QueryCache])
async def list_query_caches(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.list_query_caches(db, skip=skip, limit=limit)

@router.get("/query-caches/{cache_id}", response_model=QueryCache)
async def get_query_cache(
    cache_id: int,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.get_query_cache(db, cache_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Query Cache not found")
    return db_obj

@router.put("/query-caches/{cache_id}", response_model=QueryCache)
async def update_query_cache(
    cache_id: int,
    cache_in: QueryCacheUpdate,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.update_query_cache(db, cache_id, cache_in)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Query Cache not found")
    return db_obj

@router.delete("/query-caches/{cache_id}", response_model=bool)
async def delete_query_cache(
    cache_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await performance_service.delete_query_cache(db, cache_id)
    if not success:
        raise HTTPException(status_code=404, detail="Query Cache not found")
    return True

# ============= FrontendBundle Endpoints =============

@router.post("/frontend-bundles", response_model=FrontendBundle)
async def create_frontend_bundle(
    bundle_in: FrontendBundleCreate,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.create_frontend_bundle(db, bundle_in)

@router.get("/frontend-bundles", response_model=list[FrontendBundle])
async def list_frontend_bundles(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.list_frontend_bundles(db, skip=skip, limit=limit)

@router.get("/frontend-bundles/{bundle_id}", response_model=FrontendBundle)
async def get_frontend_bundle(
    bundle_id: int,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.get_frontend_bundle(db, bundle_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Frontend Bundle not found")
    return db_obj

@router.put("/frontend-bundles/{bundle_id}", response_model=FrontendBundle)
async def update_frontend_bundle(
    bundle_id: int,
    bundle_in: FrontendBundleUpdate,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.update_frontend_bundle(db, bundle_id, bundle_in)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Frontend Bundle not found")
    return db_obj

@router.delete("/frontend-bundles/{bundle_id}", response_model=bool)
async def delete_frontend_bundle(
    bundle_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await performance_service.delete_frontend_bundle(db, bundle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Frontend Bundle not found")
    return True

# ============= AssetOptimization Endpoints =============

@router.post("/asset-optimizations", response_model=AssetOptimization)
async def create_asset_optimization(
    asset_in: AssetOptimizationCreate,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.create_asset_optimization(db, asset_in)

@router.get("/asset-optimizations", response_model=list[AssetOptimization])
async def list_asset_optimizations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.list_asset_optimizations(db, skip=skip, limit=limit)

@router.get("/asset-optimizations/{asset_id}", response_model=AssetOptimization)
async def get_asset_optimization(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.get_asset_optimization(db, asset_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Asset Optimization not found")
    return db_obj

@router.put("/asset-optimizations/{asset_id}", response_model=AssetOptimization)
async def update_asset_optimization(
    asset_id: int,
    asset_in: AssetOptimizationUpdate,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.update_asset_optimization(db, asset_id, asset_in)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Asset Optimization not found")
    return db_obj

@router.delete("/asset-optimizations/{asset_id}", response_model=bool)
async def delete_asset_optimization(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await performance_service.delete_asset_optimization(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset Optimization not found")
    return True

# ============= ServerResponse Endpoints =============

@router.post("/server-responses", response_model=ServerResponse)
async def create_server_response(
    response_in: ServerResponseCreate,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.create_server_response(db, response_in)

@router.get("/server-responses", response_model=list[ServerResponse])
async def list_server_responses(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    return await performance_service.list_server_responses(db, skip=skip, limit=limit)

@router.get("/server-responses/{response_id}", response_model=ServerResponse)
async def get_server_response(
    response_id: int,
    db: AsyncSession = Depends(get_db)
):
    db_obj = await performance_service.get_server_response(db, response_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Server Response not found")
    return db_obj

@router.delete("/server-responses/{response_id}", response_model=bool)
async def delete_server_response(
    response_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await performance_service.delete_server_response(db, response_id)
    if not success:
        raise HTTPException(status_code=404, detail="Server Response not found")
    return True
