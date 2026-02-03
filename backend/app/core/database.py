"""
Database connection and session management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects import sqlite
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from geoalchemy2 import Geometry
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True if settings.ENVIRONMENT == "development" else False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# SQLite compatibility patches
if "sqlite" in settings.DATABASE_URL:
    @compiles(Geometry, 'sqlite')
    def compile_geometry(element, compiler, **kw):
        return "TEXT"

    @compiles(ARRAY, 'sqlite')
    def compile_array(element, compiler, **kw):
        return "JSON"

    @compiles(JSONB, 'sqlite')
    def compile_jsonb(element, compiler, **kw):
        return "JSON"

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


# Dependency to get database session
async def get_db() -> AsyncSession:
    """
    Dependency function to get database session
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
