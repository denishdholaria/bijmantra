"""
Veena Cognitive Core Models

SQLAlchemy models for Veena AI long-term memory, reasoning traces,
and user context storage.

Author: Principal Architect (Claude Opus 4.5)
Date: 2026-02-02
See: .agent/MitsubitshiHeavy.md - Task 2

Design Decisions:
- Uses Mapped[...] typing (SQLAlchemy 2.0 strict pattern)
- Polymorphic entity_type/entity_id for cross-domain linking
- RLS-ready with organization_id on all tables
- pgvector-ready embedding field for RAG queries
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, 
    DateTime, Enum, Boolean, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel


# =============================================================================
# Enums
# =============================================================================

class MemoryType(str, enum.Enum):
    """Type of memory storage."""
    EPISODIC = "EPISODIC"       # Specific events/interactions
    SEMANTIC = "SEMANTIC"        # General knowledge/facts
    PROCEDURAL = "PROCEDURAL"   # How to do things


class EntityType(str, enum.Enum):
    """Polymorphic entity types for cross-domain linking."""
    EXPERIMENT = "EXPERIMENT"
    FIELD = "FIELD"
    TRIAL = "TRIAL"
    GERMPLASM = "GERMPLASM"
    CROSS = "CROSS"
    OBSERVATION = "OBSERVATION"
    USER = "USER"
    GENERAL = "GENERAL"


class ReasoningStage(str, enum.Enum):
    """Stage in the reasoning process."""
    CONCEPT = "CONCEPT"          # Initial concept/observation
    HYPOTHESIS = "HYPOTHESIS"    # Formed hypothesis
    DEDUCTION = "DEDUCTION"      # Logical deduction step
    CONCLUSION = "CONCLUSION"    # Final conclusion


# =============================================================================
# Veena Memory Model
# =============================================================================

class VeenaMemory(BaseModel):
    """
    Episodic and Semantic memory storage for Veena AI.
    
    Supports RAG (Retrieval Augmented Generation) via pgvector embeddings.
    Links to any domain entity via polymorphic identity pattern.
    
    Memory Lifecycle:
        User Query → Veena processes → Stores insight as EPISODIC
        Multiple insights → Consolidated into SEMANTIC knowledge
    """
    __tablename__ = "veena_memories"
    __table_args__ = (
        Index('idx_veena_memories_org_user', 'organization_id', 'user_id'),
        Index('idx_veena_memories_entity', 'entity_type', 'entity_id'),
        Index('idx_veena_memories_type', 'memory_type'),
        {'extend_existing': True}
    )
    
    # Multi-tenancy
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    # Memory content
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType), nullable=False, default=MemoryType.EPISODIC
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Embedding for vector similarity search (pgvector)
    # Note: Actual VECTOR type requires pgvector extension
    # Using ARRAY(Float) as fallback, switch to Vector(1536) with pgvector
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )
    
    # Source reference
    source_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'chat', 'experiment', 'document', etc.
    source_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Reference ID
    
    # Polymorphic entity link (cross-domain)
    entity_type: Mapped[Optional[EntityType]] = mapped_column(
        Enum(EntityType), nullable=True
    )
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # User association
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    
    # Metadata
    importance_score: Mapped[float] = mapped_column(
        Integer, nullable=False, default=0.5
    )  # 0.0-1.0, higher = more important
    access_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # Times retrieved
    last_accessed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # For temporary memories
    
    # Additional structured data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


# =============================================================================
# Reasoning Trace Model
# =============================================================================

class ReasoningTrace(BaseModel):
    """
    Stores structured reasoning chains: Concept → Deduction → Conclusion.
    
    Enables transparency in AI decision-making and supports
    explanation generation for scientific recommendations.
    
    Reasoning Chain Example:
        Concept: "Variety X shows 15% higher yield under stress"
        Hypothesis: "X may have drought tolerance genes"
        Deduction: "Cross X with Y to combine traits"
        Conclusion: "Recommend crossing block X-Y for drought program"
    """
    __tablename__ = "veena_reasoning_traces"
    __table_args__ = (
        Index('idx_reasoning_traces_org', 'organization_id'),
        Index('idx_reasoning_traces_session', 'session_id'),
        Index('idx_reasoning_traces_parent', 'parent_id'),
        {'extend_existing': True}
    )
    
    # Multi-tenancy
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    # Session grouping (conversation/analysis session)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    
    # Reasoning chain
    stage: Mapped[ReasoningStage] = mapped_column(
        Enum(ReasoningStage), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(
        Integer, nullable=False, default=0.5
    )  # 0.0-1.0
    
    # Chain linking (parent → child reasoning steps)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("veena_reasoning_traces.id"), nullable=True
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    
    # Evidence/sources
    evidence_sources: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # List of source references
    
    # Polymorphic entity link
    entity_type: Mapped[Optional[EntityType]] = mapped_column(
        Enum(EntityType), nullable=True
    )
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # User who triggered this reasoning
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    
    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Self-referential relationship for reasoning chains
    parent = relationship(
        "ReasoningTrace",
        remote_side="ReasoningTrace.id",
        backref="children"
    )


# =============================================================================
# User Context Model
# =============================================================================

class UserContext(BaseModel):
    """
    Long-term user preferences and context for personalized AI interactions.
    
    Stores:
    - Preferred communication style
    - Domain expertise areas
    - Frequently accessed entities
    - Custom instructions
    """
    __tablename__ = "veena_user_contexts"
    __table_args__ = (
        Index('idx_user_contexts_org_user', 'organization_id', 'user_id'),
        {'extend_existing': True}
    )
    
    # Multi-tenancy
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True
    )
    
    # User association (one context per user per org)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    
    # Communication preferences
    preferred_language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en"
    )
    communication_style: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'formal', 'casual', 'technical', 'simplified'
    response_verbosity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="balanced"
    )  # 'concise', 'balanced', 'detailed'
    
    # Domain expertise
    expertise_areas: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # ['genomics', 'phenotyping', 'breeding']
    focus_programs: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # Program IDs user works with most
    
    # Custom instructions
    custom_instructions: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Free-form user instructions to AI
    
    # Interaction history summary
    total_interactions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_interaction: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    frequently_asked_topics: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    
    # Feature flags/preferences
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Example: {"auto_summarize": true, "show_confidence": true}
    
    # Relationship
    user = relationship("User", backref="veena_context")
