"""
Proposal Schemas (The Scribe)
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.proposal import ProposalStatus, ActionType

class ProposalBase(BaseModel):
    title: str
    description: Optional[str] = None
    action_type: ActionType
    target_data: Dict[str, Any]
    ai_rationale: Optional[str] = None
    confidence_score: Optional[int] = 0

class ProposalCreate(ProposalBase):
    pass

class ProposalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProposalStatus] = None
    reviewer_notes: Optional[str] = None

class ProposalReview(BaseModel):
    approved: bool
    notes: Optional[str] = None

class ProposalResponse(ProposalBase):
    id: int
    organization_id: int
    user_id: Optional[int] = None
    status: ProposalStatus
    reviewer_notes: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    created_by_ai: bool

    class Config:
        from_attributes = True
