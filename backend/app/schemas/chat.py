"""
Chat API schemas for REEVU.

Request and response models for the chat API endpoints.
Extracted from backend/app/api/v2/chat.py.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.reevu_chat_context import ReevuScopedChatContext


class ChatMessage(BaseModel):
    """A single chat message"""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime | None = None


class ChatRequest(BaseModel):
    """Request to the canonical REEVU chat API."""

    message: str = Field(..., description="User's message")
    conversation_id: str | None = Field(None, description="Conversation ID for context")
    conversation_history: list[ChatMessage] | None = Field(
        None, description="Previous messages"
    )
    include_context: bool = Field(True, description="Whether to retrieve RAG context")
    context_limit: int = Field(5, ge=1, le=20, description="Max context documents")
    task_context: ReevuScopedChatContext | None = Field(
        None,
        description="Explicit task-scoped UI context for canonical REEVU orchestration",
    )
    preferred_provider: str | None = Field(None, description="Force specific LLM provider")
    # BYOK (Bring Your Own Key) - allows users to use their own API keys
    user_api_key: str | None = Field(
        None, description="User's API key for the provider (BYOK)"
    )
    user_model: str | None = Field(None, description="User's preferred model name")


class ContextDocument(BaseModel):
    """A document retrieved for context"""

    doc_id: str
    doc_type: str
    title: str | None
    content: str
    similarity: float
    source_id: str | None


class ChatResponse(BaseModel):
    """Response from REEVU"""

    request_id: str = Field(
        ..., description="Canonical request trace identifier for correlation"
    )
    message: str
    provider: str
    model: str
    model_confirmed: bool = Field(
        False, description="True if model name came from API response, False if from config"
    )
    context: list[ContextDocument] | None = None
    conversation_id: str | None = None
    suggestions: list[str] | None = None
    cached: bool = False
    latency_ms: float | None = None
    function_call: dict[str, Any] | None = Field(
        None, description="Function that was executed"
    )
    function_result: dict[str, Any] | None = Field(
        None, description="Result of function execution"
    )
    policy_validation: dict[str, Any] | None = Field(
        None,
        description="Policy validation metadata with evidence and calculation coverage",
    )
    evidence_envelope: dict[str, Any] | None = Field(
        None,
        description="Stage-B evidence envelope for grounding and explainability",
    )
    retrieval_audit: dict[str, Any] | None = Field(
        None,
        description="Stage-C retrieval execution audit metadata for canonical REEVU responses",
    )
    plan_execution_summary: dict[str, Any] | None = Field(
        None,
        description="Stage-C multi-domain execution plan summary",
    )
    comparison_result: dict[str, Any] | None = Field(
        None,
        description="Stage-C structured comparison/ranking result (populated only for ranking function results)",
    )


class ChatUsageProviderSnapshot(BaseModel):
    """Current routing snapshot for managed REEVU traffic."""

    active_provider: str | None = None
    active_model: str | None = None
    active_provider_source: str | None = None
    active_provider_source_label: str | None = None


class ChatUsageAttributionDimension(BaseModel):
    """Explicit support state for telemetry attribution dimensions."""

    supported: bool
    value: str | None = None
    reason: str | None = None


class ChatUsageAttributionSnapshot(BaseModel):
    """Usage attribution dimensions exposed by the current slice."""

    lane: ChatUsageAttributionDimension
    mission: ChatUsageAttributionDimension


class ChatUsageTokenTelemetry(BaseModel):
    """Supplemental token telemetry observed for managed REEVU traffic."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    coverage_state: str
    coverage_message: str


class ChatUsageSoftAlert(BaseModel):
    """Non-blocking quota alert state."""

    state: str
    threshold_basis: str
    percent_used: float
    message: str


class ChatUsageResponse(BaseModel):
    """Richer daily usage snapshot for REEVU-managed traffic."""

    used: int
    limit: int
    remaining: int
    request_percentage_used: float
    quota_authority: str
    provider: ChatUsageProviderSnapshot
    token_telemetry: ChatUsageTokenTelemetry
    attribution: ChatUsageAttributionSnapshot
    soft_alert: ChatUsageSoftAlert


class ContextRequest(BaseModel):
    """Request to get context for a query"""

    query: str
    doc_types: list[str] | None = None
    limit: int = Field(5, ge=1, le=20)


class ContextResponse(BaseModel):
    """Context retrieval response"""

    query: str
    documents: list[ContextDocument]
    total: int
