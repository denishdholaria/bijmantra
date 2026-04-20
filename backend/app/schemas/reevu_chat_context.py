"""REEVU scoped chat context schema.

Defines the explicit task-scoped context envelope accepted by the canonical
REEVU chat API. This replaces broad frontend prompt dumps with structured
route, selection, and attachment metadata.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReevuContextAttachment(BaseModel):
    """A user-visible entity attached to a REEVU request."""

    kind: str = Field(..., description="Attachment kind, such as 'trial' or 'germplasm'")
    entity_id: str = Field(..., description="Stable identifier for the attached entity")
    label: str | None = Field(None, description="Optional UI label shown to the user")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Lightweight attachment metadata useful to REEVU routing",
    )


class ReevuScopedChatContext(BaseModel):
    """Task-scoped UI context sent with a REEVU chat request."""

    active_route: str | None = Field(None, description="Current frontend route")
    workspace: str | None = Field(None, description="Active workspace or division name")
    entity_type: str | None = Field(None, description="Primary entity type in focus")
    selected_entity_ids: list[str] = Field(
        default_factory=list,
        description="Currently selected entity identifiers",
    )
    active_filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Active UI filters relevant to the current task",
    )
    visible_columns: list[str] = Field(
        default_factory=list,
        description="Visible table or grid columns relevant to the task",
    )
    attached_context: list[ReevuContextAttachment] = Field(
        default_factory=list,
        description="Explicit user-visible context attachments",
    )