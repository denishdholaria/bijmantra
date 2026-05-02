from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============= DatabaseIndex Schemas =============

class DatabaseIndexBase(BaseModel):
    table_name: str
    index_name: str
    columns: List[str]
    is_unique: bool = False
    description: Optional[str] = None


class DatabaseIndexCreate(DatabaseIndexBase):
    pass


class DatabaseIndexUpdate(BaseModel):
    table_name: Optional[str] = None
    index_name: Optional[str] = None
    columns: Optional[List[str]] = None
    is_unique: Optional[bool] = None
    description: Optional[str] = None


class DatabaseIndex(DatabaseIndexBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= QueryCache Schemas =============

class QueryCacheBase(BaseModel):
    query_hash: str
    query_text: str
    hit_count: int = 0
    miss_count: int = 0
    is_active: bool = True
    last_accessed: Optional[datetime] = None


class QueryCacheCreate(QueryCacheBase):
    pass


class QueryCacheUpdate(BaseModel):
    hit_count: Optional[int] = None
    miss_count: Optional[int] = None
    is_active: Optional[bool] = None
    last_accessed: Optional[datetime] = None


class QueryCache(QueryCacheBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= FrontendBundle Schemas =============

class FrontendBundleBase(BaseModel):
    name: str
    size_kb: float
    load_time_ms: Optional[int] = None
    build_id: str
    status: str = "active"


class FrontendBundleCreate(FrontendBundleBase):
    pass


class FrontendBundleUpdate(BaseModel):
    size_kb: Optional[float] = None
    load_time_ms: Optional[int] = None
    status: Optional[str] = None


class FrontendBundle(FrontendBundleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= AssetOptimization Schemas =============

class AssetOptimizationBase(BaseModel):
    asset_path: str
    original_size_kb: float
    optimized_size_kb: float
    compression_ratio: Optional[float] = None
    optimization_method: Optional[str] = None


class AssetOptimizationCreate(AssetOptimizationBase):
    pass


class AssetOptimizationUpdate(BaseModel):
    original_size_kb: Optional[float] = None
    optimized_size_kb: Optional[float] = None
    compression_ratio: Optional[float] = None
    optimization_method: Optional[str] = None


class AssetOptimization(AssetOptimizationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= ServerResponse Schemas =============

class ServerResponseBase(BaseModel):
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


class ServerResponseCreate(ServerResponseBase):
    pass


class ServerResponseUpdate(BaseModel):
    pass  # Usually logs are immutable, but included for completeness


class ServerResponse(ServerResponseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
