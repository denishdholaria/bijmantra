"""
Integration Registry

Central registry of all available integrations.
"""

from typing import Dict, Type, Optional
from .base import IntegrationAdapter, IntegrationConfig


# Registry of all integration adapters
INTEGRATION_REGISTRY: Dict[str, Type[IntegrationAdapter]] = {}


def register_adapter(adapter_class: Type[IntegrationAdapter]) -> Type[IntegrationAdapter]:
    """
    Decorator to register an integration adapter.
    
    Usage:
        @register_adapter
        class MyAdapter(IntegrationAdapter):
            id = "my_adapter"
            ...
    """
    # Get the id from a temporary instance or class attribute
    adapter_id = getattr(adapter_class, 'id', None)
    if adapter_id:
        INTEGRATION_REGISTRY[adapter_id] = adapter_class
    return adapter_class


def get_adapter(
    integration_id: str,
    config: Optional[Dict] = None
) -> Optional[IntegrationAdapter]:
    """
    Get an integration adapter instance.
    
    Args:
        integration_id: ID of the integration
        config: Configuration dictionary
    
    Returns:
        Configured adapter instance, or None if not found
    """
    adapter_class = INTEGRATION_REGISTRY.get(integration_id)
    if not adapter_class:
        return None
    
    integration_config = IntegrationConfig(**(config or {}))
    return adapter_class(integration_config)


def list_integrations() -> list:
    """List all registered integrations."""
    return [
        {
            "id": adapter_id,
            "name": getattr(cls, 'name', adapter_id),
            "description": getattr(cls, 'description', ''),
        }
        for adapter_id, cls in INTEGRATION_REGISTRY.items()
    ]
