"""
Vector Search API
Semantic search endpoints for Veena AI RAG

Endpoints:
- POST /api/v2/vector/search - Semantic search
- POST /api/v2/vector/index - Index a document
- GET /api/v2/vector/stats - Get vector store stats
- DELETE /api/v2/vector/{doc_id} - Delete a document
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.ai.memory import (
    VectorStoreService,
    BreedingVectorService,
    EmbeddingService,
    SearchRequest,
    SearchResult,
    DocumentCreate,
    DocumentResponse,
)

router = APIRouter(prefix="/vector", tags=["Vector Search"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class VectorSearchRequest(BaseModel):
    """Request for semantic search"""
    query: str = Field(..., description="Natural language search query")
    doc_types: Optional[List[str]] = Field(
        None, 
        description="Filter by document types: germplasm, trial, protocol"
    )
    limit: int = Field(10, ge=1, le=100, description="Max results to return")
    min_similarity: float = Field(0.4, ge=0, le=1, description="Minimum similarity threshold")


class VectorSearchResponse(BaseModel):
    """Response for semantic search"""
    query: str
    results: List[SearchResult]
    total: int


class IndexGermplasmRequest(BaseModel):
    """Request to index germplasm"""
    germplasm_id: str
    name: str
    description: str = ""
    traits: Optional[Dict[str, Any]] = None
    pedigree: Optional[str] = None


class IndexTrialRequest(BaseModel):
    """Request to index trial"""
    trial_id: str
    name: str
    description: str = ""
    objectives: Optional[str] = None
    location: Optional[str] = None


class IndexProtocolRequest(BaseModel):
    """Request to index protocol"""
    protocol_id: str
    name: str
    content: str
    category: Optional[str] = None


class IndexDocumentRequest(BaseModel):
    """Generic document indexing request"""
    doc_type: str = Field(..., description="Document type: germplasm, trial, protocol, custom")
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    source_type: Optional[str] = None


class VectorStatsResponse(BaseModel):
    """Vector store statistics"""
    total_documents: int
    by_type: Dict[str, int]
    embedding_dimension: int
    model: str


class SimilarDocumentsRequest(BaseModel):
    """Request to find similar documents"""
    doc_id: str
    limit: int = Field(10, ge=1, le=50)
    exclude_same_type: bool = False


# ============================================
# DEPENDENCIES
# ============================================

# Singleton embedding service (model loaded once)
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def get_vector_store(
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> VectorStoreService:
    """Get vector store service"""
    return VectorStoreService(db, embedding_service)


async def get_breeding_vector_service(
    vector_store: VectorStoreService = Depends(get_vector_store)
) -> BreedingVectorService:
    """Get breeding-specific vector service"""
    return BreedingVectorService(vector_store)


# ============================================
# ENDPOINTS
# ============================================

@router.post("/search", response_model=VectorSearchResponse)
async def semantic_search(
    request: VectorSearchRequest,
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    Perform semantic search across indexed documents.
    
    Use this for:
    - Finding relevant germplasm by description
    - Searching breeding protocols
    - RAG context retrieval for Veena AI
    """
    search_request = SearchRequest(
        query=request.query,
        doc_types=request.doc_types,
        limit=request.limit,
        min_similarity=request.min_similarity
    )
    
    results = await vector_store.search(search_request)
    
    return VectorSearchResponse(
        query=request.query,
        results=results,
        total=len(results)
    )


@router.post("/index", response_model=DocumentResponse)
async def index_document(
    request: IndexDocumentRequest,
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    Index a document for semantic search.
    
    The document will be embedded and stored in the vector database.
    """
    doc = DocumentCreate(
        doc_type=request.doc_type,
        title=request.title,
        content=request.content,
        metadata=request.metadata,
        source_id=request.source_id,
        source_type=request.source_type
    )
    
    return await vector_store.add_document(doc)


@router.post("/index/germplasm", response_model=DocumentResponse)
async def index_germplasm(
    request: IndexGermplasmRequest,
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service)
):
    """Index a germplasm entry for semantic search"""
    return await breeding_service.index_germplasm(
        germplasm_id=request.germplasm_id,
        name=request.name,
        description=request.description,
        traits=request.traits or {},
        pedigree=request.pedigree
    )


@router.post("/index/trial", response_model=DocumentResponse)
async def index_trial(
    request: IndexTrialRequest,
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service)
):
    """Index a trial for semantic search"""
    return await breeding_service.index_trial(
        trial_id=request.trial_id,
        name=request.name,
        description=request.description,
        objectives=request.objectives,
        location=request.location
    )


@router.post("/index/protocol", response_model=DocumentResponse)
async def index_protocol(
    request: IndexProtocolRequest,
    breeding_service: BreedingVectorService = Depends(get_breeding_vector_service)
):
    """Index a breeding protocol for semantic search"""
    return await breeding_service.index_protocol(
        protocol_id=request.protocol_id,
        name=request.name,
        content=request.content,
        category=request.category
    )


@router.post("/similar", response_model=List[SearchResult])
async def find_similar_documents(
    request: SimilarDocumentsRequest,
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """Find documents similar to a given document"""
    return await vector_store.find_similar(
        doc_id=request.doc_id,
        limit=request.limit,
        exclude_same_type=request.exclude_same_type
    )


@router.get("/stats", response_model=VectorStatsResponse)
async def get_vector_stats(
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """Get vector store statistics"""
    stats = await vector_store.get_stats()
    return VectorStatsResponse(**stats)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """Delete a document from the vector store"""
    deleted = await vector_store.delete_document(doc_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found"
        )
    return {"message": f"Document {doc_id} deleted"}


@router.post("/initialize")
async def initialize_vector_store(
    vector_store: VectorStoreService = Depends(get_vector_store)
):
    """
    Initialize the vector store.
    
    Creates pgvector extension and indexes.
    Run this once after database setup.
    """
    await vector_store.initialize()
    return {"message": "Vector store initialized successfully"}
