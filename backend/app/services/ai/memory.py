"""
Vector Store Service
Semantic search and embeddings for Veena AI using pgvector

USE CASES FOR BIJMANTRA:
1. Semantic search across germplasm descriptions
2. Find similar varieties based on traits
3. Search breeding literature and protocols
4. RAG (Retrieval-Augmented Generation) for Veena AI
5. Phenotype similarity matching
6. Cross recommendation based on genetic similarity
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, UTC
import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String, DateTime, Integer, Text, Index
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from app.models.base import Base


# ============================================
# CONFIGURATION
# ============================================

# Embedding dimensions (depends on model used)
# OpenAI ada-002: 1536
# sentence-transformers/all-MiniLM-L6-v2: 384
# BAAI/bge-small-en: 384
EMBEDDING_DIMENSION = 384  # Using lightweight model for local inference


class EmbeddingModel(str, Enum):
    """Supported embedding models"""
    MINILM = "all-MiniLM-L6-v2"  # Fast, local, 384 dims
    BGE_SMALL = "BAAI/bge-small-en"  # Better quality, 384 dims
    OPENAI_ADA = "text-embedding-ada-002"  # Best quality, 1536 dims, requires API


# ============================================
# DATABASE MODELS
# ============================================

class VectorDocument(Base):
    """
    Stores documents with their vector embeddings for semantic search.
    Uses pgvector extension for efficient similarity search.
    """
    __tablename__ = "vector_documents"

    id = Column(Integer, primary_key=True, index=True)

    # Document identification
    doc_id = Column(String, unique=True, index=True, nullable=False)
    doc_type = Column(String, index=True, nullable=False)  # germplasm, trial, protocol, etc.

    # Content
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String, index=True)  # For deduplication

    # Metadata
    doc_metadata = Column(Text, nullable=True)  # JSON string (renamed from 'metadata' - reserved)
    source_id = Column(String, index=True, nullable=True)  # Reference to source entity
    source_type = Column(String, index=True, nullable=True)

    # Embedding (stored as array, pgvector handles the rest)
    # Note: The actual vector column is created via raw SQL with pgvector

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Indexes
    __table_args__ = (
        Index('ix_vector_doc_type_source', 'doc_type', 'source_type'),
    )


# ============================================
# SCHEMAS
# ============================================

class DocumentCreate(BaseModel):
    doc_type: str
    title: Optional[str] = None
    content: str
    metadata: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    source_type: Optional[str] = None


class DocumentResponse(BaseModel):
    doc_id: str
    doc_type: str
    title: Optional[str]
    content: str
    metadata: Optional[Dict[str, Any]]
    source_id: Optional[str]
    source_type: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SearchResult(BaseModel):
    doc_id: str
    doc_type: str
    title: Optional[str]
    content: str
    metadata: Optional[Dict[str, Any]]
    similarity: float  # Cosine similarity score (0-1)
    source_id: Optional[str]
    source_type: Optional[str]


class SearchRequest(BaseModel):
    query: str
    doc_types: Optional[List[str]] = None
    limit: int = 10
    min_similarity: float = 0.5


# ============================================
# EMBEDDING SERVICE
# ============================================

class EmbeddingService:
    """
    Generates embeddings using local models or API.
    Uses sentence-transformers for local inference.
    """

    def __init__(self, model_name: str = EmbeddingModel.MINILM.value):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """Lazy load the embedding model"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                print(f"[VectorStore] Loaded embedding model: {self.model_name}")
            except ImportError:
                print("[VectorStore] sentence-transformers not installed, using mock embeddings")
                self._model = "mock"

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        self._load_model()

        if self._model == "mock":
            # Return mock embedding for development
            import random
            random.seed(hash(text) % 2**32)
            return [random.uniform(-1, 1) for _ in range(EMBEDDING_DIMENSION)]

        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        self._load_model()

        if self._model == "mock":
            return [self.embed(text) for text in texts]

        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


# ============================================
# VECTOR STORE SERVICE
# ============================================

