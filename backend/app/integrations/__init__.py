"""
Parashakti Framework - Integration Hub

External service adapters for connecting to third-party systems.
Each adapter implements a standard interface for consistent behavior.
"""

from .base import IntegrationAdapter, IntegrationStatus, IntegrationConfig
from .registry import get_adapter, INTEGRATION_REGISTRY

__all__ = [
    "IntegrationAdapter",
    "IntegrationStatus",
    "IntegrationConfig",
    "get_adapter",
    "INTEGRATION_REGISTRY",
]
