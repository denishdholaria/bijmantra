"""
Service Registry for Cross-Domain Communication

This module provides a centralized registry for domain services,
allowing cross-domain communication without direct imports.

This follows the architecture stabilization design (ADR-0001) which
requires domains to communicate through explicit interfaces rather
than direct imports.
"""

from typing import Any, Dict, Optional, Protocol
from sqlalchemy.ext.asyncio import AsyncSession


class SearchServiceProtocol(Protocol):
    """Protocol for search services across domains."""
    
    async def search(
        self,
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Search for entities in the domain."""
        ...
    
    async def get_by_id(
        self,
        db: AsyncSession,
        organization_id: int,
        entity_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Get entity by ID."""
        ...
    
    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Get statistics for the domain."""
        ...


class ServiceRegistry:
    """
    Central registry for domain services.
    
    This allows cross-domain communication without direct imports,
    maintaining domain boundaries while enabling integration.
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
    
    def register(self, name: str, service: Any) -> None:
        """Register a service in the registry."""
        self._services[name] = service
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service from the registry."""
        return self._services.get(name)
    
    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services


# Global service registry instance
_registry = ServiceRegistry()


def register_service(name: str, service: Any) -> None:
    """Register a service in the global registry."""
    _registry.register(name, service)


def get_service(name: str) -> Optional[Any]:
    """Get a service from the global registry."""
    return _registry.get(name)


def has_service(name: str) -> bool:
    """Check if a service is registered."""
    return _registry.has(name)


# Service name constants
class ServiceNames:
    """Constants for service names in the registry."""
    
    # Breeding domain
    CROSS_SEARCH = "breeding.cross_search"
    TRIAL_SEARCH = "breeding.trial_search"
    BREEDING_VALUE = "breeding.breeding_value"
    
    # Germplasm domain
    GERMPLASM_SEARCH = "germplasm.search"
    
    # Spatial domain
    LOCATION_SEARCH = "spatial.location_search"
    
    # Environment domain
    WEATHER = "environment.weather"
    GDD_CALCULATOR = "environment.gdd_calculator"
    
    # Genomics domain
    GWAS = "genomics.gwas"
    KINSHIP = "genomics.kinship"
