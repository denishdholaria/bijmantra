"""
Veena Cognitive Service

Manages the "Mind" of Veena AI:
- Long-term Memory (Episodic/Semantic)
- Reasoning Traces (Chain of Thought)
- User Context & Preferences

This service connects the Chat API to the Mitsubishi Heavy core schemas.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from app.models.veena_core import (
    VeenaMemory,
    ReasoningTrace,
    UserContext,
    MemoryType,
    ReasoningStage,
    EntityType
)
from app.models.core import User
from app.services.veena_cognitive_service import VeenaCognitiveService

logger = logging.getLogger(__name__)

class VeenaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cognitive = VeenaCognitiveService(db)

    async def get_or_create_user_context(self, user: User) -> UserContext:
        """Fetch user context or create a default one if missing."""
        stmt = select(UserContext).where(UserContext.user_id == user.id)
        result = await self.db.execute(stmt)
        context = result.scalar_one_or_none()

        if not context:
            logger.info(f"Creating new cognitive context for user {user.id}")
            context = UserContext(
                user_id=user.id,
                organization_id=user.organization_id,
                preferred_language="en",
                response_verbosity="balanced",
                communication_style="professional", # Default
                total_interactions=0,
                preferences={"auto_summarize": True}
            )
            self.db.add(context)
            await self.db.flush() # Get ID but don't commit yet

        return context

    async def update_interaction_stats(self, user_id: int):
        """Increment interaction count and update last seen timestamp."""
        stmt = (
            update(UserContext)
            .where(UserContext.user_id == user_id)
            .values(
                total_interactions=UserContext.total_interactions + 1,
                last_interaction=datetime.now()
            )
        )
        await self.db.execute(stmt)

    async def save_episodic_memory(
        self,
        user: User,
        content: str,
        source_type: str = "chat",
        source_id: Optional[str] = None,
        importance: float = 0.5,
        summary: Optional[str] = None
    ) -> VeenaMemory:
        """Store a user interaction or fact as Episodic memory."""
        memory = VeenaMemory(
            organization_id=user.organization_id,
            user_id=user.id,
            memory_type=MemoryType.EPISODIC,
            content=content,
            source_type=source_type,
            source_id=source_id,
            importance_score=importance,
            summary=summary,
            last_accessed=datetime.now()
        )
        self.db.add(memory)
        return memory

    async def log_reasoning_trace(
        self,
        user: User,
        session_id: UUID,
        stage: ReasoningStage,
        content: str,
        confidence: float = 0.8,
        parent_id: Optional[int] = None,
        sequence: int = 0
    ) -> ReasoningTrace:
        """Log a step in the AI's chain of thought."""
        trace = ReasoningTrace(
            organization_id=user.organization_id,
            user_id=user.id,
            session_id=session_id,
            stage=stage,
            content=content,
            confidence=confidence,
            parent_id=parent_id,
            sequence_order=sequence
        )
        self.db.add(trace)
        return trace

    async def store_memory(self, user_id: int, interaction_data: Dict[str, Any]):
        """Delegates to dedicated cognitive memory service."""
        return await self.cognitive.store_memory(user_id, interaction_data)

    async def retrieve_relevant_context(self, user_id: int, current_query: str, limit: int = 5):
        """Delegates vector-style retrieval to dedicated cognitive service."""
        return await self.cognitive.retrieve_relevant_context(user_id, current_query, limit=limit)

    async def get_recent_memories(
        self,
        user_id: int,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[VeenaMemory]:
        """Retrieve recent relevant memories for context."""
        stmt = (
            select(VeenaMemory)
            .where(
                VeenaMemory.user_id == user_id,
                VeenaMemory.importance_score >= min_importance
            )
            .order_by(desc(VeenaMemory.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

from fastapi import Depends
from app.api.deps import get_db

# Helper for Dependency Injection
async def get_veena_service(db: AsyncSession = Depends(get_db)) -> VeenaService:
    return VeenaService(db)
