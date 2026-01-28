"""
Integration Hub Service
Manage external API integrations and user API keys

Supported Integrations:
- NCBI (GenBank, BLAST, Entrez)
- Google Earth Engine
- OpenWeatherMap
- ERPNext
- Custom webhooks
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from enum import Enum
from dataclasses import dataclass
import hashlib
import json

from pydantic import BaseModel, Field
from cryptography.fernet import Fernet
import os


class IntegrationType(str, Enum):
    """Supported integration types"""
    NCBI = "ncbi"
    EARTH_ENGINE = "earth_engine"
    OPENWEATHER = "openweather"
    ERPNEXT = "erpnext"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class IntegrationStatus(str, Enum):
    """Integration connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    type: IntegrationType
    name: str
    description: str
    required_fields: List[str]
    optional_fields: List[str]
    docs_url: str
    icon: str


# Available integrations
INTEGRATIONS: Dict[IntegrationType, IntegrationConfig] = {
    IntegrationType.NCBI: IntegrationConfig(
        type=IntegrationType.NCBI,
        name="NCBI",
        description="National Center for Biotechnology Information - GenBank, BLAST, Entrez",
        required_fields=["api_key", "email"],
        optional_fields=["tool_name"],
        docs_url="https://www.ncbi.nlm.nih.gov/books/NBK25497/",
        icon="🧬"
    ),
    IntegrationType.EARTH_ENGINE: IntegrationConfig(
        type=IntegrationType.EARTH_ENGINE,
        name="Google Earth Engine",
        description="Satellite imagery and geospatial analysis",
        required_fields=["service_account_key"],
        optional_fields=["project_id"],
        docs_url="https://developers.google.com/earth-engine",
        icon="🌍"
    ),
    IntegrationType.OPENWEATHER: IntegrationConfig(
        type=IntegrationType.OPENWEATHER,
        name="OpenWeatherMap",
        description="Weather data and forecasts",
        required_fields=["api_key"],
        optional_fields=[],
        docs_url="https://openweathermap.org/api",
        icon="🌤️"
    ),
    IntegrationType.ERPNEXT: IntegrationConfig(
        type=IntegrationType.ERPNEXT,
        name="ERPNext",
        description="Enterprise resource planning integration",
        required_fields=["api_key", "api_secret", "base_url"],
        optional_fields=[],
        docs_url="https://frappeframework.com/docs",
        icon="📊"
    ),
    IntegrationType.WEBHOOK: IntegrationConfig(
        type=IntegrationType.WEBHOOK,
        name="Webhook",
        description="Custom webhook for external notifications",
        required_fields=["url"],
        optional_fields=["secret", "headers"],
        docs_url="",
        icon="🔗"
    ),
}


