"""Knowledge Graph capability adapters."""

from typing import Any


__all__ = [
    "SqlAlchemyKnowledgeGraphAdapter",
    "SqlAlchemyKnowledgeGraphExplorerSnapshotAdapter",
    "SqlAlchemyKnowledgeGraphPersistence",
]


def __getattr__(name: str) -> Any:
    if name in {
        "SqlAlchemyKnowledgeGraphAdapter",
        "SqlAlchemyKnowledgeGraphExplorerSnapshotAdapter",
    }:
        from app.domains.intelligence.capabilities.knowledge_graph.adapters import (
            knowledge_graph,
        )

        value = getattr(knowledge_graph, name)
    elif name == "SqlAlchemyKnowledgeGraphPersistence":
        from app.domains.intelligence.capabilities.knowledge_graph.adapters import (
            knowledge_graph_persistence,
        )

        value = getattr(knowledge_graph_persistence, name)
    else:
        raise AttributeError(name)

    globals()[name] = value
    return value
