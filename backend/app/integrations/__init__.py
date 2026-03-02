"""
Parashakti Framework - Integration Hub

External service adapters for connecting to third-party systems.
Each adapter implements a standard interface for consistent behavior.
"""

from .base import IntegrationAdapter, IntegrationConfig, IntegrationStatus
from .registry import INTEGRATION_REGISTRY, get_adapter


__all__ = [
    "IntegrationAdapter",
    "IntegrationStatus",
    "IntegrationConfig",
    "get_adapter",
    "INTEGRATION_REGISTRY",
]
