"""
Veena AI Chat API
Multi-tier LLM-powered conversational assistant for plant breeding

Supports multiple LLM providers (in priority order):
1. Ollama (local, free, private)
2. Groq (free tier: 30 req/min)
3. Google AI Studio (free tier: 60 req/min)
4. HuggingFace (free tier)
5. OpenAI (paid)
6. Anthropic (paid)
7. Template fallback (always works)

Endpoints:
- POST /api/v2/chat - Send a message to Veena
- POST /api/v2/chat/context - Get relevant context for a query
- GET /api/v2/chat/status - Get LLM provider status
- GET /api/v2/chat/health - Health check
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vector_store import (
    VectorStoreService,
    BreedingVectorService,
    EmbeddingService,
    SearchResult,
)
from app.services.llm_service import (
    get_llm_service,
    MultiTierLLMService,
    LLMProvider,
    ConversationMessage,
)

router = APIRouter(prefix="/chat", tags=["Veena AI"])


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
    context: Optional[List[ContextDocument]] = None
    conversation_id: Optional[str] = None
    suggestions: Optional[List[str]] = None
    cached: bool = False
    latency_ms: Optional[float] = None


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
    breeding_service: BreedingVectorService = Depends(get_breeding_service)
):
    """
    Send a message to Veena AI assistant.
    
    Veena uses RAG (Retrieval-Augmented Generation) combined with
    multi-tier LLM support to provide intelligent, contextual responses.
    
    **Free LLM Options:**
    - Ollama (local): Install from ollama.ai
    - Groq: Get free API key from console.groq.com
    - Google AI: Get free key from aistudio.google.com
    """
    llm_service = get_llm_service()
    context_docs = None
    context_response = None
    context_text = None
    
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
                timestamp=msg.timestamp or datetime.utcnow()
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
    llm_response = await llm_service.chat(
        user_message=request.message,
        conversation_history=history,
        context=context_text
    )
    
    # Generate suggestions
    suggestions = generate_suggestions(request.message, llm_response.content)
    
    return ChatResponse(
        message=llm_response.content,
        provider=llm_response.provider.value,
        model=llm_response.model,
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
