"""Intelligence adapters for API, persistence, workers, and external systems."""

from app.domains.intelligence.capabilities.knowledge_graph.adapters import (
    LegacyKnowledgeGraphEvidencePackDataSource,
    LegacyKnowledgeGraphEvidenceSearchDataSource,
    LegacyKnowledgeGraphRetrievalDataSource,
    SqlAlchemyKnowledgeGraphAdapter,
    SqlAlchemyKnowledgeGraphExplorerSnapshotAdapter,
    SqlAlchemyKnowledgeGraphPersistence,
)


__all__ = [
    "LegacyKnowledgeGraphEvidencePackDataSource",
    "LegacyKnowledgeGraphEvidenceSearchDataSource",
    "LegacyKnowledgeGraphRetrievalDataSource",
    "SqlAlchemyKnowledgeGraphAdapter",
    "SqlAlchemyKnowledgeGraphExplorerSnapshotAdapter",
    "SqlAlchemyKnowledgeGraphPersistence",
]