class VectorStoreService:
    """
    Main service for vector storage and semantic search.
    Uses pgvector for efficient similarity search.
    """

    def __init__(self, db: AsyncSession, embedding_service: Optional[EmbeddingService] = None):
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()

    async def initialize(self):
        """Initialize pgvector extension and create vector column"""
        # Enable pgvector extension
        await self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Add vector column if not exists
        # Using raw SQL because SQLAlchemy doesn't natively support pgvector
        await self.db.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'vector_documents' AND column_name = 'embedding'
                ) THEN
                    ALTER TABLE vector_documents 
                    ADD COLUMN embedding vector({EMBEDDING_DIMENSION});
                END IF;
            END $$;
        """))

        # Create index for fast similarity search
        await self.db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_vector_documents_embedding 
            ON vector_documents 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))

        await self.db.commit()
        print("[VectorStore] Initialized pgvector extension and indexes")

    def _generate_doc_id(self, content: str, doc_type: str) -> str:
        """Generate unique document ID"""
        hash_input = f"{doc_type}:{content[:500]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _content_hash(self, content: str) -> str:
        """Generate content hash for deduplication"""
        return hashlib.md5(content.encode()).hexdigest()

    async def add_document(self, doc: DocumentCreate) -> DocumentResponse:
        """Add a document with its embedding to the vector store"""

        # Generate embedding
        embedding = self.embedding_service.embed(doc.content)

        # Generate IDs
        doc_id = self._generate_doc_id(doc.content, doc.doc_type)
        content_hash = self._content_hash(doc.content)

        # Check for duplicate
        existing = await self.db.execute(
            select(VectorDocument).where(VectorDocument.content_hash == content_hash)
        )
        if existing.scalar_one_or_none():
            # Return existing document
            result = await self.db.execute(
                select(VectorDocument).where(VectorDocument.content_hash == content_hash)
            )
            existing_doc = result.scalar_one()
            return DocumentResponse(
                doc_id=existing_doc.doc_id,
                doc_type=existing_doc.doc_type,
                title=existing_doc.title,
                content=existing_doc.content,
                metadata=json.loads(existing_doc.doc_metadata) if existing_doc.doc_metadata else None,
                source_id=existing_doc.source_id,
                source_type=existing_doc.source_type,
                created_at=existing_doc.created_at
            )

        # Insert document
        await self.db.execute(text("""
            INSERT INTO vector_documents 
            (doc_id, doc_type, title, content, content_hash, doc_metadata, source_id, source_type, embedding, created_at, updated_at)
            VALUES (:doc_id, :doc_type, :title, :content, :content_hash, :doc_metadata, :source_id, :source_type, :embedding, :created_at, :updated_at)
        """), {
            "doc_id": doc_id,
            "doc_type": doc.doc_type,
            "title": doc.title,
            "content": doc.content,
            "content_hash": content_hash,
            "doc_metadata": json.dumps(doc.metadata) if doc.metadata else None,
            "source_id": doc.source_id,
            "source_type": doc.source_type,
            "embedding": str(embedding),  # pgvector accepts string representation
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC)
        })

        await self.db.commit()

        return DocumentResponse(
            doc_id=doc_id,
            doc_type=doc.doc_type,
            title=doc.title,
            content=doc.content,
            metadata=doc.metadata,
            source_id=doc.source_id,
            source_type=doc.source_type,
            created_at=datetime.now(UTC)
        )

    async def search(self, request: SearchRequest) -> List[SearchResult]:
        """
        Semantic search using cosine similarity.
        Returns documents most similar to the query.
        """

        # Generate query embedding
        query_embedding = self.embedding_service.embed(request.query)

        # Build query with optional type filter
        type_filter = ""
        params = {
            "embedding": str(query_embedding),
            "limit": request.limit,
            "min_similarity": request.min_similarity
        }

        if request.doc_types:
            type_filter = "AND doc_type = ANY(:doc_types)"
            params["doc_types"] = request.doc_types

        # Cosine similarity search
        result = await self.db.execute(text(f"""
            SELECT 
                doc_id, doc_type, title, content, doc_metadata, source_id, source_type,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM vector_documents
            WHERE 1 - (embedding <=> :embedding::vector) >= :min_similarity
            {type_filter}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """), params)

        rows = result.fetchall()

        return [
            SearchResult(
                doc_id=row.doc_id,
                doc_type=row.doc_type,
                title=row.title,
                content=row.content,
                metadata=json.loads(row.doc_metadata) if row.doc_metadata else None,
                similarity=float(row.similarity),
                source_id=row.source_id,
                source_type=row.source_type
            )
            for row in rows
        ]

    async def find_similar(
        self,
        doc_id: str,
        limit: int = 10,
        exclude_same_type: bool = False
    ) -> List[SearchResult]:
        """Find documents similar to a given document"""

        # Get the document's embedding
        result = await self.db.execute(text("""
            SELECT embedding, doc_type FROM vector_documents WHERE doc_id = :doc_id
        """), {"doc_id": doc_id})

        row = result.fetchone()
        if not row:
            return []

        type_filter = ""
        if exclude_same_type:
            type_filter = "AND doc_type != :exclude_type"

        # Find similar documents
        result = await self.db.execute(text(f"""
            SELECT 
                doc_id, doc_type, title, content, doc_metadata, source_id, source_type,
                1 - (embedding <=> (SELECT embedding FROM vector_documents WHERE doc_id = :doc_id)) as similarity
            FROM vector_documents
            WHERE doc_id != :doc_id
            {type_filter}
            ORDER BY embedding <=> (SELECT embedding FROM vector_documents WHERE doc_id = :doc_id)
            LIMIT :limit
        """), {
            "doc_id": doc_id,
            "limit": limit,
            "exclude_type": row.doc_type if exclude_same_type else None
        })

        rows = result.fetchall()

        return [
            SearchResult(
                doc_id=r.doc_id,
                doc_type=r.doc_type,
                title=r.title,
                content=r.content,
                metadata=json.loads(r.doc_metadata) if r.doc_metadata else None,
                similarity=float(r.similarity),
                source_id=r.source_id,
                source_type=r.source_type
            )
            for r in rows
        ]

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the vector store"""
        result = await self.db.execute(text("""
            DELETE FROM vector_documents WHERE doc_id = :doc_id
        """), {"doc_id": doc_id})
        await self.db.commit()
        return result.rowcount > 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        result = await self.db.execute(text("""
            SELECT 
                doc_type,
                COUNT(*) as count
            FROM vector_documents
            GROUP BY doc_type
        """))

        type_counts = {row.doc_type: row.count for row in result.fetchall()}

        total_result = await self.db.execute(text("""
            SELECT COUNT(*) as total FROM vector_documents
        """))
        total = total_result.scalar()

        return {
            "total_documents": total,
            "by_type": type_counts,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "model": self.embedding_service.model_name
        }


