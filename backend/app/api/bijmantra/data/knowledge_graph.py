"""Compatibility shim for the Intelligence Knowledge Graph API adapter."""

from app.domains.intelligence.capabilities.knowledge_graph.adapters.api.knowledge_graph import (
    router,
)


__all__ = ["router"]
