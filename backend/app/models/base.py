"""
Base model with common fields for all models
"""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Column, DateTime

from app.core.database import Base


class BaseModel(Base):
    """Base model with common fields"""

    __abstract__ = True

    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