# ============================================
# BREEDING-SPECIFIC INDEXING
# ============================================

class BreedingVectorService:
    """
    High-level service for indexing breeding data for Veena AI.
    """

    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store

    async def index_germplasm(
        self,
        germplasm_id: str,
        name: str,
        description: str,
        traits: Dict[str, Any],
        pedigree: Optional[str] = None
    ) -> DocumentResponse:
        """Index a germplasm entry for semantic search"""

        # Combine all text for embedding
        content_parts = [
            f"Germplasm: {name}",
            f"Description: {description}" if description else "",
            f"Pedigree: {pedigree}" if pedigree else "",
        ]

        # Add trait information
        if traits:
            trait_text = ", ".join([f"{k}: {v}" for k, v in traits.items()])
            content_parts.append(f"Traits: {trait_text}")

        content = "\n".join(filter(None, content_parts))

        return await self.vector_store.add_document(DocumentCreate(
            doc_type="germplasm",
            title=name,
            content=content,
            metadata={"traits": traits, "pedigree": pedigree},
            source_id=germplasm_id,
            source_type="germplasm"
        ))

    async def index_trial(
        self,
        trial_id: str,
        name: str,
        description: str,
        objectives: Optional[str] = None,
        location: Optional[str] = None
    ) -> DocumentResponse:
        """Index a trial for semantic search"""

        content_parts = [
            f"Trial: {name}",
            f"Description: {description}" if description else "",
            f"Objectives: {objectives}" if objectives else "",
            f"Location: {location}" if location else "",
        ]

        content = "\n".join(filter(None, content_parts))

        return await self.vector_store.add_document(DocumentCreate(
            doc_type="trial",
            title=name,
            content=content,
            metadata={"objectives": objectives, "location": location},
            source_id=trial_id,
            source_type="trial"
        ))

    async def index_protocol(
        self,
        protocol_id: str,
        name: str,
        content: str,
        category: Optional[str] = None
    ) -> DocumentResponse:
        """Index a breeding protocol or SOP"""

        return await self.vector_store.add_document(DocumentCreate(
            doc_type="protocol",
            title=name,
            content=content,
            metadata={"category": category},
            source_id=protocol_id,
            source_type="protocol"
        ))

    async def search_breeding_knowledge(
        self,
        query: str,
        include_germplasm: bool = True,
        include_trials: bool = True,
        include_protocols: bool = True,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search across all breeding knowledge for Veena AI.
        Used for RAG (Retrieval-Augmented Generation).
        """

        doc_types = []
        if include_germplasm:
            doc_types.append("germplasm")
        if include_trials:
            doc_types.append("trial")
        if include_protocols:
            doc_types.append("protocol")

        return await self.vector_store.search(SearchRequest(
            query=query,
            doc_types=doc_types if doc_types else None,
            limit=limit,
            min_similarity=0.4
        ))

    async def find_similar_germplasm(
        self,
        germplasm_id: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """Find germplasm similar to a given entry"""

        # First, get the document for this germplasm
        result = await self.vector_store.db.execute(text("""
            SELECT doc_id FROM vector_documents 
            WHERE source_id = :source_id AND source_type = 'germplasm'
        """), {"source_id": germplasm_id})

        row = result.fetchone()
        if not row:
            return []

        return await self.vector_store.find_similar(row.doc_id, limit=limit)
