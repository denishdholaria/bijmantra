"""
Integration Adapter Base Class

All external integrations implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime, timezone


class IntegrationStatus(str, Enum):
    """Status of an integration connection."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"
    RATE_LIMITED = "rate_limited"


@dataclass
class IntegrationConfig:
    """Configuration for an integration."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: int = 30
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    records_synced: int = 0
    records_failed: int = 0
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class IntegrationAdapter(ABC):
    """
    Base class for all external integrations.
    
    Implementations must provide:
    - id: Unique identifier
    - name: Human-readable name
    - description: What this integration provides
    - required_config: List of required configuration keys
    - test_connection(): Verify the integration works
    - get_status(): Get current status
    
    Optional:
    - optional_config: List of optional configuration keys
    - sync(): Sync data with external service
    """

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self._last_error: Optional[str] = None
        self._last_sync: Optional[datetime] = None

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this integration."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this integration provides."""
        pass

    @property
    @abstractmethod
    def required_config(self) -> List[str]:
        """List of required configuration keys."""
        pass

    @property
    def optional_config(self) -> List[str]:
        """List of optional configuration keys."""
        return []

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if the integration is properly configured and reachable.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_status(self) -> IntegrationStatus:
        """
        Get current integration status.
        
        Returns:
            Current status enum value
        """
        pass

    async def sync(self, direction: str = "pull") -> SyncResult:
        """
        Sync data with external service.
        
        Args:
            direction: "pull" to fetch from external, "push" to send to external
        
        Returns:
            SyncResult with details of the operation
        
        Raises:
            NotImplementedError if sync is not supported
        """
        raise NotImplementedError("This integration does not support sync")

    def is_configured(self) -> bool:
        """Check if all required configuration is present."""
        for key in self.required_config:
            if not getattr(self.config, key, None) and key not in self.config.extra:
                return False
        return True

    def get_last_error(self) -> Optional[str]:
        """Get the last error message, if any."""
        return self._last_error

    def get_last_sync(self) -> Optional[datetime]:
        """Get timestamp of last successful sync."""
        return self._last_sync

    def to_dict(self) -> Dict[str, Any]:
        """Serialize adapter info to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required_config": self.required_config,
            "optional_config": self.optional_config,
            "is_configured": self.is_configured(),
            "last_error": self._last_error,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
        }
