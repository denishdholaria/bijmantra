"""
AI Utilization Models
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class AIUsageDaily(BaseModel):
    """
    Tracks daily AI usage metrics per organization.
    Used for enforcing quota limits on the "Free/Standard" tier.
    """
    __tablename__ = "ai_usage_daily"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    usage_date = Column(Date, nullable=False, index=True)
    
    request_count = Column(Integer, default=0, nullable=False)
    token_count_input = Column(Integer, default=0)
    token_count_output = Column(Integer, default=0)
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'usage_date', name='uq_org_daily_usage'),
    )
    
    # Relationships
    organization = relationship("Organization")
