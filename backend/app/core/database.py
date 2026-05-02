"""
Database connection and session management
"""

import os

from geoalchemy2 import Geometry
from sqlalchemy import event
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

# pgcrypto session variable setup
# Sets app.encryption_key for the session so pgp_sym_encrypt() / pgp_sym_decrypt()
# can call current_setting('app.encryption_key') without needing the key passed
# explicitly on every query. Uses set_config() with is_local=false so the value
# persists for the lifetime of the pooled connection (not just the current transaction).
# If INTEGRATION_ENCRYPTION_KEY is absent the listener is a no-op — pgcrypto
# functions simply won't be available until the env var is provided.
@event.listens_for(engine.sync_engine, "connect")
def set_pgcrypto_encryption_key(dbapi_conn, connection_record):
    """Set app.encryption_key session variable for pgcrypto functions."""
    encryption_key = os.environ.get("INTEGRATION_ENCRYPTION_KEY")
    if encryption_key:
        cursor = dbapi_conn.cursor()
        # Parameterized set_config prevents injection; is_local=false scopes to session
        cursor.execute(
            "SELECT set_config('app.encryption_key', %s, false)",
            (encryption_key,),
        )
        cursor.close()


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
