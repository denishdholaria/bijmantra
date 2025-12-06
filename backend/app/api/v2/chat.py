"""
Veena AI Chat API
RAG-powered conversational assistant for plant breeding

Endpoints:
- POST /api/v2/chat - Send a message to Veena
- POST /api/v2/chat/context - Get relevant context for a query
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
    include_context: bool = Field(True, description="Whether to retrieve RAG context")
    context_limit: int = Field(5, ge=1, le=20, description="Max context documents")


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
    context: Optional[List[ContextDocument]] = None
    conversation_id: Optional[str] = None
    suggestions: Optional[List[str]] = None


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
# VEENA RESPONSE GENERATION
# ============================================

class VeenaAssistant:
    """
    Veena AI Assistant for plant breeding.
    
    Currently uses template-based responses with RAG context.
    Can be extended to use LLM APIs (OpenAI, Anthropic, local models).
    """
    
    GREETING_PATTERNS = [
        "hello", "hi", "hey", "namaste", "good morning", 
        "good afternoon", "good evening"
    ]
    
    HELP_PATTERNS = [
        "help", "what can you do", "capabilities", "features"
    ]
    
    def __init__(self):
        self.name = "Veena"
    
    def _is_greeting(self, message: str) -> bool:
        message_lower = message.lower().strip()
        return any(pattern in message_lower for pattern in self.GREETING_PATTERNS)
    
    def _is_help_request(self, message: str) -> bool:
        message_lower = message.lower().strip()
        return any(pattern in message_lower for pattern in self.HELP_PATTERNS)
    
    def _format_context(self, documents: List[SearchResult]) -> str:
        """Format retrieved documents as context"""
        if not documents:
            return ""
        
        context_parts = ["Based on the knowledge base:\n"]
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"{i}. [{doc.doc_type}] {doc.title or 'Untitled'}")
            # Truncate content for context
            content_preview = doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
            context_parts.append(f"   {content_preview}\n")
        
        return "\n".join(context_parts)
    
    def generate_response(
        self, 
        message: str, 
        context_docs: Optional[List[SearchResult]] = None
    ) -> tuple[str, List[str]]:
        """
        Generate a response to the user's message.
        
        Returns: (response_text, suggestions)
        """
        # Handle greetings
        if self._is_greeting(message):
            return (
                f"Namaste! 🙏 I'm {self.name}, your plant breeding assistant. "
                "I can help you with:\n"
                "• Finding germplasm by traits or characteristics\n"
                "• Searching breeding protocols and SOPs\n"
                "• Answering questions about trials and studies\n"
                "• Recommending crosses based on genetic similarity\n\n"
                "What would you like to know?",
                [
                    "Show me drought-tolerant varieties",
                    "What protocols do we have for DNA extraction?",
                    "Find germplasm similar to IR64"
                ]
            )
        
        # Handle help requests
        if self._is_help_request(message):
            return (
                f"I'm {self.name}, your AI assistant for plant breeding. Here's what I can do:\n\n"
                "🌾 **Germplasm Search**\n"
                "Ask me about varieties, traits, or characteristics.\n"
                "Example: 'Find rice varieties with high yield and disease resistance'\n\n"
                "📋 **Protocol Lookup**\n"
                "Search breeding protocols and standard procedures.\n"
                "Example: 'How do I perform marker-assisted selection?'\n\n"
                "🔬 **Trial Information**\n"
                "Get details about ongoing or past trials.\n"
                "Example: 'What trials are running in Hyderabad?'\n\n"
                "🧬 **Similarity Search**\n"
                "Find genetically or phenotypically similar entries.\n"
                "Example: 'Find varieties similar to Swarna'\n\n"
                "Just ask your question naturally!",
                [
                    "Search for high-yielding wheat varieties",
                    "Show me crossing protocols",
                    "What germplasm do we have from IRRI?"
                ]
            )
        
        # Generate response based on context
        if context_docs and len(context_docs) > 0:
            # We have relevant context
            top_doc = context_docs[0]
            
            if top_doc.similarity > 0.7:
                # High confidence match
                response = f"I found relevant information:\n\n"
                response += f"**{top_doc.title or top_doc.doc_type.title()}**\n"
                response += f"{top_doc.content[:500]}"
                if len(top_doc.content) > 500:
                    response += "...\n\n"
                else:
                    response += "\n\n"
                
                if len(context_docs) > 1:
                    response += f"I also found {len(context_docs) - 1} related entries. "
                    response += "Would you like me to show more details?"
                
                suggestions = [
                    f"Tell me more about {top_doc.title}" if top_doc.title else "Show more details",
                    "Find similar entries",
                    "Search for something else"
                ]
            else:
                # Lower confidence - provide what we found but note uncertainty
                response = "Here's what I found that might be relevant:\n\n"
                for doc in context_docs[:3]:
                    response += f"• **{doc.title or doc.doc_type}** (similarity: {doc.similarity:.0%})\n"
                    response += f"  {doc.content[:150]}...\n\n"
                
                response += "Would you like me to search with different terms?"
                suggestions = [
                    "Refine my search",
                    "Show all results",
                    "Search in a different category"
                ]
        else:
            # No context found
            response = (
                "I couldn't find specific information about that in the knowledge base. "
                "This could mean:\n"
                "• The data hasn't been indexed yet\n"
                "• Try rephrasing your question\n"
                "• The information might be under a different category\n\n"
                "Would you like me to help you search differently?"
            )
            suggestions = [
                "Show me all germplasm",
                "List available protocols",
                "What data is indexed?"
            ]
        
        return response, suggestions


# Singleton assistant
_veena = VeenaAssistant()


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
    
    Veena uses RAG (Retrieval-Augmented Generation) to provide
    contextually relevant responses based on your breeding data.
    """
    context_docs = None
    context_response = None
    
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
                        content=doc.content[:500],  # Truncate for response
                        similarity=doc.similarity,
                        source_id=doc.source_id
                    )
                    for doc in context_docs
                ]
        except Exception as e:
            print(f"[Veena] Context retrieval error: {e}")
            # Continue without context
    
    # Generate response
    response_text, suggestions = _veena.generate_response(
        request.message, 
        context_docs
    )
    
    return ChatResponse(
        message=response_text,
        context=context_response,
        conversation_id=request.conversation_id,
        suggestions=suggestions
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


@router.get("/health")
async def veena_health():
    """Check Veena AI health status"""
    return {
        "status": "healthy",
        "assistant": "Veena",
        "capabilities": [
            "semantic_search",
            "germplasm_lookup",
            "protocol_search",
            "trial_information",
            "similarity_matching"
        ],
        "rag_enabled": True
    }
