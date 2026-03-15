"""
Database connection and session management
"""

from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import declarative_base

from app.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# SQLite compatibility patches
if "sqlite" in settings.DATABASE_URL:

    @compiles(Geometry, "sqlite")
    def compile_geometry(element, compiler, **kw):
        return "TEXT"

    @compiles(ARRAY, "sqlite")
    def compile_array(element, compiler, **kw):
        return "JSON"

    @compiles(JSONB, "sqlite")
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
