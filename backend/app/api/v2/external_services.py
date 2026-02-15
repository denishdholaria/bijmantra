"""
External Services Status API

Provides status information for external service integrations:
- AI providers (Google Gemini, Groq, Ollama, OpenAI, Anthropic)
- Weather services (OpenWeatherMap, Visual Crossing)
- Maps (Mapbox)
- Analytics (NASA POWER)

This endpoint allows the frontend to check which services are configured
and display appropriate notices to users.
"""

import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Optional
from enum import Enum

from app.services.ai.engine import get_llm_service, LLMProvider
from app.api.deps import get_current_user


router = APIRouter(prefix="/external-services", tags=["external-services"], dependencies=[Depends(get_current_user)])


# ============================================================================
# Schemas
# ============================================================================

class ServiceCategory(str, Enum):
    AI = "ai"
    WEATHER = "weather"
    MAPS = "maps"
    ANALYTICS = "analytics"
    STORAGE = "storage"


class ServiceStatus(BaseModel):
    """Status of a single external service"""
    id: str
    name: str
    category: ServiceCategory
    configured: bool
    available: bool
    free_tier: bool
    env_var: str
    config_path: str
    message: Optional[str] = None


class ExternalServicesStatusResponse(BaseModel):
    """Response containing status of all external services"""
    services: Dict[str, ServiceStatus]
    summary: Dict[str, int]  # Count by category


# ============================================================================
# Service Configuration
# ============================================================================

# Map of service IDs to their environment variables and metadata
SERVICE_CONFIG = {
    # AI Services
    "google_ai": {
        "name": "Google Gemini",
        "category": ServiceCategory.AI,
        "env_var": "GOOGLE_AI_KEY",
        "free_tier": True,
        "config_path": "/settings/ai",
    },
    "groq": {
        "name": "Groq",
        "category": ServiceCategory.AI,
        "env_var": "GROQ_API_KEY",
        "free_tier": True,
        "config_path": "/settings/ai",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "category": ServiceCategory.AI,
        "env_var": "OLLAMA_HOST",
        "free_tier": True,
        "config_path": "/settings/ai",
        "default_value": "http://localhost:11434",  # Has default
    },
    "openai": {
        "name": "OpenAI",
        "category": ServiceCategory.AI,
        "env_var": "OPENAI_API_KEY",
        "free_tier": False,
        "config_path": "/settings/ai",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "category": ServiceCategory.AI,
        "env_var": "ANTHROPIC_API_KEY",
        "free_tier": False,
        "config_path": "/settings/ai",
    },
    
    # Weather Services
    "openweathermap": {
        "name": "OpenWeatherMap",
        "category": ServiceCategory.WEATHER,
        "env_var": "OPENWEATHERMAP_API_KEY",
        "free_tier": True,
        "config_path": "/settings/integrations",
    },
    "visualcrossing": {
        "name": "Visual Crossing",
        "category": ServiceCategory.WEATHER,
        "env_var": "VISUALCROSSING_API_KEY",
        "free_tier": True,
        "config_path": "/settings/integrations",
    },
    
    # Maps
    "mapbox": {
        "name": "Mapbox",
        "category": ServiceCategory.MAPS,
        "env_var": "MAPBOX_ACCESS_TOKEN",
        "free_tier": True,
        "config_path": "/settings/integrations",
    },
    
    # Analytics
    "nasa_power": {
        "name": "NASA POWER",
        "category": ServiceCategory.ANALYTICS,
        "env_var": "NASA_POWER_API_KEY",
        "free_tier": True,
        "config_path": "/settings/integrations",
    },
}


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status", response_model=ExternalServicesStatusResponse)
async def get_external_services_status():
    """
    Get configuration status of all external services.
    
    Returns which services are configured (have API keys set)
    and which are available for use.
    
    This endpoint does NOT expose actual API keys - only whether they are set.
    """
    services: Dict[str, ServiceStatus] = {}
    summary: Dict[str, int] = {
        "ai": 0,
        "weather": 0,
        "maps": 0,
        "analytics": 0,
        "storage": 0,
    }
    
    # Check each service
    for service_id, config in SERVICE_CONFIG.items():
        env_var = config["env_var"]
        env_value = os.getenv(env_var)
        default_value = config.get("default_value")
        
        # Service is configured if env var is set OR has a default
        configured = bool(env_value) or bool(default_value)
        
        # For Ollama, check if server is actually reachable
        available = configured
        message = None
        
        if service_id == "ollama" and configured:
            # Ollama availability is checked separately via LLM service
            try:
                llm_service = get_llm_service()
                ollama_config = llm_service.providers.get(LLMProvider.OLLAMA)
                available = ollama_config.available if ollama_config else False
                if not available:
                    message = "Ollama server not reachable"
            except Exception:
                available = False
                message = "Could not check Ollama status"
        
        services[service_id] = ServiceStatus(
            id=service_id,
            name=config["name"],
            category=config["category"],
            configured=configured,
            available=available,
            free_tier=config["free_tier"],
            env_var=env_var,
            config_path=config["config_path"],
            message=message,
        )
        
        # Update summary count
        if configured:
            summary[config["category"].value] += 1
    
    return ExternalServicesStatusResponse(
        services=services,
        summary=summary,
    )


@router.get("/status/{service_id}", response_model=ServiceStatus)
async def get_service_status(service_id: str):
    """
    Get configuration status of a specific external service.
    
    Args:
        service_id: The service identifier (e.g., 'google_ai', 'openweathermap')
    
    Returns:
        Status of the requested service
    """
    if service_id not in SERVICE_CONFIG:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"Unknown service: {service_id}. Valid services: {list(SERVICE_CONFIG.keys())}"
        )
    
    config = SERVICE_CONFIG[service_id]
    env_var = config["env_var"]
    env_value = os.getenv(env_var)
    default_value = config.get("default_value")
    
    configured = bool(env_value) or bool(default_value)
    available = configured
    message = None
    
    # Special handling for Ollama
    if service_id == "ollama" and configured:
        try:
            llm_service = get_llm_service()
            ollama_config = llm_service.providers.get(LLMProvider.OLLAMA)
            available = ollama_config.available if ollama_config else False
            if not available:
                message = "Ollama server not reachable"
        except Exception:
            available = False
            message = "Could not check Ollama status"
    
    return ServiceStatus(
        id=service_id,
        name=config["name"],
        category=config["category"],
        configured=configured,
        available=available,
        free_tier=config["free_tier"],
        env_var=env_var,
        config_path=config["config_path"],
        message=message,
    )
