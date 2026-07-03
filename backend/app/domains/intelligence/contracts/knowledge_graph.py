"""Backward-compatible Intelligence Knowledge Graph contracts.

New domain code should import schemas and ports from the
`app.domains.intelligence.capabilities.knowledge_graph` package. This module is
kept temporarily so older references fail softly while the architecture
transition drains.
"""

from app.domains.intelligence.capabilities.knowledge_graph.ports.knowledge_graph import *  # noqa: F401,F403
from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import *  # noqa: F401,F403


__all__ = [
    name
    for name in globals()
    if name.startswith("KnowledgeGraph") or name == "GraphAssetNotFound"
]
