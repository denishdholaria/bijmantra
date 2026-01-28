"""
System Settings Model
Stores configuration for different system modules per organization.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SystemSettings(BaseModel):
    """
    System Settings model
    Stores settings as JSON blobs keyed by category (e.g., 'general', 'security').
    """

    __tablename__ = "system_settings"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint('organization_id', 'category', name='uq_system_settings_org_category'),
    )

    # Relationships
    organization = relationship("Organization")
    updater = relationship("User", foreign_keys=[updated_by])
