"""
REEVU Chat API
Multi-tier LLM-powered conversational assistant for plant breeding

Supports multiple LLM providers (in priority order):
1. Ollama (local, free, private)
2. Groq (free tier: 30 req/min)
3. Google AI Studio (free tier: 60 req/min)
4. HuggingFace (free tier)
5. FunctionGemma (function calling, 270M)
6. OpenAI (paid)
7. Anthropic (paid)
8. Template fallback (always works)

Endpoints:
- POST /api/v2/chat - Send a message to REEVU (with function calling!)
- POST /api/v2/chat/stream - Stream a message to REEVU (SSE)
- POST /api/v2/chat/context - Get relevant context for a query
- GET /api/v2/chat/status - Get LLM provider status
- GET /api/v2/chat/health - Health check
"""

import contextlib
import json
import logging
import os
import re
from time import perf_counter
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import uuid4

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.modules.ai.services.engine import (
    ConversationMessage,
    LLMProvider,
    MultiTierLLMService,
    get_llm_service,
)
from app.modules.ai.services.memory import (
    BreedingVectorService,
    EmbeddingService,
    SearchResult,
    VectorStoreService,
)

# Import domain services for function executor
from app.modules.breeding.services.cross_search_service import cross_search_service
from app.modules.breeding.services.trial_search_service import trial_search_service
from app.modules.breeding.services.breeding_value_service import breeding_value_service
from app.modules.germplasm.services.search_service import germplasm_search_service
from app.modules.spatial.services.location_search_service import location_search_service
from app.modules.environment.services.weather_service import weather_service

from app.modules.ai.services.quota import AIQuotaService
from app.modules.ai.services.tools import FunctionExecutor
from app.modules.ai.services.function_calling_service import FunctionCallingService
from app.modules.ai.services.capability_registry import CapabilityRegistry
from app.modules.ai.service import get_ai_provider_service
from app.schemas.reevu_chat_context import ReevuScopedChatContext
from app.schemas.reevu_envelope import CalculationStep, EvidenceRef, ReevuEnvelope, UncertaintyInfo
from app.modules.ai.services.reevu import ClaimItem, DeterministicRouter, EvidencePack, PolicyGuard, RecommendationFormatter, ReevuMetrics, ReevuPlanner, ReevuStage, ResponseValidator, ValidationResult, extract_numeric_citation_ids, is_non_claim_percentage, is_year_like_numeric_ref
from app.modules.ai.services.reevu_provenance_validator import validate_all as validate_provenance
from app.modules.ai.services.veena_service import VeenaService, get_veena_service


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/chat", tags=["REEVU AI"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class ChatMessage(BaseModel):
    """A single chat message"""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime | None = None


class ChatRequest(BaseModel):
    """Request to the canonical REEVU chat API."""
    message: str = Field(..., description="User's message")
    conversation_id: str | None = Field(None, description="Conversation ID for context")
    conversation_history: list[ChatMessage] | None = Field(None, description="Previous messages")
    include_context: bool = Field(True, description="Whether to retrieve RAG context")
    context_limit: int = Field(5, ge=1, le=20, description="Max context documents")
    task_context: ReevuScopedChatContext | None = Field(
        None,
        description="Explicit task-scoped UI context for canonical REEVU orchestration",
    )
    preferred_provider: str | None = Field(None, description="Force specific LLM provider")
    # BYOK (Bring Your Own Key) - allows users to use their own API keys
    user_api_key: str | None = Field(None, description="User's API key for the provider (BYOK)")
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
    message: str
    provider: str
    model: str
    model_confirmed: bool = Field(False, description="True if model name came from API response, False if from config")
    context: list[ContextDocument] | None = None
    conversation_id: str | None = None
    suggestions: list[str] | None = None
    cached: bool = False
    latency_ms: float | None = None
    function_call: dict[str, Any] | None = Field(None, description="Function that was executed")
    function_result: dict[str, Any] | None = Field(None, description="Result of function execution")
    policy_validation: dict[str, Any] | None = Field(
        None,
        description="Policy validation metadata with evidence and calculation coverage",
    )
    evidence_envelope: dict[str, Any] | None = Field(
        None,
        description="Stage-B evidence envelope for grounding and explainability",
    )
    plan_execution_summary: dict[str, Any] | None = Field(
        None,
        description="Stage-C multi-domain execution plan summary",
    )
    comparison_result: dict[str, Any] | None = Field(
        None,
        description="Stage-C structured comparison/ranking result (populated only for ranking function results)",
    )


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


# ============================================
# DEPENDENCIES
# ============================================

