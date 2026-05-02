"""
Performance Optimization Models
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text

from app.models.base import BaseModel


class DatabaseIndex(BaseModel):
    """
    Tracks database indexes and their metadata.
    """
    __tablename__ = "perf_database_indexes"

    table_name = Column(String, nullable=False, index=True)
    index_name = Column(String, nullable=False, unique=True, index=True)
    columns = Column(JSON, nullable=False)  # List of column names
    is_unique = Column(Boolean, default=False)
    description = Column(String, nullable=True)


class QueryCache(BaseModel):
    """
    Tracks query cache performance metrics.
    """
    __tablename__ = "perf_query_cache"

    query_hash = Column(String, nullable=False, unique=True, index=True)
    query_text = Column(Text, nullable=False)
    hit_count = Column(Integer, default=0)
    miss_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)


class FrontendBundle(BaseModel):
    """
    Tracks frontend bundle sizes and load metrics.
    """
    __tablename__ = "perf_frontend_bundles"

    name = Column(String, nullable=False, index=True)
    size_kb = Column(Float, nullable=False)
    load_time_ms = Column(Integer, nullable=True)
    build_id = Column(String, nullable=False, index=True)
    status = Column(String, default="active")


class AssetOptimization(BaseModel):
    """
    Tracks static asset optimization metrics.
    """
    __tablename__ = "perf_asset_optimizations"

    asset_path = Column(String, nullable=False, unique=True, index=True)
    original_size_kb = Column(Float, nullable=False)
    optimized_size_kb = Column(Float, nullable=False)
    compression_ratio = Column(Float, nullable=True)
    optimization_method = Column(String, nullable=True)


class ServerResponse(BaseModel):
    """
    Tracks server response times and status codes.
    """
    __tablename__ = "perf_server_responses"

    endpoint = Column(String, nullable=False, index=True)
    method = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    client_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
