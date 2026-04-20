"""Canonical REEVU cognitive facade over legacy veena cognitive services.

This keeps the active runtime on REEVU-named imports while preserving
backward-compatible aliases tied to persisted schemas and historical routes.
"""

from app.modules.ai.services.veena_cognitive_service import (
    ReasoningEngine,
    VeenaCognitiveService,
)


ReevuReasoningEngine = ReasoningEngine
ReevuCognitiveService = VeenaCognitiveService

# Legacy compatibility aliases retained during migration.
ReasoningEngine = ReevuReasoningEngine
VeenaCognitiveService = ReevuCognitiveService

__all__ = [
    "ReevuReasoningEngine",
    "ReevuCognitiveService",
    "ReasoningEngine",
    "VeenaCognitiveService",
]