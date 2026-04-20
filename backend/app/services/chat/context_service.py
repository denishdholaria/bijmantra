"""
Context service for REEVU chat.

Handles RAG context retrieval, formatting, and task context assembly.
Extracted from backend/app/api/v2/chat.py.
"""

import json
import logging
from typing import Any

from app.modules.ai.services.memory import SearchResult
from app.schemas.reevu_chat_context import ReevuScopedChatContext

logger = logging.getLogger(__name__)


class ContextService:
    """Service for managing chat context and RAG retrieval."""

    @staticmethod
    def format_context_for_llm(documents: list[SearchResult]) -> str:
        """Format retrieved documents as context for the LLM."""
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

    @staticmethod
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
            context_parts.append("- visible_columns: " + ", ".join(task_context.visible_columns))
        if task_context.attached_context:
            context_parts.append("- attached_context:")
            for attachment in task_context.attached_context:
                label = f" ({attachment.label})" if attachment.label else ""
                context_parts.append(
                    f"  - {attachment.kind}:{attachment.entity_id}{label}"
                )

        if len(context_parts) == 1:
            return ""

        context_parts.append(
            "Use this scoped task context to interpret the request. Prefer it over broad application assumptions."
        )
        return "\n".join(context_parts)

    @staticmethod
    def merge_prompt_context(*parts: str) -> str:
        """Join non-empty prompt context fragments with spacing."""
        return "\n\n".join(part for part in parts if part)

    @staticmethod
    def extract_context_doc_ids(documents: list[SearchResult] | None) -> list[str]:
        """Extract document IDs from search results."""
        if not documents:
            return []
        return [doc.doc_id for doc in documents]
