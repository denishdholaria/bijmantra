"""
Conversation service for REEVU chat.

Handles conversation history management, message formatting, and memory encoding.
Extracted from backend/app/api/v2/chat.py.
"""

import logging
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.modules.ai.services.engine import ConversationMessage
from app.modules.ai.services.reevu_service import ReevuService

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation history and memory."""

    def __init__(self, reevu_service: ReevuService):
        self.reevu_service = reevu_service

    def convert_history_to_messages(
        self, conversation_history: list[dict[str, Any]] | None
    ) -> list[ConversationMessage] | None:
        """Convert API conversation history to internal ConversationMessage format."""
        if not conversation_history:
            return None

        return [
            ConversationMessage(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                timestamp=msg.get("timestamp") or datetime.now(UTC),
            )
            for msg in conversation_history
        ]

    async def save_conversation_memory(
        self,
        user_ref: SimpleNamespace,
        user_message: str,
        assistant_response: str,
        max_length: int = 200,
    ) -> None:
        """Save conversation snippet to episodic memory."""
        if not assistant_response:
            return

        try:
            content = f"User: {user_message}\nREEVU: {assistant_response[:max_length]}..."
            await self.reevu_service.save_episodic_memory(
                user=user_ref,
                content=content,
                source_type="chat",
                importance=0.3,
            )
        except Exception as e:
            logger.error(f"[REEVU] Failed to save conversation memory: {e}")

    async def initialize_user_context(self, user_ref: SimpleNamespace) -> None:
        """Initialize or retrieve user context and update interaction stats."""
        await self.reevu_service.get_or_create_user_context(user_ref)
        await self.reevu_service.update_interaction_stats(user_ref.id)
