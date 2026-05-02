"""
Proposal Schemas (The Scribe)
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.proposal import ActionType, ProposalStatus


class ProposalBase(BaseModel):
    title: str
    description: str | None = None
    action_type: ActionType
    target_data: dict[str, Any]
    ai_rationale: str | None = None
    confidence_score: int | None = 0

class ProposalCreate(ProposalBase):
    pass

class ProposalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: ProposalStatus | None = None
    reviewer_notes: str | None = None

class ProposalReview(BaseModel):
    approved: bool
    notes: str | None = None

class ProposalResponse(ProposalBase):
    id: int
    organization_id: int
    user_id: int | None = None
    status: ProposalStatus
    reviewer_notes: str | None = None
    execution_result: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None
    executed_at: datetime | None = None
    created_by_ai: bool

    model_config = ConfigDict(from_attributes=True)
