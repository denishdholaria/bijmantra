"""Intelligence adapters for API, persistence, workers, and external systems."""

from typing import Any


__all__ = [
    "SqlAlchemyKnowledgeGraphAdapter",
    "SqlAlchemyKnowledgeGraphExplorerSnapshotAdapter",
    "SqlAlchemyKnowledgeGraphPersistence",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(name)

    from app.domains.intelligence.capabilities.knowledge_graph import adapters

    value = getattr(adapters, name)
    globals()[name] = value
    return value