_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def get_vector_store(
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> VectorStoreService:
    return VectorStoreService(db, embedding_service)


async def get_request_llm_service(
    db: AsyncSession,
    current_user: User,
) -> Any:
    """Create a request-scoped LLM service using persisted org config when present."""
    base_service = get_llm_service()
    if not isinstance(base_service, MultiTierLLMService):
        return base_service

    registry = await get_ai_provider_service().load_registry(
        db,
        int(current_user.organization_id),
        is_superuser=bool(getattr(current_user, "is_superuser", False)),
    )
    llm_service = MultiTierLLMService()
    llm_service.set_provider_registry(registry)
    return llm_service


async def get_request_capability_registry(
    db: AsyncSession,
    current_user: User,
) -> CapabilityRegistry:
    agent_setting = await get_request_agent_setting(db, current_user)
    if agent_setting is None:
        return CapabilityRegistry()

    return CapabilityRegistry.from_agent_setting(agent_setting)


async def get_request_agent_setting(
    db: AsyncSession,
    current_user: User,
) -> Any | None:
    provider_service = get_ai_provider_service()
    get_agent_setting = getattr(provider_service, "get_agent_setting", None)
    if get_agent_setting is None:
        return None

    try:
        return await get_agent_setting(
            db,
            int(current_user.organization_id),
            is_superuser=bool(getattr(current_user, "is_superuser", False)),
        )
    except Exception as exc:
        logger.warning("[Veena] Prompt-mode agent settings unavailable, continuing without overrides: %s", exc)
        return None


async def get_breeding_service(
    vector_store: VectorStoreService = Depends(get_vector_store)
) -> BreedingVectorService:
    return BreedingVectorService(vector_store)


# ============================================
# HELPER FUNCTIONS
# ============================================

def format_context_for_llm(documents: list[SearchResult]) -> str:
    """Format retrieved documents as context for the LLM"""
    if not documents:
        return ""

    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(f"[{i}] {doc.doc_type.upper()}: {doc.title or 'Untitled'}")
        # Include relevant content
        content = doc.content[:500] if len(doc.content) > 500 else doc.content
        context_parts.append(f"    {content}")
        context_parts.append("")

    return "\n".join(context_parts)


def format_task_context_for_llm(task_context: ReevuScopedChatContext | None) -> str:
    """Format task-scoped UI state into a concise prompt fragment."""
    if task_context is None:
        return ""

    context_parts = ["ACTIVE USER TASK CONTEXT"]

    if task_context.active_route:
        context_parts.append(f"- active_route: {task_context.active_route}")
    if task_context.workspace:
        context_parts.append(f"- workspace: {task_context.workspace}")
    if task_context.entity_type:
        context_parts.append(f"- entity_type: {task_context.entity_type}")
    if task_context.selected_entity_ids:
        context_parts.append(
            "- selected_entity_ids: " + ", ".join(task_context.selected_entity_ids)
        )
    if task_context.active_filters:
        context_parts.append(
            "- active_filters: "
            + json.dumps(task_context.active_filters, ensure_ascii=True, sort_keys=True)
        )
    if task_context.visible_columns:
        context_parts.append(
            "- visible_columns: " + ", ".join(task_context.visible_columns)
        )
    if task_context.attached_context:
        context_parts.append("- attached_context:")
        for attachment in task_context.attached_context:
            label = f" ({attachment.label})" if attachment.label else ""
            context_parts.append(f"  - {attachment.kind}:{attachment.entity_id}{label}")

    if len(context_parts) == 1:
        return ""

    context_parts.append(
        "Use this scoped task context to interpret the request. Prefer it over broad application assumptions."
    )
    return "\n".join(context_parts)


def merge_prompt_context(*parts: str) -> str:
    """Join non-empty prompt context fragments with spacing."""
    return "\n\n".join(part for part in parts if part)


def _get_llm_routing_state(llm_service: Any) -> dict[str, Any]:
    """Extract request-scoped routing state from the active LLM service."""
    get_routing_state = getattr(llm_service, "get_routing_state", None)
    if callable(get_routing_state):
        return get_routing_state()

    registry = getattr(llm_service, "registry", None) or getattr(llm_service, "_registry", None)
    if registry is not None:
        registry_get_routing_state = getattr(registry, "get_routing_state", None)
        if callable(registry_get_routing_state):
            return registry_get_routing_state()

    return {
        "preferred_provider": None,
        "preferred_provider_only": False,
        "selection_mode": "priority_order",
    }


def _derive_routing_decisions(
    *,
    requested_provider: str | None,
    actual_provider: str | None,
    routing_state: dict[str, Any] | None,
) -> list[str]:
    """Summarize how runtime routing resolved a chat request."""
    decisions: list[str] = []
    normalized_requested = requested_provider.lower() if requested_provider else None
    normalized_actual = actual_provider.lower() if actual_provider else None
    normalized_preferred = None
    preferred_provider_only = False

    if routing_state:
        preferred_value = routing_state.get("preferred_provider")
        if isinstance(preferred_value, str) and preferred_value:
            normalized_preferred = preferred_value.lower()
        preferred_provider_only = bool(routing_state.get("preferred_provider_only"))

    if normalized_requested:
        decisions.append("request_override")
        if normalized_actual == normalized_requested:
            decisions.append("request_override_applied")
        else:
            decisions.append("request_override_fallback")
    elif normalized_preferred:
        decisions.append("managed_preferred_only" if preferred_provider_only else "managed_preferred")
        if normalized_actual == normalized_preferred:
            decisions.append("managed_preferred_hit")
        else:
            decisions.append("managed_preferred_miss")
    else:
        decisions.append("priority_order")

    if normalized_actual == "template":
        decisions.append("template_fallback")

    return decisions


def generate_suggestions(message: str, response: str) -> list[str]:
    """Generate follow-up suggestions based on conversation"""
    message_lower = message.lower()

    if "germplasm" in message_lower or "variety" in message_lower:
        return [
            "Show me similar varieties",
            "What are the key traits?",
            "Find disease-resistant options"
        ]

    if "trial" in message_lower:
        return [
            "Show trial results",
            "Compare with other trials",
            "What's the best performer?"
        ]

    if "cross" in message_lower or "breeding" in message_lower:
        return [
            "Suggest optimal parents",
            "Calculate genetic distance",
            "Show pedigree information"
        ]

    if "disease" in message_lower or "resistance" in message_lower:
        return [
            "List resistance genes",
            "Show screening protocols",
            "Find resistant varieties"
        ]

    # Default suggestions
    return [
        "Tell me more",
        "Search germplasm",
        "Show active trials"
    ]


def _build_evidence_pack(
    context_docs: list[SearchResult] | None,
    function_call_name: str | None = None,
    function_result: dict[str, Any] | None = None,
) -> EvidencePack:
    """Assemble an evidence pack from retrieved context and tool execution artifacts."""
    evidence_refs: set[str] = set()
    calculation_ids: set[str] = set()

    for doc in context_docs or []:
        if doc.doc_id:
            evidence_refs.add(str(doc.doc_id))
        if doc.source_id:
            evidence_refs.add(str(doc.source_id))

    if function_result:
        for key in ("evidence_refs", "source_ids", "doc_ids"):
            values = function_result.get(key)
            if isinstance(values, list):
                evidence_refs.update(str(v) for v in values if v is not None)

        calc_values = function_result.get("calculation_ids")
        if isinstance(calc_values, list):
            calculation_ids.update(str(v) for v in calc_values if v is not None)

        payload = function_result.get("data")
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    if item.get("doc_id") is not None:
                        evidence_refs.add(str(item["doc_id"]))
                    if item.get("source_id") is not None:
                        evidence_refs.add(str(item["source_id"]))
                    if item.get("id") is not None:
                        evidence_refs.add(str(item["id"]))

    if function_call_name and function_call_name.startswith(("calculate_", "analyze_", "predict_")):
        calculation_ids.add(f"fn:{function_call_name}")

    return EvidencePack(evidence_refs=evidence_refs, calculation_ids=calculation_ids)


def _extract_claims_for_validation(content: str, evidence_pack: EvidencePack) -> list[ClaimItem]:
    """Extract minimal claim structure for deterministic policy validation."""
    claims: list[ClaimItem] = []
    seen_claim_keys: set[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = set()

    def _append_claim(claim: ClaimItem) -> None:
        normalized_statement = claim.statement.strip().lower()
        normalized_refs = tuple(ref.strip().lower() for ref in claim.evidence_refs)
        normalized_calcs = tuple(calc.strip() for calc in claim.calculation_ids)
        key = (claim.claim_type, normalized_statement, normalized_refs, normalized_calcs)
        if key in seen_claim_keys:
            return
        seen_claim_keys.add(key)
        claims.append(claim)

    sentences = [
        segment.strip()
        for segment in re.split(r"(?<=[.!?])\s+|\n+", content)
        if segment and segment.strip()
    ]
    if not sentences:
        sentences = [content]

    for sentence in sentences:
        sentence_calc_ids = tuple(
            calc.strip() for calc in re.findall(r"\[\[calc:([^\]]+)\]\]", sentence) if calc.strip()
        )

        # Optional explicit tags for future stricter contracts.
        for ref in re.findall(r"\[\[ref:([^\]]+)\]\]", sentence):
            _append_claim(
                ClaimItem(
                    statement=f"reference:{ref}",
                    claim_type="reference",
                    evidence_refs=(ref.strip(),),
                )
            )

        for cited_id in extract_numeric_citation_ids(sentence):
            _append_claim(
                ClaimItem(
                    statement=f"reference:[{cited_id}]",
                    claim_type="reference",
                    evidence_refs=(cited_id,),
                )
            )

        for calc in sentence_calc_ids:
            _append_claim(
                ClaimItem(
                    statement=f"quantitative:{calc}",
                    claim_type="quantitative",
                    calculation_ids=(calc,),
                )
            )

        # Interpret percentage statements as quantitative claims that require
        # deterministic calculation provenance.
        for percentage_phrase in re.findall(r"\b\d{1,3}(?:\.\d+)?%\s*\w+", sentence):
            if is_non_claim_percentage(percentage_phrase):
                continue
            calculation_ids = (
                sentence_calc_ids
                if sentence_calc_ids
                else tuple(sorted(evidence_pack.calculation_ids))
            )
            if not calculation_ids:
                calculation_ids = ("missing_calculation",)

            _append_claim(
                ClaimItem(
                    statement=f"quantitative:{percentage_phrase.strip()}",
                    claim_type="quantitative",
                    calculation_ids=calculation_ids,
                )
            )

    # Heuristic quantitative check: if there are many non-year numeric values but no
    # available calculations or evidence, force a validation failure.
    non_claim_percentage_tokens: set[str] = set()
    for phrase in re.findall(r"\b\d{1,3}(?:\.\d+)?%\s*\w+", content):
        if is_non_claim_percentage(phrase):
            token = phrase.split("%", maxsplit=1)[0].strip()
            if token:
                non_claim_percentage_tokens.add(f"{token}%")
                non_claim_percentage_tokens.add(token)

    raw_numeric_tokens = re.findall(r"\b\d+(?:\.\d+)?%?\b", content)
    numeric_tokens: list[str] = []
    for token in raw_numeric_tokens:
        if token in non_claim_percentage_tokens:
            continue
        normalized = token[:-1] if token.endswith("%") else token
        if normalized.isdigit() and is_year_like_numeric_ref(normalized):
            continue
        numeric_tokens.append(token)

    has_quantitative_density = len(numeric_tokens) >= 3
    if has_quantitative_density and not evidence_pack.calculation_ids and not evidence_pack.evidence_refs:
        _append_claim(
            ClaimItem(
                statement="quantitative-claim-without-evidence",
                claim_type="quantitative",
                calculation_ids=("missing_calculation",),
            )
        )

    return claims


def _validate_response_content(
    content: str,
    context_docs: list[SearchResult] | None,
    function_call_name: str | None = None,
    function_result: dict[str, Any] | None = None,
) -> tuple[ValidationResult, EvidencePack]:
    """Run REEVU response validation against assembled evidence pack."""
    evidence_pack = _build_evidence_pack(context_docs, function_call_name, function_result)
    claims = _extract_claims_for_validation(content, evidence_pack)
    validator = ResponseValidator()
    validation = validator.validate_claims(claims=claims, evidence_pack=evidence_pack)

    # Stage B hardening: content-level citation/quantitative checks are part of
    # blocking validation, not just envelope metadata.
    content_flags = validator.check_citation_mismatch(content, evidence_pack)
    content_flags.extend(validator.check_percentage_without_calc(content, evidence_pack))

    if content_flags:
        merged_errors = list(validation.errors)
        for flag in content_flags:
            if flag not in merged_errors:
                merged_errors.append(flag)
        validation = ValidationResult(valid=False, errors=tuple(merged_errors))

    return validation, evidence_pack


def _build_safe_failure_payload(
    error_category: str,
    searched: list[str] | None = None,
    missing: list[str] | None = None,
    next_steps: list[str] | None = None,
) -> dict[str, Any]:
    """Create a standardized safe-failure payload for user-facing AI failures."""
    return {
        "error_category": error_category,
        "searched": searched or [],
        "missing": missing or [],
        "next_steps": next_steps or [],
    }


def _build_reevu_envelope(
    content: str,
    evidence_pack: EvidencePack,
    validation: ValidationResult,
    context_docs: list[SearchResult] | None = None,
    function_call_name: str | None = None,
) -> dict[str, Any]:
    """Construct the Stage-B evidence envelope from validation artefacts."""
    evidence_refs = [
        EvidenceRef(
            source_type="rag",
            entity_id=str(ref),
            query_or_method="vector_search",
        )
        for ref in evidence_pack.evidence_refs
    ]
    calculation_steps = [
        CalculationStep(step_id=str(calc_id))
        for calc_id in evidence_pack.calculation_ids
    ]
    claims = _extract_claims_for_validation(content, evidence_pack)
    claim_strings = [c.statement for c in claims]

    # Validation errors already include Stage B content-level checks.
    policy_flags = list(validation.errors)

    confidence = 1.0 if validation.valid else max(0.0, 1.0 - 0.2 * len(validation.errors))
    missing_data: list[str] = []
    if not evidence_pack.evidence_refs:
        missing_data.append("no_rag_context")
    if not evidence_pack.calculation_ids and function_call_name:
        missing_data.append("no_calculation_ids")

    envelope = ReevuEnvelope(
        claims=claim_strings,
        evidence_refs=evidence_refs,
        calculation_steps=calculation_steps,
        uncertainty=UncertaintyInfo(confidence=confidence, missing_data=missing_data),
        policy_flags=policy_flags,
    )

    # Run provenance checks and merge flags.
    provenance_flags = validate_provenance(envelope)
    if provenance_flags:
        envelope = envelope.model_copy(update={"policy_flags": envelope.policy_flags + provenance_flags})

    envelope_payload = envelope.model_dump()
    envelope_payload["calculations"] = envelope_payload.get("calculation_steps", [])
    return envelope_payload


def _maybe_format_comparison(
    function_result: dict[str, Any] | None,
    function_call_name: str | None = None,
    domains_involved: list[str] | None = None,
) -> dict[str, Any] | None:
    """If the function result contains rankable candidates, format a structured comparison.

    Returns ``ComparisonResult.model_dump()`` if candidates are detected, ``None`` otherwise.
    This is additive: callers that ignore the return value retain full backward compatibility.
    """
    if not function_result:
        return None

    data = function_result.get("data")
    if not isinstance(data, list) or len(data) == 0:
        return None

    # Heuristic: treat as rankable if items are dicts with score/name/candidate keys.
    _RANK_KEYS = {"score", "name", "candidate"}
    if not all(isinstance(item, dict) for item in data):
        return None
    if not any(_RANK_KEYS & set(item.keys()) for item in data):
        return None

    formatter = RecommendationFormatter()
    methodology = f"function:{function_call_name}" if function_call_name else ""
    result = formatter.format_comparison(
        data,
        methodology=methodology,
        domains_used=domains_involved,
    )
    return result.model_dump()


# ============================================
# ENDPOINTS
# ============================================

@router.post("/", response_model=ChatResponse)
async def chat_with_veena(
    request: ChatRequest,
    breeding_service: BreedingVectorService = Depends(get_breeding_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    veena_service: VeenaService = Depends(get_veena_service)

):
    """
    REEVU uses RAG (Retrieval-Augmented Generation) combined with
    multi-tier LLM support to provide intelligent, contextual responses.

    **NEW: Function Calling with FunctionGemma**
    REEVU can now execute actions like searching germplasm, creating trials,
    comparing varieties, and more!

    **Free LLM Options:**
    - Ollama (local): Install from ollama.ai
    - Groq: Get free API key from console.groq.com
    - Google AI: Get free key from aistudio.google.com
    - FunctionGemma: Use HuggingFace API key
    """
    llm_service = await get_request_llm_service(db, current_user)
    agent_setting = await get_request_agent_setting(db, current_user)
    capability_registry = CapabilityRegistry.from_agent_setting(agent_setting)
    if agent_setting is None:
        capability_registry = CapabilityRegistry()
    user_id = int(current_user.id)
    organization_id = int(current_user.organization_id)
    user_ref = SimpleNamespace(id=user_id, organization_id=organization_id)
    context_docs = None
    context_response = None
    context_text = None
    scoped_task_context = format_task_context_for_llm(request.task_context)
    function_call_result = None
    function_call_data = None

    # Step 1: Check if this is a function call request
    function_calling_service = FunctionCallingService(
        api_key=os.getenv("HUGGINGFACE_API_KEY") or os.getenv("FUNCTIONGEMMA_API_KEY"),
        function_schemas=capability_registry.get_allowed_functions(),
    )
    
    start_time = perf_counter()

    # ENFORCE QUOTA (Hybrid Tiered Model)
    # If user provides their own key (BYOK), skip quota.
    # Otherwise, check organization daily limit.
    if not request.user_api_key:
        try:
            await AIQuotaService.check_and_increment_usage(
                db,
                organization_id=organization_id,
                increment=True
            )
        except HTTPException as quota_http_error:
            # Preserve explicit quota-limit behavior.
            raise quota_http_error
        except Exception as quota_error:
            # Fail-open on quota infrastructure errors so chat remains available.
            logger.warning(f"[Veena] Quota check skipped due to error: {quota_error}")
            with contextlib.suppress(Exception):
                await db.rollback()

    # COGNITIVE LOAD: Fetch User Context
    await veena_service.get_or_create_user_context(user_ref)
    await veena_service.update_interaction_stats(user_id)

    try:
        function_call = await function_calling_service.detect_function_call(
            user_message=request.message,
            conversation_history=[msg.model_dump() for msg in (request.conversation_history or [])]
        )

        if function_call:
            logger.info(f"[Veena] Function call detected: {function_call.name}")

            # Step 2: Execute the function
            function_executor = FunctionExecutor(
                db,
                capability_registry=capability_registry,
                cross_search_service=cross_search_service,
                trial_search_service=trial_search_service,
                germplasm_search_service=germplasm_search_service,
                location_search_service=location_search_service,
                weather_service=weather_service,
                breeding_value_service=breeding_value_service,
            )
            try:
                function_call_result = await function_executor.execute(
                    function_call.name,
                    function_call.parameters
                )
                function_call_data = function_call.to_dict()

                # Step 3: Format the result as a natural language response
                result_summary = json.dumps(function_call_result, indent=2)
                format_prompt = f"""The user asked: "{request.message}"

I executed the function: {function_call.name}
With parameters: {json.dumps(function_call.parameters)}

Result:
{result_summary}

Please provide a natural, friendly response to the user explaining what was found.
CRITICAL: Base your answer STRICTLY on the 'Result' data provided above. Do not hallucinate additional varieties or traits not present in the data.
If the result is empty, clearly state that no matching records were found in the database.
When citing concrete evidence IDs from records, annotate using [[ref:<id>]].
When presenting computed values derived from execution, annotate using [[calc:fn:{function_call.name}]]."""

                llm_response = await llm_service.chat(
                    user_message=format_prompt,
                    conversation_history=None,
                    context=scoped_task_context or None,
                    organization_id=organization_id,
                    user_id=user_id,
                    system_prompt_override=getattr(agent_setting, "system_prompt_override", None),
                    prompt_mode_capabilities=getattr(agent_setting, "prompt_mode_capabilities", None),
                )

                validation, evidence_pack = _validate_response_content(
                    content=llm_response.content,
                    context_docs=context_docs,
                    function_call_name=function_call.name,
                    function_result=function_call_result,
                )
                policy_validation_payload = {
                    "valid": validation.valid,
                    "error_count": len(validation.errors),
                    "errors": list(validation.errors),
                    "evidence_count": len(evidence_pack.evidence_refs),
                    "calculation_count": len(evidence_pack.calculation_ids),
                }
                if not validation.valid:
                    policy_validation_payload["safe_failure"] = _build_safe_failure_payload(
                        error_category="insufficient_evidence",
                        searched=["function_result", "retrieved_context", "response_validation"],
                        missing=["grounded evidence for one or more claims"],
                        next_steps=[
                            "Retry with narrower filters (crop, trial, location, season).",
                            "Request source IDs and verify records before action.",
                        ],
                    )
                    llm_response.content = (
                        "I could not fully verify this answer against current evidence. "
                        "Please rerun with more specific filters or review source records before taking action."
                    )

                # Generate suggestions based on function executed
                suggestions = [
                    "Show me more details",
                    "Export this data",
                    "What else can you do?"
                ]

                return ChatResponse(
                    message=llm_response.content,
                    provider=llm_response.provider.value,
                    model=llm_response.model,
                    model_confirmed=llm_response.model_confirmed,
                    context=None,
                    conversation_id=request.conversation_id,
                    suggestions=suggestions,
                    cached=False,
                    latency_ms=llm_response.latency_ms,
                    function_call=function_call_data,
                    function_result=function_call_result,
                    policy_validation=policy_validation_payload,
                    evidence_envelope=_build_reevu_envelope(
                        content=llm_response.content,
                        evidence_pack=evidence_pack,
                        validation=validation,
                        context_docs=context_docs,
                        function_call_name=function_call.name,
                    ),
                    comparison_result=_maybe_format_comparison(
                        function_call_result,
                        function_call_name=function_call.name,
                    ),
                )

            except Exception as e:
                logger.error(f"[Veena] Function execution error: {e}")
                # Fall through to regular chat if function execution fails

    except Exception as e:
        logger.warning(f"[Veena] Function detection error: {e}, proceeding with regular chat")

    # Step 4: Regular conversational response (no function call detected or execution failed)

    # Retrieve relevant context if enabled
    if request.include_context:
        try:
            context_docs = await breeding_service.search_breeding_knowledge(
                query=request.message,
                limit=request.context_limit
            )

            if context_docs:
                context_response = [
                    ContextDocument(
                        doc_id=doc.doc_id,
                        doc_type=doc.doc_type,
                        title=doc.title,
                        content=doc.content[:500],
                        similarity=doc.similarity,
                        source_id=doc.source_id
                    )
                    for doc in context_docs
                ]
                context_text = format_context_for_llm(context_docs)
        except Exception as e:
            print(f"[Veena] Context retrieval error: {e}")

    context_text = merge_prompt_context(scoped_task_context, context_text or "")

    # Convert conversation history
    history = None
    if request.conversation_history:
        history = [
            ConversationMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp or datetime.now(UTC)
            )
            for msg in request.conversation_history
        ]

    # Parse preferred provider
    preferred = None
    if request.preferred_provider:
        with contextlib.suppress(ValueError):
            preferred = LLMProvider(request.preferred_provider.lower())

    # Generate response using LLM
    # If user provided their own API key (BYOK), use it
    llm_response = await llm_service.chat(
        user_message=request.message,
        conversation_history=history,
        context=context_text,
        preferred_provider=preferred,
        organization_id=organization_id,
        user_id=user_id,
        user_api_key=request.user_api_key,
        user_model=request.user_model,
        system_prompt_override=getattr(agent_setting, "system_prompt_override", None),
        prompt_mode_capabilities=getattr(agent_setting, "prompt_mode_capabilities", None),
    )

    validation, evidence_pack = _validate_response_content(
        content=llm_response.content,
        context_docs=context_docs,
        function_call_name=None,
        function_result=None,
    )
    policy_validation_payload = {
        "valid": validation.valid,
        "error_count": len(validation.errors),
        "errors": list(validation.errors),
        "evidence_count": len(evidence_pack.evidence_refs),
        "calculation_count": len(evidence_pack.calculation_ids),
    }
    if not validation.valid:
        policy_validation_payload["safe_failure"] = _build_safe_failure_payload(
            error_category="insufficient_evidence",
            searched=["retrieved_context", "response_validation"],
            missing=["grounded evidence for one or more claims"],
            next_steps=[
                "Narrow the question by crop, trial, location, or date range.",
                "Ask for cited record IDs and verify before decisions.",
            ],
        )
        llm_response.content = (
            "I cannot verify all claims in a grounded way from the currently available evidence. "
            "Try a narrower query or provide additional context to improve confidence."
        )

    suggestions = generate_suggestions(request.message, llm_response.content)

    # MEMORY ENCODING: Save conversation snippet
    # Only save if meaningful (not empty)
    if llm_service and llm_response.content:
        await veena_service.save_episodic_memory(
            user=user_ref,
            content=f"User: {request.message}\nVeena: {llm_response.content[:200]}...",
            source_type="chat",
            importance=0.3
        )
        
    total_latency = perf_counter() - start_time
    routing_state = _get_llm_routing_state(llm_service)
    ReevuMetrics.get().record_request(
        domain="unknown",  # In non-stream, we don't have the planner domain yet.
        function_name=function_call_result.get("name", "") if function_call_result else "",
        status="safe_failure" if not validation.valid else "ok",
        latency_seconds=total_latency,
        stage="total",
        policy_flags=list(validation.errors) if validation else [],
        provider=llm_response.provider.value,
        safe_failure_reason="insufficient_evidence" if not validation.valid else None,
        routing_decisions=_derive_routing_decisions(
            requested_provider=request.preferred_provider,
            actual_provider=llm_response.provider.value,
            routing_state=routing_state,
        ),
    )


    return ChatResponse(
        message=llm_response.content,
        provider=llm_response.provider.value,
        model=llm_response.model,
        model_confirmed=llm_response.model_confirmed,
        context=context_response,
        conversation_id=request.conversation_id,
        suggestions=suggestions,
        cached=llm_response.cached,
        latency_ms=llm_response.latency_ms,
        policy_validation=policy_validation_payload,
        evidence_envelope=_build_reevu_envelope(
            content=llm_response.content,
            evidence_pack=evidence_pack,
            validation=validation,
            context_docs=context_docs,
            function_call_name=None,
        ),
    )


@router.post("/context", response_model=ContextResponse)
async def get_context(
    request: ContextRequest,
    breeding_service: BreedingVectorService = Depends(get_breeding_service)
):
    """
    Get relevant context documents for a query.

    Use this to retrieve RAG context without generating a response.
    Useful for custom integrations or debugging.
    """
    docs = await breeding_service.search_breeding_knowledge(
        query=request.query,
        include_germplasm="germplasm" in (request.doc_types or []) or request.doc_types is None,
        include_trials="trial" in (request.doc_types or []) or request.doc_types is None,
        include_protocols="protocol" in (request.doc_types or []) or request.doc_types is None,
        limit=request.limit
    )

    return ContextResponse(
        query=request.query,
        documents=[
            ContextDocument(
                doc_id=doc.doc_id,
                doc_type=doc.doc_type,
                title=doc.title,
                content=doc.content,
                similarity=doc.similarity,
                source_id=doc.source_id
            )
            for doc in docs
        ],
        total=len(docs)
    )


@router.get("/status")
async def get_llm_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get status of all LLM providers.

    Shows which providers are configured and available.
    """
    llm_service = await get_request_llm_service(db, current_user)
    return await llm_service.get_status()


@router.get("/usage")
async def get_ai_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get daily AI usage statistics for the organization.
    Returns {used, limit, remaining}.
    """
    return await AIQuotaService.get_usage_stats(db, current_user.organization_id)


@router.get("/health")
async def reevu_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check REEVU AI health status"""
    llm_service = await get_request_llm_service(db, current_user)
    status = await llm_service.get_status()

    return {
        "status": "healthy",
        "assistant": "REEVU",
        "active_provider": status["active_provider"],
        "active_model": status["active_model"],
        "active_provider_source": status.get("active_provider_source", "none"),
        "active_provider_source_label": status.get("active_provider_source_label", "Unavailable"),
        "capabilities": [
            "semantic_search",
            "germplasm_lookup",
            "protocol_search",
            "trial_information",
            "similarity_matching",
            "natural_conversation"
        ],
        "rag_enabled": True,
        "llm_enabled": status["active_provider"] != "template",
        "free_tier_available": any(
            p["available"] and p["free_tier"]
            for p in status["providers"].values()
        )
    }


async def veena_health():
    """Compatibility alias for legacy imports."""
    return await reevu_health()


@router.get("/metrics")
async def reevu_metrics():
    """Return REEVU runtime metrics snapshot.

    Non-authenticated endpoint for scraping by observability tools.
    Returns counter and histogram data collected since process start.
    """
    return ReevuMetrics.get().get_metrics_snapshot()


@router.get("/diagnostics")
async def reevu_diagnostics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return operator-facing REEVU routing and validation diagnostics."""
    if not bool(getattr(current_user, "is_superuser", False)):
        raise HTTPException(status_code=403, detail="Superuser access required")

    llm_service = await get_request_llm_service(db, current_user)
    status = await llm_service.get_status()
    metrics_snapshot = ReevuMetrics.get().get_metrics_snapshot()
    diagnostics_snapshot = ReevuMetrics.get().get_diagnostics_snapshot()
    routing_state = _get_llm_routing_state(llm_service)

    providers = [
        {
            "provider": provider_name,
            "available": provider_state.get("available", False),
            "free_tier": provider_state.get("free_tier", False),
        }
        for provider_name, provider_state in sorted(status.get("providers", {}).items())
    ]

    return {
        "assistant": "REEVU",
        "active_provider": status.get("active_provider", "unknown"),
        "active_model": status.get("active_model", "unknown"),
        "active_provider_source": status.get("active_provider_source", "none"),
        "active_provider_source_label": status.get("active_provider_source_label", "Unavailable"),
        "uptime_seconds": metrics_snapshot.get("uptime_seconds", 0),
        "total_requests": metrics_snapshot.get("total_requests", 0),
        "providers": providers,
        "routing_state": routing_state,
        "request_statuses": diagnostics_snapshot.get("request_statuses", []),
        "provider_latencies": diagnostics_snapshot.get("provider_latencies", []),
        "safe_failures": diagnostics_snapshot.get("safe_failures", []),
        "routing_decisions": diagnostics_snapshot.get("routing_decisions", []),
        "policy_flags": metrics_snapshot.get("policy_flags", []),
    }


@router.post("/stream")
async def stream_chat_with_veena(
    request: ChatRequest,
    breeding_service: BreedingVectorService = Depends(get_breeding_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    veena_service: VeenaService = Depends(get_veena_service)
):
    """
    Stream a message to REEVU AI assistant using Server-Sent Events (SSE).

    Returns real-time streaming response with text chunks as they are generated.
    The response is formatted as SSE with 'data: ' prefixed lines.

    **Streaming Format:**
    - First event: `data: {"type": "start", "provider": "...", "model": "..."}`
    - Content events: `data: {"type": "chunk", "content": "..."}`
    - Proposal event: `data: {"type": "proposal_created", "data": {...}}`
    - Final event: `data: {"type": "done"}`
    - Error event: `data: {"type": "error", "message": "..."}`
    """
    import asyncio

    llm_service = await get_request_llm_service(db, current_user)
    agent_setting = await get_request_agent_setting(db, current_user)
    capability_registry = CapabilityRegistry.from_agent_setting(agent_setting)
    if agent_setting is None:
        capability_registry = CapabilityRegistry()
    policy_guard = PolicyGuard()
    user_id = int(current_user.id)
    organization_id = int(current_user.organization_id)
    user_ref = SimpleNamespace(id=user_id, organization_id=organization_id)
    context_docs = None
    context_text = None
    context_doc_ids: list[str] = []
    scoped_task_context = format_task_context_for_llm(request.task_context)
    request_id = str(uuid4())
    stage_started_at: dict[str, float] = {}

    def stage_event(stage: ReevuStage, status: str, **extra: Any) -> str:
        stage_key = stage.value
        now_perf = perf_counter()
        payload: dict[str, Any] = {
            "type": "stage",
            "request_id": request_id,
            "stage": stage_key,
            "status": status,
            "ts": datetime.now(UTC).isoformat(),
        }

        if status == "started":
            stage_started_at[stage_key] = now_perf
        elif status == "completed":
            started_at = stage_started_at.get(stage_key)
            payload["latency_ms"] = (
                round((now_perf - started_at) * 1000, 3)
                if started_at is not None
                else 0.0
            )

        payload.update(extra)
        return f"data: {json.dumps(payload)}\n\n"

    # 1. Retrieve relevant context if enabled
    if request.include_context:
        try:
            access_decision = policy_guard.evaluate_access(
                domain_scope="breeding",
                entity="breeding_knowledge",
                operation="read",
            )
            if not access_decision.allowed:
                raise HTTPException(status_code=403, detail=access_decision.reason)

            context_docs = await breeding_service.search_breeding_knowledge(
                query=request.message,
                limit=request.context_limit
            )

            if context_docs:
                context_text = format_context_for_llm(context_docs)
                context_doc_ids = [doc.doc_id for doc in context_docs]
        except Exception as e:
            logger.warning(f"[Veena] Context retrieval error for streaming: {e}")

    context_text = merge_prompt_context(scoped_task_context, context_text or "")

    # 2. Convert conversation history
    history = None
    if request.conversation_history:
        history = [
            ConversationMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp or datetime.now(UTC)
            )
            for msg in request.conversation_history
        ]

    # 3. Parse preferred provider
    preferred = None
    if request.preferred_provider:
        with contextlib.suppress(ValueError):
            preferred = LLMProvider(request.preferred_provider.lower())

    # ENFORCE QUOTA FOR STREAMING
    if not request.user_api_key:
        # We increment at start of stream. If stream fails, we still count it (simpler)
        # Or we could increment at end, but start protects against DOS.
        try:
            await AIQuotaService.check_and_increment_usage(
                db,
                organization_id=organization_id,
                increment=True
            )
        except HTTPException as quota_http_error:
            # Preserve explicit quota-limit behavior.
            raise quota_http_error
        except Exception as quota_error:
            # Fail-open on quota infrastructure errors so stream remains available.
            logger.warning(f"[Veena] Streaming quota check skipped due to error: {quota_error}")
            with contextlib.suppress(Exception):
                await db.rollback()

    # COGNITIVE LOAD
    await veena_service.get_or_create_user_context(user_ref)
    await veena_service.update_interaction_stats(user_id)
    
    start_time = perf_counter()

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream with proper error handling and keepalive"""
        try:
            yield stage_event(ReevuStage.INTENT_SCOPE, "started")

            # A. Detect Function Call
            function_calling_service = FunctionCallingService(
                api_key=os.getenv("HUGGINGFACE_API_KEY") or os.getenv("FUNCTIONGEMMA_API_KEY"),
                function_schemas=capability_registry.get_allowed_functions(),
            )

            function_call = None
            function_result = None
            prompt_override = None
            accumulated_response = ""
            plan_summary: dict[str, Any] | None = None

            try:
                yield stage_event(ReevuStage.PLAN_GENERATION, "started")
                # Detect function call (async)
                function_call = await function_calling_service.detect_function_call(
                    user_message=request.message,
                    conversation_history=[msg.model_dump() for msg in (request.conversation_history or [])]
                )

                # Stage C: Build multi-domain execution plan.
                planner = ReevuPlanner()
                plan = planner.build_plan(
                    request.message,
                    function_call_name=function_call.name if function_call else None,
                )
                plan_summary = {
                    "plan_id": plan.plan_id,
                    "is_compound": plan.is_compound,
                    "domains_involved": plan.domains_involved,
                    "total_steps": plan.total_steps,
                    "steps": [s.model_dump() for s in plan.steps],
                }

                # Stage C: Deterministic routing check.
                det_router = DeterministicRouter()
                routing = det_router.get_routing_decision(
                    request.message,
                    function_call_name=function_call.name if function_call else None,
                )
                if routing.should_route:
                    plan_summary["deterministic_routing"] = routing.model_dump()

                yield stage_event(
                    ReevuStage.PLAN_GENERATION,
                    "completed",
                    function_call_detected=bool(function_call),
                    plan_is_compound=plan.is_compound,
                    domains_involved=plan.domains_involved,
                )
            except Exception as e:
                logger.warning(f"[Veena] Function detection failed: {e}")
                yield stage_event(ReevuStage.PLAN_GENERATION, "failed", error=str(e))

            # B. Get Status / Provider Info
            # Same logic as before for determining provider
            actual_provider = "unknown"
            actual_model = "unknown"

            if request.user_api_key and request.preferred_provider:
                actual_provider = request.preferred_provider
                actual_model = request.user_model or "default"
            else:
                status = await llm_service.get_status()
                actual_provider = status.get("active_provider", "unknown")
                actual_model = status.get("active_model", "unknown")

            # C. Send Start Event
            start_event = json.dumps({
                "type": "start",
                "request_id": request_id,
                "provider": actual_provider,
                "model": actual_model
            })
            yield f"data: {start_event}\n\n"

            # Check configuration availability (skip if func call detected as we might use different logic?)
            # Actually, we still need LLM for explanation.
            has_byok = request.user_api_key and request.preferred_provider
            if not has_byok and not function_call: # If function call, we might proceed even if template mode? No.
                 status = await llm_service.get_status()
                 if status.get("active_provider") == "template" and not any(
                     p.get("available") for p in status.get("providers", {}).values()
                 ):
                     # Template mode warning
                     yield f'data: {json.dumps({"type": "chunk", "request_id": request_id, "content": "I\'m running in template mode without an AI backend. "})}\n\n'
                     yield f'data: {json.dumps({"type": "chunk", "request_id": request_id, "content": "Please configure an AI provider for full features."})}\n\n'
                     yield f'data: {json.dumps({"type": "done", "request_id": request_id})}\n\n'
                     return

            # D. Execute Function (if detected)
            if function_call:
                logger.info(f"[Veena] Executing function in stream: {function_call.name}")
                yield stage_event(ReevuStage.DATA_EXECUTION, "started", function_name=function_call.name)

                # Notify client about function execution (optional, maybe just show thinking?)
                # yield f'data: {json.dumps({"type": "chunk", "content": "🔄 processing request..."})}\n\n'

                function_executor = FunctionExecutor(
                    db,
                    capability_registry=capability_registry,
                    cross_search_service=cross_search_service,
                    trial_search_service=trial_search_service,
                    germplasm_search_service=germplasm_search_service,
                    location_search_service=location_search_service,
                    weather_service=weather_service,
                    breeding_value_service=breeding_value_service,
                )
                try:
                    function_result = await function_executor.execute(
                        function_call.name,
                        function_call.parameters
                    )
                    yield stage_event(
                        ReevuStage.DATA_EXECUTION,
                        "completed",
                        function_name=function_call.name,
                    )

                    # Check if Proposal
                    if function_result.get("result_type") == "proposal_created":
                        proposal_data = function_result.get("data", {})
                        # Emit specific Proposal Event
                        proposal_event = json.dumps({
                            "type": "proposal_created",
                            "data": proposal_data
                        })
                        yield f"data: {proposal_event}\n\n"

                    # Prepare Prompt for Explanation
                    result_summary = json.dumps(function_result, indent=2)
                    prompt_override = f"""The user asked: "{request.message}"

I executed the function: {function_call.name}
With parameters: {json.dumps(function_call.parameters)}

Result:
{result_summary}

Please provide a natural response explaining this to the user."""

                    if function_call.name.startswith(("calculate_", "analyze_", "predict_")):
                        prompt_override += (
                            "\nWhen presenting computed numeric claims, annotate with [[calc:fn:"
                            + function_call.name
                            + "]]."
                        )

                    prompt_override += (
                        "\nWhen citing concrete source record IDs, annotate each with [[ref:<id>]]."
                    )

                except Exception as e:
                    logger.error(f"[Veena] Function execution error: {e}")
                    yield stage_event(ReevuStage.DATA_EXECUTION, "failed", error=str(e))
                    error_event = json.dumps(
                        {
                            "type": "chunk",
                            "request_id": request_id,
                            "content": f"\n\n[Error executing action: {str(e)}]",
                        }
                    )
                    yield f"data: {error_event}\n\n"

            # E. Stream Response (Regular or Function Explanation)
            message_to_send = prompt_override if prompt_override else request.message
            yield stage_event(ReevuStage.ANSWER_SYNTHESIS, "started")

            chunk_count = 0
            async for chunk in llm_service.stream_chat(
                user_message=message_to_send,
                conversation_history=history if not prompt_override else None, # Clean history if explaining function? Or keep it? keeping it is better for context.
                context=context_text, # Still include RAG context? Yes.
                preferred_provider=preferred,
                user_api_key=request.user_api_key,
                user_model=request.user_model,
                system_prompt_override=getattr(agent_setting, "system_prompt_override", None),
                prompt_mode_capabilities=getattr(agent_setting, "prompt_mode_capabilities", None),
            ):
                chunk_event = json.dumps(
                    {
                        "type": "chunk",
                        "request_id": request_id,
                        "content": chunk,
                    }
                )
                yield f"data: {chunk_event}\n\n"
                accumulated_response += chunk
                chunk_count += 1

                if chunk_count % 50 == 0:
                    yield ": keepalive\n\n"

            # MEMORY ENCODING
            if accumulated_response:
                try:
                    await veena_service.save_episodic_memory(
                        user=user_ref,
                        content=f"User: {request.message}\\nVeena: {accumulated_response[:200]}...",
                        source_type="chat",
                        importance=0.3
                    )
                except Exception as mem_err:
                    logger.error(f"[Veena] Failed to save stream memory: {mem_err}")

            yield stage_event(ReevuStage.ANSWER_SYNTHESIS, "completed")

            # F. Policy Validation Stage (structure-first, evidence pack ready for richer claim checks)
            yield stage_event(ReevuStage.POLICY_VALIDATION, "started")
            validation, evidence_pack = _validate_response_content(
                content=accumulated_response,
                context_docs=context_docs if request.include_context else None,
                function_call_name=function_call.name if function_call else None,
                function_result=function_result,
            )
            policy_validation_stage_payload: dict[str, Any] = {
                "valid": validation.valid,
                "error_count": len(validation.errors),
                "evidence_count": len(evidence_pack.evidence_refs),
                "calculation_count": len(evidence_pack.calculation_ids),
            }
            if not validation.valid:
                policy_validation_stage_payload["safe_failure"] = _build_safe_failure_payload(
                    error_category="insufficient_evidence",
                    searched=["stream_response", "retrieved_context", "response_validation"],
                    missing=["grounded evidence for one or more claims"],
                    next_steps=[
                        "Narrow the query by crop, trial, location, or season.",
                        "Request cited record IDs and verify before decisions.",
                    ],
                )
            yield stage_event(
                ReevuStage.POLICY_VALIDATION,
                "completed",
                **policy_validation_stage_payload,
            )

            yield stage_event(ReevuStage.RESPONSE_EMISSION, "completed")

            # Stage B: Emit evidence envelope as a summary SSE event.
            envelope_dict = _build_reevu_envelope(
                content=accumulated_response,
                evidence_pack=evidence_pack,
                validation=validation,
                context_docs=context_docs if request.include_context else None,
                function_call_name=function_call.name if function_call else None,
            )
            summary_payload: dict[str, Any] = {
                "type": "summary",
                "request_id": request_id,
                "evidence_envelope": envelope_dict,
            }
            if plan_summary:
                summary_payload["plan_execution_summary"] = plan_summary
            comparison = _maybe_format_comparison(
                function_result,
                function_call_name=function_call.name if function_call else None,
            )
            if comparison:
                summary_payload["comparison_result"] = comparison
            summary_event = json.dumps(summary_payload)
            yield f"data: {summary_event}\n\n"

            yield f'data: {json.dumps({"type": "done", "request_id": request_id})}\n\n'
            
            # Record successful streaming request metrics
            total_latency = perf_counter() - start_time
            primary_domain = plan_summary["domains_involved"][0] if plan_summary and plan_summary.get("domains_involved") else "unknown"
            func_name = function_call.name if function_call else ""
            status = "safe_failure" if not validation.valid else "ok"
            policy_flags = list(validation.errors) if validation else []
            routing_state = _get_llm_routing_state(llm_service)

            ReevuMetrics.get().record_request(
                domain=primary_domain,
                function_name=func_name,
                status=status,
                latency_seconds=total_latency,
                stage="total",
                policy_flags=policy_flags,
                provider=actual_provider,
                safe_failure_reason="insufficient_evidence" if not validation.valid else None,
                routing_decisions=_derive_routing_decisions(
                    requested_provider=request.preferred_provider,
                    actual_provider=actual_provider,
                    routing_state=routing_state,
                ),
            )

        except asyncio.CancelledError:
            logger.info("[Veena] Stream cancelled by client")
            # We don't necessarily record cancelled as an error, or we could. Let's record as error.
            total_latency = perf_counter() - start_time
            ReevuMetrics.get().record_request(status="error", latency_seconds=total_latency)
            raise
        except Exception as e:
            logger.error(f"[Veena] Streaming error: {e}")
            total_latency = perf_counter() - start_time
            ReevuMetrics.get().record_request(status="error", latency_seconds=total_latency)
            error_event = json.dumps(
                {
                    "type": "error",
                    "message": str(e),
                    "request_id": request_id,
                    "safe_failure": _build_safe_failure_payload(
                        error_category="streaming_error",
                        searched=["llm_stream", "retrieved_context", "response_pipeline"],
                        missing=["successful stream completion"],
                        next_steps=[
                            "Retry the request in a few seconds.",
                            "If issue persists, narrow the query scope and retry.",
                        ],
                    ),
                }
            )
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked",
        }
    )
