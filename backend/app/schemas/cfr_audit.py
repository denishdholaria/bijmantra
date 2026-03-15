"""
CFR Part 11 Audit Log Schemas

Pydantic models for request validation and response serialization
of immutable audit logs.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CFRLogBase(BaseModel):
    """Base fields for CFR logs."""

    action_type: str = Field(..., description="Action type (CREATE, UPDATE, DELETE, SIGN, EXPORT)")
    resource_type: str = Field(..., description="Type of resource affected (e.g., 'Trial')")
    resource_id: str | None = Field(None, description="ID of the resource affected")
    reason: str | None = Field(None, description="Reason for the change (required for updates)")
    changes: dict | None = Field(None, description="JSON object describing the change (before/after)")


class CFRLogCreate(CFRLogBase):
    """Schema for creating a new log entry."""

    user_id: int | None = None
    organization_id: int | None = None
    ip_address: str | None = None


class CFRLogResponse(CFRLogBase):
    """Schema for reading log entries."""

    id: UUID
    timestamp: datetime
    user_id: int | None
    organization_id: int | None
    ip_address: str | None
    signature: str
    previous_hash: str

    model_config = ConfigDict(from_attributes=True)
