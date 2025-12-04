"""
Vector Store API Endpoints
Semantic search and embeddings for Veena AI

USE CASES:
1. "Find germplasm similar to variety X"
2. "Search for drought-tolerant wheat varieties"
3. "What protocols do we have for disease screening?"
4. RAG context retrieval for Veena AI responses
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.vector_store import (
    VectorStoreService,
    BreedingVectorService,
    EmbeddingService,
    DocumentCreate,
    DocumentResponse,
    SearchRequest,
    SearchResult
)

router = APIRouter(prefix="/vector", tags=["Vector Store"])


# ============================================
# DEPENDENCY
# ============================================

async def get_vector_store(db: AsyncSession = Depends(get_db)) -> VectorStoreService:
    """Get vector store service instance"""
    embedding_service = EmbeddingService()
    return VectorStoreService(db, embedding_service)


async def get_breeding_vector_service(
    vector_store: VectorStoreService = Depends(get_vector_store)
) -> BreedingVectorService:
    """Get breeding-specific vector service"""
    return BreedingVectorService(vector_store)


# ============================================
# INITIALIZATION
# ============================================

@router.post("/initialize")
async def initialize_vector_store(
    vector_store: VectorStoreService = Depends(get_vector_store),
    current_user = Depends(get_current_user)
):
    """
    Initialize the vector store (pgvector extension and indexes).
    Run this once after database setup.
    """
    await vector_store.initialize()
    return {"status": "initialized", "message": "Vector store ready"}


# ============================================
# DOCUMENT MANAGEMENT
# ============================================

@router.post("/documents", response_model=DocumentResponse)
async def add_document(
    doc: DocumentCreate,
    vector_store: VectorStoreService = Depends(get_vector_store),
    current_user = Depends(get_current_user)
):
    """
    Add a document to the vector store.
    The document will be embedded and indexed for semantic search.
    """
    return await vector_store.add_document(doc)


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store),
    current_user = Depends(get_current_user)
):
    """Delete a document from the vector store"""
    deleted = await vector_store.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "doc_id": doc_id}


# ============================================
# SEARCH
# ============================================

@router.post("/search", response_model=List[SearchResult])
async def semantic_search(
    request: SearchRequest,
    vector_store: VectorStoreService = Depends(get_vector_store),
    current_user = Depends(get_current_user)
):
    """
    Semantic search across all indexed documents.
    
    Returns documents most similar to the query based on meaning,
    not just keyword matching.
    
    Example queries:
    - "drought tolerant wheat varieties"
    - "high yielding rice with disease resistance"
    - "protocols for marker-assisted selection"
    """
    return await vector_store.search(request)


@router.get("/search/simple", response_model=List[SearchResult])
async def simple_search(
    q: str = Query(..., description="Search query"),
    types: Optional[str] = Query(None, description="Comma-separated doc types"),
    limit: int = Query(10, ge=1, le=100),
    vector_store: VectorStoreService = Depends(get_vector_store),
    current_user = Depends(get_current_user)
):
    """
    Simple semantic search endpoint.
    
    Example: /api/v2/vector/search/simple?q=drought%20tolerant&types=germplasm
    """
    doc_types = types.split(",") if types else None
    
    return await vector_store.search(SearchRequest(
        query=q,
        doc_types=doc_types,
        limit=limit,
        min_similarity=0.4
    ))


@router.get("/similar/{doc_id}", response_model=List[SearchResult])
async def find_similar_documents(
    doc_id: str,
    limit: int = Query(10, ge=1, le=100),
    exclude_same_type: bool = Query(False),
    vector_store: VectorStoreService = Depends(get_vector_store),
    current_user = Depends(get_current_user)
):
    """
    Find documents similar to a given document.
    
    Useful for:
    - "Show me germplasm similar to this one"
    - "Find related trials"
    """
    return await vector_store.find_similar(doc_id, limit, exclude_same_type)


# ============================================
# BREEDING-SPECIFIC ENDPOINTS
# ============================================

@router.post("/index/germplasm")
async def index_germplasm(
    germplasm_id: str,
    name: str,
    description: str = "",
    traits: Optional[dict] = None,
    pedigree: Optional[str] = None,
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service),
    current_user = Depends(get_current_user)
):
    """
    Index a germplasm entry for semantic search.
    
    This enables queries like:
    - "Find drought tolerant varieties"
    - "Show me germplasm with high protein content"
    """
    return await breeding_service.index_germplasm(
        germplasm_id=germplasm_id,
        name=name,
        description=description,
        traits=traits or {},
        pedigree=pedigree
    )


@router.post("/index/trial")
async def index_trial(
    trial_id: str,
    name: str,
    description: str = "",
    objectives: Optional[str] = None,
    location: Optional[str] = None,
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service),
    current_user = Depends(get_current_user)
):
    """
    Index a trial for semantic search.
    
    This enables queries like:
    - "Find trials testing disease resistance"
    - "Show me yield trials in northern region"
    """
    return await breeding_service.index_trial(
        trial_id=trial_id,
        name=name,
        description=description,
        objectives=objectives,
        location=location
    )


@router.post("/index/protocol")
async def index_protocol(
    protocol_id: str,
    name: str,
    content: str,
    category: Optional[str] = None,
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service),
    current_user = Depends(get_current_user)
):
    """
    Index a breeding protocol or SOP.
    
    This enables queries like:
    - "How do we do marker-assisted selection?"
    - "What's the protocol for disease screening?"
    """
    return await breeding_service.index_protocol(
        protocol_id=protocol_id,
        name=name,
        content=content,
        category=category
    )


@router.get("/breeding/search", response_model=List[SearchResult])
async def search_breeding_knowledge(
    q: str = Query(..., description="Search query"),
    include_germplasm: bool = Query(True),
    include_trials: bool = Query(True),
    include_protocols: bool = Query(True),
    limit: int = Query(10, ge=1, le=50),
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service),
    current_user = Depends(get_current_user)
):
    """
    Search across all breeding knowledge.
    
    This is the main endpoint for Veena AI to retrieve context
    for answering breeding-related questions (RAG).
    
    Example queries:
    - "drought tolerant wheat varieties with good yield"
    - "disease resistance screening protocols"
    - "trials in Punjab region"
    """
    return await breeding_service.search_breeding_knowledge(
        query=q,
        include_germplasm=include_germplasm,
        include_trials=include_trials,
        include_protocols=include_protocols,
        limit=limit
    )


@router.get("/germplasm/{germplasm_id}/similar", response_model=List[SearchResult])
async def find_similar_germplasm(
    germplasm_id: str,
    limit: int = Query(10, ge=1, le=50),
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service),
    current_user = Depends(get_current_user)
):
    """
    Find germplasm similar to a given entry.
    
    Useful for:
    - Finding alternative varieties
    - Identifying potential crossing parents
    - Discovering related genetic material
    """
    return await breeding_service.find_similar_germplasm(germplasm_id, limit)


# ============================================
# STATISTICS
# ============================================

@router.get("/stats")
async def get_vector_store_stats(
    vector_store: VectorStoreService = Depends(get_vector_store),
    current_user = Depends(get_current_user)
):
    """
    Get vector store statistics.
    
    Returns:
    - Total documents indexed
    - Documents by type
    - Embedding model info
    """
    return await vector_store.get_stats()


# ============================================
# VEENA AI INTEGRATION
# ============================================

@router.post("/veena/context")
async def get_veena_context(
    query: str,
    max_results: int = Query(5, ge=1, le=20),
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service),
    current_user = Depends(get_current_user)
):
    """
    Get relevant context for Veena AI to answer a question.
    
    This endpoint is called by Veena before generating a response
    to retrieve relevant breeding knowledge (RAG pattern).
    
    Returns formatted context that can be injected into the AI prompt.
    """
    results = await breeding_service.search_breeding_knowledge(
        query=query,
        limit=max_results
    )
    
    # Format context for AI
    context_parts = []
    for i, result in enumerate(results, 1):
        context_parts.append(f"""
[Source {i}: {result.doc_type.upper()}]
Title: {result.title or 'N/A'}
Content: {result.content[:500]}...
Relevance: {result.similarity:.2%}
""")
    
    return {
        "query": query,
        "context": "\n".join(context_parts),
        "sources": [
            {
                "doc_id": r.doc_id,
                "doc_type": r.doc_type,
                "title": r.title,
                "similarity": r.similarity
            }
            for r in results
        ],
        "total_sources": len(results)
    }
