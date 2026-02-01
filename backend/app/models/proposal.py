"""
Proposal Model (The Scribe)
Defines the schema for AI-generated safe proposals (Draft Actions).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, JSON, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel

class ProposalStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"

class ActionType(str, enum.Enum):
    CREATE_TRIAL = "create_trial"
    CREATE_CROSS = "create_cross"
    RECORD_OBSERVATION = "record_observation"
    GENERATE_REPORT = "generate_report"
    SQL_QUERY = "sql_query"
    CUSTOM = "custom"

class Proposal(BaseModel):
    """
    Represents a proposed action (usually by AI Scribe) that requires human approval.
    """
    __tablename__ = "proposals"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # The human owner/reviewer
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    action_type = Column(SQLEnum(ActionType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    status = Column(SQLEnum(ProposalStatus, values_callable=lambda x: [e.value for e in x]), default=ProposalStatus.DRAFT)
    
    # The actual data/payload for the action
    target_data = Column(JSON, default=dict)
    
    # AI Reasoning
    ai_rationale = Column(Text)
    confidence_score = Column(Integer, default=0)  # 0-100
    
    # Human Feedback
    reviewer_notes = Column(Text)
    
    # Execution Result
    execution_result = Column(JSON, default=dict)
    executed_at = Column(DateTime)
    
    # Metadata
    created_by_ai = Column(Boolean, default=True)
    
    # Relationships
    organization = relationship("Organization", backref="proposals")
    user = relationship("User", backref="proposals")