class UserIntegration(BaseModel):
    """User's integration configuration"""
    id: str
    user_id: str
    organization_id: str
    integration_type: IntegrationType
    name: str
    credentials: Dict[str, str]  # Encrypted
    status: IntegrationStatus
    last_used: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IntegrationHubService:
    """
    Service for managing external integrations
    
    Features:
    - Secure credential storage (encrypted)
    - Connection testing
    - Usage tracking
    - Rate limiting awareness
    """
    
    def __init__(self):
        # Get or generate encryption key
        key = os.getenv("INTEGRATION_ENCRYPTION_KEY")
        if not key:
            # Generate a key for development (in production, use env var)
            key = Fernet.generate_key().decode()
            print(f"[IntegrationHub] Generated encryption key (set INTEGRATION_ENCRYPTION_KEY in production)")
        
        self._cipher = Fernet(key.encode() if isinstance(key, str) else key)
        
        # In-memory storage (use database in production)
        self._integrations: Dict[str, UserIntegration] = {}
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self._cipher.encrypt(data.encode()).decode()
    
    def _decrypt(self, data: str) -> str:
        """Decrypt sensitive data"""
        return self._cipher.decrypt(data.encode()).decode()
    
    def _generate_id(self, user_id: str, integration_type: str) -> str:
        """Generate unique integration ID"""
        hash_input = f"{user_id}:{integration_type}:{datetime.now(UTC).isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def get_available_integrations(self) -> List[Dict[str, Any]]:
        """Get list of available integrations"""
        return [
            {
                "type": config.type.value,
                "name": config.name,
                "description": config.description,
                "required_fields": config.required_fields,
                "optional_fields": config.optional_fields,
                "docs_url": config.docs_url,
                "icon": config.icon
            }
            for config in INTEGRATIONS.values()
        ]
    
    def add_integration(
        self,
        user_id: str,
        organization_id: str,
        integration_type: IntegrationType,
        name: str,
        credentials: Dict[str, str]
    ) -> UserIntegration:
        """Add a new integration for a user"""
        
        # Validate integration type
        if integration_type not in INTEGRATIONS:
            raise ValueError(f"Unknown integration type: {integration_type}")
        
        config = INTEGRATIONS[integration_type]
        
        # Validate required fields
        for field in config.required_fields:
            if field not in credentials:
                raise ValueError(f"Missing required field: {field}")
        
        # Encrypt credentials
        encrypted_creds = {
            key: self._encrypt(value) 
            for key, value in credentials.items()
        }
        
        # Create integration
        integration_id = self._generate_id(user_id, integration_type.value)
        now = datetime.now(UTC)
        
        integration = UserIntegration(
            id=integration_id,
            user_id=user_id,
            organization_id=organization_id,
            integration_type=integration_type,
            name=name,
            credentials=encrypted_creds,
            status=IntegrationStatus.PENDING,
            created_at=now,
            updated_at=now
        )
        
        self._integrations[integration_id] = integration
        return integration
    
    def get_user_integrations(
        self, 
        user_id: str,
        organization_id: Optional[str] = None
    ) -> List[UserIntegration]:
        """Get all integrations for a user"""
        integrations = [
            i for i in self._integrations.values()
            if i.user_id == user_id
        ]
        
        if organization_id:
            integrations = [
                i for i in integrations
                if i.organization_id == organization_id
            ]
        
        return integrations
    
    def get_integration(self, integration_id: str) -> Optional[UserIntegration]:
        """Get a specific integration"""
        return self._integrations.get(integration_id)
    
    def get_decrypted_credentials(self, integration_id: str) -> Optional[Dict[str, str]]:
        """Get decrypted credentials for an integration"""
        integration = self._integrations.get(integration_id)
        if not integration:
            return None
        
        return {
            key: self._decrypt(value)
            for key, value in integration.credentials.items()
        }
    
    def update_integration(
        self,
        integration_id: str,
        name: Optional[str] = None,
        credentials: Optional[Dict[str, str]] = None,
        status: Optional[IntegrationStatus] = None
    ) -> Optional[UserIntegration]:
        """Update an integration"""
        integration = self._integrations.get(integration_id)
        if not integration:
            return None
        
        if name:
            integration.name = name
        
        if credentials:
            integration.credentials = {
                key: self._encrypt(value)
                for key, value in credentials.items()
            }
        
        if status:
            integration.status = status
        
        integration.updated_at = datetime.now(UTC)
        return integration
    
    def delete_integration(self, integration_id: str) -> bool:
        """Delete an integration"""
        if integration_id in self._integrations:
            del self._integrations[integration_id]
            return True
        return False
    
    async def test_connection(self, integration_id: str) -> Dict[str, Any]:
        """Test connection to an integration"""
        integration = self._integrations.get(integration_id)
        if not integration:
            return {"success": False, "error": "Integration not found"}
        
        credentials = self.get_decrypted_credentials(integration_id)
        
        try:
            if integration.integration_type == IntegrationType.NCBI:
                return await self._test_ncbi(credentials)
            elif integration.integration_type == IntegrationType.OPENWEATHER:
                return await self._test_openweather(credentials)
            elif integration.integration_type == IntegrationType.WEBHOOK:
                return await self._test_webhook(credentials)
            else:
                return {"success": True, "message": "Connection test not implemented"}
        except Exception as e:
            integration.status = IntegrationStatus.ERROR
            integration.last_error = str(e)
            return {"success": False, "error": str(e)}
    
    async def _test_ncbi(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test NCBI connection"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi",
                params={
                    "api_key": credentials.get("api_key"),
                    "email": credentials.get("email"),
                    "retmode": "json"
                }
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "NCBI connection successful"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
    
    async def _test_openweather(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test OpenWeatherMap connection"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": "London",
                    "appid": credentials.get("api_key")
                }
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "OpenWeatherMap connection successful"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
    
    async def _test_webhook(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test webhook connection"""
        import httpx
        
        url = credentials.get("url")
        if not url:
            return {"success": False, "error": "No URL configured"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.head(url, timeout=10)
                return {"success": True, "message": f"Webhook reachable (HTTP {response.status_code})"}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    def record_usage(self, integration_id: str):
        """Record that an integration was used"""
        integration = self._integrations.get(integration_id)
        if integration:
            integration.last_used = datetime.now(UTC)
            integration.status = IntegrationStatus.ACTIVE


# Global service instance
integration_hub = IntegrationHubService()
