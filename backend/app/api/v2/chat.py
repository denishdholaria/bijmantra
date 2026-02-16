"""
Veena AI Chat API
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
- POST /api/v2/chat - Send a message to Veena (with function calling!)
- POST /api/v2/chat/stream - Stream a message to Veena (SSE)
- POST /api/v2/chat/context - Get relevant context for a query
- GET /api/v2/chat/status - Get LLM provider status
- GET /api/v2/chat/health - Health check
"""

import json
import logging
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.services.ai.memory import (
    VectorStoreService,
    BreedingVectorService,
    DocumentCreate,
    SearchRequest,
    EmbeddingService,
    SearchResult
)
from app.services.ai.engine import (
    get_llm_service,
    LLMProvider,
    LLMResponse,
    ConversationMessage,
)
from app.services.function_calling_service import FunctionCallingService
from app.services.ai.tools import FunctionExecutor
import os
from app.api.deps import get_current_user
from app.models.core import User
from app.services.ai.quota import AIQuotaService
from app.services.veena_service import VeenaService, get_veena_service

router = APIRouter(prefix="/chat", tags=["Veena AI"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class ChatMessage(BaseModel):
    """A single chat message"""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request to chat with Veena"""
    message: str = Field(..., description="User's message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    conversation_history: Optional[List[ChatMessage]] = Field(None, description="Previous messages")
    include_context: bool = Field(True, description="Whether to retrieve RAG context")
    context_limit: int = Field(5, ge=1, le=20, description="Max context documents")
    preferred_provider: Optional[str] = Field(None, description="Force specific LLM provider")
    # BYOK (Bring Your Own Key) - allows users to use their own API keys
    user_api_key: Optional[str] = Field(None, description="User's API key for the provider (BYOK)")
    user_model: Optional[str] = Field(None, description="User's preferred model name")


class ContextDocument(BaseModel):
    """A document retrieved for context"""
    doc_id: str
    doc_type: str
    title: Optional[str]
    content: str
    similarity: float
    source_id: Optional[str]


class ChatResponse(BaseModel):
    """Response from Veena"""
    message: str
    provider: str
    model: str
    model_confirmed: bool = Field(False, description="True if model name came from API response, False if from config")
    context: Optional[List[ContextDocument]] = None
    conversation_id: Optional[str] = None
    suggestions: Optional[List[str]] = None
    cached: bool = False
    latency_ms: Optional[float] = None
    function_call: Optional[Dict[str, Any]] = Field(None, description="Function that was executed")
    function_result: Optional[Dict[str, Any]] = Field(None, description="Result of function execution")


class ContextRequest(BaseModel):
    """Request to get context for a query"""
    query: str
    doc_types: Optional[List[str]] = None
    limit: int = Field(5, ge=1, le=20)


class ContextResponse(BaseModel):
    """Context retrieval response"""
    query: str
    documents: List[ContextDocument]
    total: int


# ============================================
# DEPENDENCIES
# ============================================

_embedding_service: Optional[EmbeddingService] = None


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


async def get_breeding_service(
    vector_store: VectorStoreService = Depends(get_vector_store)
) -> BreedingVectorService:
    return BreedingVectorService(vector_store)


# ============================================
# HELPER FUNCTIONS
# ============================================

def format_context_for_llm(documents: List[SearchResult]) -> str:
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


def generate_suggestions(message: str, response: str) -> List[str]:
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
    Veena uses RAG (Retrieval-Augmented Generation) combined with
    multi-tier LLM support to provide intelligent, contextual responses.
    
    **NEW: Function Calling with FunctionGemma**
    Veena can now execute actions like searching germplasm, creating trials,
    comparing varieties, and more!
    
    **Free LLM Options:**
    - Ollama (local): Install from ollama.ai
    - Groq: Get free API key from console.groq.com
    - Google AI: Get free key from aistudio.google.com
    - FunctionGemma: Use HuggingFace API key
    """
    llm_service = get_llm_service()
    context_docs = None
    context_response = None
    context_text = None
    function_call_result = None
    function_call_data = None

    # Step 1: Check if this is a function call request
    function_calling_service = FunctionCallingService(
        api_key=os.getenv("HUGGINGFACE_API_KEY") or os.getenv("FUNCTIONGEMMA_API_KEY")
    )

    # ENFORCE QUOTA (Hybrid Tiered Model)
    # If user provides their own key (BYOK), skip quota.
    # Otherwise, check organization daily limit.
    if not request.user_api_key:
        await AIQuotaService.check_and_increment_usage(
            db,
            organization_id=current_user.organization_id,
            increment=True
        )

    # COGNITIVE LOAD: Fetch User Context
    await veena_service.get_or_create_user_context(current_user)
    await veena_service.update_interaction_stats(current_user.id)

    try:
        function_call = await function_calling_service.detect_function_call(
            user_message=request.message,
            conversation_history=[msg.dict() for msg in (request.conversation_history or [])]
        )

        if function_call:
            logger.info(f"[Veena] Function call detected: {function_call.name}")

            # Step 2: Execute the function
            function_executor = FunctionExecutor(db)
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
If the result is empty, clearly state that no matching records were found in the database."""

                llm_response = await llm_service.chat(
                    user_message=format_prompt,
                    conversation_history=None,
                    context=None
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
                    function_result=function_call_result
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

    # Convert conversation history
    history = None
    if request.conversation_history:
        history = [
            ConversationMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp or datetime.now(timezone.utc)
            )
            for msg in request.conversation_history
        ]

    # Parse preferred provider
    preferred = None
    if request.preferred_provider:
        try:
            preferred = LLMProvider(request.preferred_provider.lower())
        except ValueError:
            pass

    # Generate response using LLM
    # If user provided their own API key (BYOK), use it
    llm_response = await llm_service.chat(
        user_message=request.message,
        conversation_history=history,
        context=context_text,
        preferred_provider=preferred,
        user_api_key=request.user_api_key,
        user_model=request.user_model
    )

    suggestions = generate_suggestions(request.message, llm_response.content)

    # MEMORY ENCODING: Save conversation snippet
    # Only save if meaningful (not empty)
    if llm_service and llm_response.content:
        await veena_service.save_episodic_memory(
            user=current_user,
            content=f"User: {request.message}\nVeena: {llm_response.content[:200]}...",
            source_type="chat",
            importance=0.3
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
        latency_ms=llm_response.latency_ms
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
async def get_llm_status():
    """
    Get status of all LLM providers.
    
    Shows which providers are configured and available.
    """
    llm_service = get_llm_service()
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
async def veena_health():
    """Check Veena AI health status"""
    llm_service = get_llm_service()
    status = await llm_service.get_status()

    return {
        "status": "healthy",
        "assistant": "Veena",
        "active_provider": status["active_provider"],
        "active_model": status["active_model"],
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


@router.post("/stream")
async def stream_chat_with_veena(
    request: ChatRequest,
    breeding_service: BreedingVectorService = Depends(get_breeding_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    veena_service: VeenaService = Depends(get_veena_service)
):
    """
    Stream a message to Veena AI assistant using Server-Sent Events (SSE).
    
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

    llm_service = get_llm_service()
    context_text = None

    # 1. Retrieve relevant context if enabled
    if request.include_context:
        try:
            context_docs = await breeding_service.search_breeding_knowledge(
                query=request.message,
                limit=request.context_limit
            )

            if context_docs:
                context_text = format_context_for_llm(context_docs)
        except Exception as e:
            logger.warning(f"[Veena] Context retrieval error for streaming: {e}")

    # 2. Convert conversation history
    history = None
    if request.conversation_history:
        history = [
            ConversationMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp or datetime.now(timezone.utc)
            )
            for msg in request.conversation_history
        ]

    # 3. Parse preferred provider
    preferred = None
    if request.preferred_provider:
        try:
            preferred = LLMProvider(request.preferred_provider.lower())
        except ValueError:
            pass

    # ENFORCE QUOTA FOR STREAMING
    if not request.user_api_key:
        # We increment at start of stream. If stream fails, we still count it (simpler)
        # Or we could increment at end, but start protects against DOS.
        await AIQuotaService.check_and_increment_usage(
            db,
            organization_id=current_user.organization_id,
            increment=True
        )

    # COGNITIVE LOAD
    await veena_service.get_or_create_user_context(current_user)
    await veena_service.update_interaction_stats(current_user.id)

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream with proper error handling and keepalive"""
        try:
            # A. Detect Function Call
            function_calling_service = FunctionCallingService(
                api_key=os.getenv("HUGGINGFACE_API_KEY") or os.getenv("FUNCTIONGEMMA_API_KEY")
            )

            function_call = None
            function_result = None
            prompt_override = None
            accumulated_response = ""

            try:
                # Detect function call (async)
                function_call = await function_calling_service.detect_function_call(
                    user_message=request.message,
                    conversation_history=[msg.dict() for msg in (request.conversation_history or [])]
                )
            except Exception as e:
                logger.warning(f"[Veena] Function detection failed: {e}")

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
                     yield 'data: {"type": "chunk", "content": "I\'m running in template mode without an AI backend. "}\n\n'
                     yield 'data: {"type": "chunk", "content": "Please configure an AI provider for full features."}\n\n'
                     yield 'data: {"type": "done"}\n\n'
                     return

            # D. Execute Function (if detected)
            if function_call:
                logger.info(f"[Veena] Executing function in stream: {function_call.name}")

                # Notify client about function execution (optional, maybe just show thinking?)
                # yield f'data: {json.dumps({"type": "chunk", "content": "🔄 processing request..."})}\n\n'

                function_executor = FunctionExecutor(db)
                try:
                    function_result = await function_executor.execute(
                        function_call.name,
                        function_call.parameters
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

                except Exception as e:
                    logger.error(f"[Veena] Function execution error: {e}")
                    error_event = json.dumps({"type": "chunk", "content": f"\n\n[Error executing action: {str(e)}]"})
                    yield f"data: {error_event}\n\n"

            # E. Stream Response (Regular or Function Explanation)
            message_to_send = prompt_override if prompt_override else request.message

            chunk_count = 0
            async for chunk in llm_service.stream_chat(
                user_message=message_to_send,
                conversation_history=history if not prompt_override else None, # Clean history if explaining function? Or keep it? keeping it is better for context.
                context=context_text, # Still include RAG context? Yes.
                preferred_provider=preferred,
                user_api_key=request.user_api_key,
                user_model=request.user_model
            ):
                chunk_event = json.dumps({"type": "chunk", "content": chunk})
                yield f"data: {chunk_event}\n\n"
                accumulated_response += chunk
                chunk_count += 1

                if chunk_count % 50 == 0:
                    yield ": keepalive\n\n"

            # MEMORY ENCODING
            if accumulated_response:
                try:
                    await veena_service.save_episodic_memory(
                        user=current_user,
                        content=f"User: {request.message}\\nVeena: {accumulated_response[:200]}...",
                        source_type="chat",
                        importance=0.3
                    )
                except Exception as mem_err:
                    logger.error(f"[Veena] Failed to save stream memory: {mem_err}")

            yield 'data: {"type": "done"}\n\n'

        except asyncio.CancelledError:
            logger.info("[Veena] Stream cancelled by client")
            raise
        except Exception as e:
            logger.error(f"[Veena] Streaming error: {e}")
            error_event = json.dumps({"type": "error", "message": str(e)})
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
